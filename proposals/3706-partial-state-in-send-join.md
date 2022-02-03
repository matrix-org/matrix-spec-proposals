# MSC3706: Extensions to `/_matrix/federation/v2/send_join/{roomId}/{eventId}` for partial state

## Background

It is well known that joining large rooms over federation can be very slow (see,
for example, [synapse#1211](https://github.com/matrix-org/synapse/issues/1211)).

Much of the reason for this is the large number of events which are returned by
the
[`/send_join`](https://spec.matrix.org/v1.2/server-server-api/#put_matrixfederationv2send_joinroomideventid)
API, and must be validated and stored.

[MSC2775](https://github.com/matrix-org/matrix-doc/pull/2775) makes a number of
suggestions for ways that this can be improved. This MSC focusses on a specific
aspect of those suggestions by proposing specific changes to the `/send_join`
API.

## Proposal

[`PUT
/_matrix/federation/v2/send_join/{roomId}/{eventId}/send_join`](https://spec.matrix.org/v1.2/server-server-api/#put_matrixfederationv2send_joinroomideventid)
is extended to support "partial state" in its responses. This involves the
following changes:

First, we add a query-parameter, `partial_state`. This can take the values
`true` or `false`; other values should be rejected with an HTTP 400 error.

Calling servers use this parameter to indicate support for partial state in
`send_join`. If it is not set to `true`, receiving servers continue to behave
as they do today.

Receiving servers are not obliged to implement partial state; they are also
free to support it for some rooms and not others.

The following changes are made to the response:

 * `partial_state`: a new boolean field is added. This should be set to `true`
   to indicate that partial state is being returned. It must otherwise be set
   to `false` or omitted.

 * `state`: if partial state is being returned, then a subset of the full room
   state, rather than the complete room state. In particular, the following
   state should be returned:

     * any state with event type other than `m.room.member`.
     * TODO: anything else?

 * `auth_chain`: The spec currently defines this as "The auth chain for the
   entire current room state". We instead rephrase this as:

   All events in the auth chain for the returned join event, as well as
   those in the auth chains for any events returned in `state`.

   (Note that in the case that full state is being returned, the two
   definitions are equivalent.)

 * `servers_in_room`: A new field of type `[string]`, listing the servers
   active in the room (ie, those with joined members) before the join.

   This is to be used by the joining server to send outgoing federation
   transactions while it synchronises the full state.


## Potential issues

TBD

## Alternatives

TBD

## Security considerations

No security issues are currently foreseen with this specific MSC, though the
larger topic of incremental synchronisation of state has several concerns;
these will be discussed in other MSCs such as MSC2775.

## Unstable prefix


## Dependencies

This MSC does not build on any existing unaccepted MSCs.
