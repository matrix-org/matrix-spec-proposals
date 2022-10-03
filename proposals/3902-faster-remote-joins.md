# MSC3902: Faster remote room joins over federation (overview)

## Background

It is well known that joining large rooms over federation can be very slow (see,
for example, [synapse#1211](https://github.com/matrix-org/synapse/issues/1211)).

Much of the reason for this is the large number of events which are returned by
the [`/send_join`](https://spec.matrix.org/v1.4/server-server-api/#put_matrixfederationv2send_joinroomideventid)
API. (As of August 2022, a `/send_join` request for Matrix HQ returns 206479
events.) These events are necessary to correctly validate the state of the room
at the point of the join, but the list is expensive for the "resident" server to
generate, and even more so for the joining server to validate and store.

This proposal therefore sets out the changes needed so that most of the room
state can be popuated lazily, in the background, *after* the user has joined
the room.

This proposal supercedes [MSC2775](https://github.com/matrix-org/matrix-spec-proposals/pull/2775).

## Proposal

Firstly, we change `/send_join` to return, on request, a much reduced list of
room state. The details of the changes to the API are set out in
[MSC3706](https://github.com/matrix-org/matrix-spec-proposals/pull/3706), but
in summary: `m.room.member` events are omitted from the response.

This gives the joining server enough information to start handling some
interactions with the room. Conceptually, processing then splits into two
threads: one, a modified mechanism for handling incoming events and requests in
the "partial-state" room; and second, a background process which concurrently
"resynchronises" the room state.

### Handling requests and events in the partial-state room

A number of changes must be made to handle the "partial-state" scenario. (As of
this writing, these changes are limited to homeserver implementations, but the
list may be extended to include changes to client implementations before this
MSC is concluded.)

 * Processing incoming events received over federation:

   * Currently, the
     [spec](https://spec.matrix.org/v1.4/server-server-api/#checks-performed-on-receipt-of-a-pdu)
     requires that an incoming event "Passes authorization rules based on the
     state before the event, otherwise it is rejected". Since we do not know
     the (full) state before the event, we can no longer apply this
     check. Instead, we perform a state-resolution between the limited state
     that we do have, and the event's auth events; we then check that the
     incoming event passes the authorization rules based on that resolved
     state.

     This process means that we are largely trusting remote servers not to send
     invalid events (hence the need for a revalidation during the
     resynchronisation process); however it does mean that if we have a ban for
     a particular user, then their events will be rejected.

   * Additionally, no attempt is made to perform a "soft fail" check on incoming events.

 * Handling other federation requests: most federation requests require
   knowledge of the room state for authorisation (we should reject requests
   from servers which do not have users in the room). However, we can no longer
   correctly determine that
   state. [MSC3895](https://github.com/matrix-org/matrix-spec-proposals/pull/3895)
   specifies a new error code to indicate that we were unable to authorise a
   request.

 * Handling client-server requests: depending on the request in question, the
   server may or may not be able to accurately answer it. For example, a
   request for the topic of the room via
   [`/rooms/{roomId}/state/m.room.topic`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv3roomsroomidstateeventtypestatekey)
   can reliably be answered (since we assume we have all non-membership state
   in the room), whereas a request for the [list of joined
   members](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv3roomsroomidjoined_members) cannot be answered.

   In the current implementation, requests that require knowledge of
   `m.room.member` events for remote users will *block* until the
   resynchronisation completes.

   (Note that we can reliably answer requests that require knowledge only of
   the membership state for local users.)

 * [`/sync`](https://spec.matrix.org/v1.4/client-server-api/#get_matrixclientv3sync)
   requires specific changes:

   * If [lazy-loading](https://spec.matrix.org/v1.4/client-server-api/#lazy-loading-room-members)
     of memberships is enabled, then any "partial state" room is included in
     the response. Even when lazy-loading is enabled, the server is expected to
     "include membership events for the `sender` of events being returned in
     the response". Since we do not have the full state of the room, we may be
     missing membership events for some senders. We resolve this by checking
     the `auth_events` for affected events, which must include a reference to a
     membership event.
     
   * If lazy-loading is *not* enabled, partial-state rooms are omitted from the
     response (until the state synchronisation completes).

     (This is [pending implementation](https://github.com/matrix-org/synapse/issues/12989) in Synapse.)

 * Outgoing events: This is [pending
   implementation](https://github.com/matrix-org/synapse/issues/12997), but is
   likely to require some changes to ensure we do not get into a situation of
   being unable to safely answer a
   [`/get_missing_events`](https://spec.matrix.org/v1.4/server-server-api/#post_matrixfederationv1get_missing_eventsroomid)
   or
   [`/state_ids`](https://spec.matrix.org/v1.4/server-server-api/#get_matrixfederationv1state_idsroomid)
   request for an event we have generated.

 * [Device management](https://spec.matrix.org/v1.4/server-server-api/#device-management):
   homeserver implementations are expected to maintain a cache of the device
   list for all remote users that share a room with a local user, via
   `m.device_list_update` EDUs. To handle incomplete membership lists, we need to make the following changes:

    * Fixes to outgoing device list updates: we keep a record of any *local*
      device list changes that take place during the resynchronisation, and,
      once resync completes, we send them out to any homeservers that were in
      the room at any point since we started joining. ([Synapse
      implementation](https://github.com/matrix-org/synapse/pull/13934))

    * Fixes to incoming device list updates: normally we ignore device-list
      updates from users who we don't think we share a room with. To ensure we
      do not discard incoming device list updates, we keep a record of any
      *remote* device list updates we receive, and replay them once resync
      completes. ([Synapse
      implementation](https://github.com/matrix-org/synapse/pull/13913)

### Resynchronisation

Once a server receives a "partial state" response to `/send_join`, it must then
call [`/state/{room_id}`](https://spec.matrix.org/v1.4/server-server-api/#get_matrixfederationv1stateroomid),
setting `event_id` to the ID of the join event returned by `/send_join`, to
obtain a full snapshot of the state at that event. It can then update its database 
accordingly.

However, this process may take some time, and it is likely that other events
have arrived in the meantime. These new events will also have been stored with
"partial state", and will not have been subject to the full event authorisation
process. The server must therefore work forward through the event DAG,
recalculating the state at each event, and rechecking event authorisation,
until it has caught up with "real time" and new events are being created with
"full state".

