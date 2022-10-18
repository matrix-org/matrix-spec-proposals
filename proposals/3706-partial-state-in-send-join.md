# MSC3706: Extensions to `/_matrix/federation/v2/send_join/{roomId}/{eventId}` for partial state

## Background

It is well known that joining large rooms over federation can be very slow (see,
for example, [synapse#1211](https://github.com/matrix-org/synapse/issues/1211)).

Much of the reason for this is the large number of events which are returned by
the [`/send_join`](https://spec.matrix.org/v1.2/server-server-api/#put_matrixfederationv2send_joinroomideventid)
API, and must be validated and stored.

[MSC3902](https://github.com/matrix-org/matrix-doc/pull/3902) gives an overview
of changes to the matrix protocol to improve this situation. This MSC focuses
on a specific aspect of those suggestions by proposing specific changes to the
`/send_join` API.

## Proposal

[`PUT /_matrix/federation/v2/send_join/{roomId}/{eventId}/send_join`](https://spec.matrix.org/v1.2/server-server-api/#put_matrixfederationv2send_joinroomideventid)
is extended to support "partial state" in its responses. This involves the
following changes.

### New query parameter

`partial_state` is added as a new query parameter. This can take the values
`true` or `false`; other values should be rejected with an HTTP 400 error with
matrix error code `M_INVALID_PARAM`.

Calling servers use this parameter to indicate support for partial state in
`send_join`. If it is not set to `true`, receiving servers continue to behave
as they do today.

### Changes to the response

Receiving servers are not obliged to implement partial state: they are also
free to support it for some rooms and not others.

The following changes are made to the response:

 * `partial_state`: a new boolean field is added. This should be set to `true`
   to indicate that partial state is being returned. It must otherwise be set
   to `false` or omitted.

 * `state`: if partial state is being returned, then state events with event
   type `m.room.member` are omitted from the response. All other room state is
   returned as normal. (See 'Alternatives' for discussion on why only
   `m.room.member` events are omitted.)
 
 * `auth_chain`: The spec currently defines this as "The auth chain for the
   entire current room state". We instead rephrase this as:

   > All events in the auth chain for the returned join event, as well as
   > those in the auth chains for any events returned in `state`.

   (Note that in the case that full state is being returned, the two
   definitions are equivalent.)

 * If the `partial_state` query parameter was set, we make a further
   optimisation to `auth_chain`:

   > Any events returned within `state` can be omitted from `auth_chain`.

   For example: the `m.room.create` event is part of the room state, so
   must be included in `state`. However, it also forms part of the auth chain
   for all of the returned events, so in the current spec, must *also* be
   included in `auth_chain`. However, this is redundant, so we should omit it
   for calling servers which opt into that via the `partial_state` query param.

 * `servers_in_room`: A new field of type `[string]`, listing the servers
   active in the room (ie, those with joined members) before the join.

   This is to be used by the joining server to send outgoing federation
   transactions while it synchronises the full state.

   This field is **required** if the `partial_state` response field is true; it
   is otherwise optional.

## Potential issues

None at present.

## Alternatives

 * In future, the list of event types to omit could be expanded. (Some rooms
   may have large numbers of other state events).
   
   Currently, `m.room.member` events are by far the biggest problem. For
   example, a `/send_join` request for Matrix HQ returns approximately 85000
   events in `state`, of which all but 44 are `m.room.member`. 

   In order to reduce the scope of the change, we have therefore decided to
   focus on `m.room.member` events for now. Future MSCs might provde a
   mechanism for omitting other event types.
 
## Security considerations

No security issues are currently foreseen with this specific MSC, though the
larger topic of incremental synchronisation of state has several concerns;
these will be discussed in other MSCs such as MSC3902.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`partial_state` | query parameter, response field | `org.matrix.msc3706.partial_state`
`servers_in_room` | response field | `org.matrix.msc3706.servers_in_room`


## Dependencies

This MSC does not build on any existing unaccepted MSCs.
