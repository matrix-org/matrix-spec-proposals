# MSC4463: Backfilling Pinned Events

When a homeserver joins a room it lacks prior history for, any pinned events in its
history are often invisible to clients, as server implementations typically respond
to [requests for the event][CS_get_evt] with `M_NOT_FOUND` if it is not locally stored.

When conversation within the room refers to prior pinned events that a member does
not have access to, this increases friction and eliminates one of the primary use
cases of pinned events: to share important historical information with new members.

## Proposal

Once a homeserver has joined a room, if the room contains the [`m.room.pinned_events`][CS_pinned_evts]
state event, it SHOULD make an attempt to backfill or fetch all of the event IDs listed
within its `pinned` field. Additionally, if `m.room.pinned_events` is updated to contain
an event that the homeserver is not aware of, it SHOULD make an attempt to backfill or
fetch that event by its listed ID.

Compliant homeservers SHOULD use the [`/_matrix/federation/v1/event/{eventId}`][SS_get_evt] endpoint
to fetch a singular event from other homeservers in the room. Homeservers SHOULD use a
best-effort heuristic to determine which servers in the room might have the desired
event (such as the homeserver of the user who sent the `m.room.pinned_events` event).

## Potential issues

Fetching historic events without filling all of the history in between may result in
a sparse DAG with gaps that some homeserver implementations may have difficulty handling.

Determining an appropriate server to fetch events from is much more difficult than with
traditional backfill, as the pinned event could be very far in the past. The heuristic
for choosing candidate servers is left as an implementation decision.

## Alternatives

The content of pinned messages could be included directly within the room state, however
this would require costly state updates whenever pinned messages change (which in many
cases, long lived messages receive regular updates).

This implementation is eager and encourages homeservers to fetch the pinned events
as part of room join and whenever the list of pinned events changes. A lazy implementation
of this MSC was not considered because there is not a clear "pinned events" endpoint for
clients to use besides fetching room state.

Instead of returning `M_NOT_FOUND`, homeserver implementations could instead choose to
fetch events over federation [whenever a client requests them][CS_get_evt].

## Security considerations

Malicious rooms could insert large lists of pinned events in an attempt to deny service to
homeservers joining it by causing a large fan-out of federation requests. This is already
possible in many ways by producing events with long auth chains or rooms with excessive
state[^1]. Servers MUST validate received events as they would any other event, checking
auth chains and signatures to prevent malicious servers sending events.

[^1]: Rooms such as the Matrix Community space are prime examples of expensive, difficult-to
    join rooms, which the requirement to backfill even more events would likely worsen.

## Unstable prefix

N/A, this MSC does not introduce any new identifiers and only serves to provide a
recommendation to server implementations.

## Dependencies

None.

[CS_get_evt]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3roomsroomideventeventid
[CS_pinned_evts]: https://spec.matrix.org/v1.18/client-server-api/#mroompinned_events
[SS_get_evt]: https://spec.matrix.org/v1.18/server-server-api/#get_matrixfederationv1eventeventid
[SS_backfill]: https://spec.matrix.org/v1.18/server-server-api/#backfilling-and-retrieving-missing-events
