# MSC2848: Globally unique event IDs

Currently the client-server API and server-server API disagree on the deprecation of the `GET /event/:eventId`
endpoint, which has lead to confusion and concern among the core team and wider community. The endpoint
currently implies that event IDs are globally unique, which although may be true, is not optimal
for storage mechanics of all homeservers.

Some homeservers, like Synapse, currently store events in a single table with a `UNIQUE` constraint
across the event ID column. Due to Synapse's position as a reference implementation while the spec
was still being finalized, event IDs can be assumed to be globally unique already - this MSC does not
intend to change this fact. Newer homeserver implementations are trying to use scaling mechanisms
where different processes/databases are responsible for individual rooms, which is harder to achieve
when there's an endpoint which doesn't suggest a room ID for routing.

Previously it was considered a simple clarification error in the spec for the deprecation disagreement
and that the server-server API was right in its position to have the endpoint not deprecated. This MSC
changes that position by considering other server implementations while not imposing performance,
storage, or stability restrictions on existing implementations.

This MSC is spun off following a conversation on [matrix-doc#2779](https://github.com/matrix-org/matrix-doc/issues/2779)
and the subsequent clarifications in [#matrix-spec:matrix.org](https://matrix.to/#/#matrix-spec:matrix.org).
For context, this is being opened as an MSC to help aid conversation of the problem space while also
attempting to propose a potential (neutral) way forward to represent the highly impassioned perspectives.

## Proposal

In short, this MSC introduces a new federation endpoint `GET /_matrix/federation/v1/room/:roomId/event/:eventId`
which replaces the existing [`GET /_matrix/federation/v1/event/:eventId`](https://matrix.org/docs/spec/server_server/r0.1.4#get-matrix-federation-v1-event-eventid)
endpoint. The response and request parameters are largely the same with the following addition:
If the event ID is not in the room, or the room is not known to the server, a 404 `M_NOT_FOUND`
error is returned.

The existing `GET /event/:eventId` endpoint is to be deprecated and discouraged from use.

Synapse, and other server implementations which already key events by ID, should be entirely fine with
this change as the only additional check would be if the room ID in the request matches the room ID on
the event. If there's a mismatch, 404.

The spec would also clarify that event IDs can be considered globally unique for the purposes of
their storage. This does imply that implementations generating event IDs (in v1 and v2 rooms) will
need to ensure they are careful about how they assign event IDs to room events. A suggestion could
be incorporating the room ID in the event ID, putting a worker identifier in the event ID, or using
a lock within the software stack to ensure the same event ID doesn't get assigned more than once.

In v3-v6 rooms, the event IDs are based off the reference hash which includes the room ID. This
implicitly makes them globally unique as the reference hash collisions are considered to be exactly
the same event.

It should be more than appropriate to incorporate the room ID into the endpoint as a request parameter
as the calling server will almost always know the room ID the event is supposed to belong to. For
example, after calling `/state_ids` or verifying auth events the server will know the room ID to
go looking for events within. This also brings the fetch event endpoint up to par with the remainder
of the federation API which already demands a room ID for all other requests involving room events.

[MSC2644](https://github.com/matrix-org/matrix-doc/pull/2644) is a proposal which wishes to reference
rooms by event ID and not by room ID, however. This MSC intentionally goes against this wish by
deprecating the very API it wishes to use (when coupled with [MSC2695](https://github.com/matrix-org/matrix-doc/pull/2695)).
It's not immediately clear to the author why matrix.to needs to use an event ID over a room ID
to reference a room - this section of the MSC will need completing as feedback is acquired.

For backwards compatibility, if the server returns a failing HTTP status code without a reasonable
error code (`M_NOT_FOUND`, `M_FORBIDDEN`, etc) on the newly proposed endpoint, the server should retry
the request with the deprecated endpoint.

## Potential issues

As mentioned, some limited use cases for using a bare event ID would not be possible under this MSC.
Per above, the justification and rationale for going against this desired feature is yet to be completed
pending feedback.

## Alternatives

[MSC2695](https://github.com/matrix-org/matrix-doc/pull/2695) is the alternative where the client-server
API endpoint gets de-deprecated in favour of supporting bare event IDs. Per above, the justification for
going against MSC2695 is yet to be completed pending feedback.

## Security considerations

All the existing security considerations are covered by importing the behaviour of the existing endpoints,
with the added restrictions for the added parameters.

## Unstable prefix

The federation API can be awkward to detect support for unstable features, however if a server wishes
to try anyways it can use `org.matrix.msc2848` as the unstable prefix. This makes the new endpoint
`GET /_matrix/federation/unstable/org.matrix.msc2848/room/:roomId/event/:eventId` during the pre-spec
era of this MSC.
