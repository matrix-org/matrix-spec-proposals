# MSC3523: Timeboxed/ranged relations endpoint

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines a new `/relations` endpoint
which clients can use to get information about reactions, replies, edits, etc made to an event, however
the endpoint assumes that all events can indefinitely receive changes. For some cases, namely
[polls](https://github.com/matrix-org/matrix-doc/pull/3381), the client will need to ignore responses
added to a poll after the poll closes.

This proposal introduces additional query parameters to the `/relations` endpoint to allow clients to
filter the relations down to a specific time period. Clients implementing polls can then use these
parameters to only find responses up until the poll was closed, preventing a case where the server
needs to handle all the rules for polls itself.

## Proposal

Two new query parameters are added to [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)'s
`/relations` endpoint:

* `?from_target=[number|event ID]` - **Optional.** The unix timestamp or event ID to start considering
  relations for the response, inclusive. If ommitted, the start point is unbounded.
* `?to_target=[number|event ID]` - **Optional.** The unix timestamp or event ID to stop considering
  relations for the response, inclusive. If omitted, the end point is unbounded.

*Note*: The slightly awkward naming is to avoid conflict/confusion with pagination.

A mix of timestamps and event IDs is permitted (ie: `from_target=1637701025885&to_target=$poll_end`).

Timestamps are anticipated to be used when the client isn't sure when an event happened, or if the
linearized DAG is not an accurate representation of the client's requirements. Event IDs are expected
to be used when the client wants to know what happened between two points, such as in the case of
backfilling a gappy/limited sync.

The server's handling of relations between event IDs is very similar to how it processes
[`/messages`](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3roomsroomidmessages).
The DAG is linearized and relations between the start and end point are considered.

The response is not changed by this proposal. Repeated calls using the pagination tokens will need
to specify the same `from_target` and `to_target` values in order to maintain accurate paging.

## Potential issues

For application-specific uses, such as polls, it's possible that clients end up using the wrong
combination of timestamps and event IDs. Clients are encouraged to be cautious of this risk, and
features which have a potential for concern should be explicit about what shape of the endpoint
should be called.

There's not currently a forseeable use case for a `from_target` or even using event IDs as bounding
points, however the proposal author believes that 2-4 MSCs for related functionality feels needlessly
complicated.

## Alternatives

Unclear - the client could try and use `/messages` to backfill *everything*, but that seems very
inefficient when trying to get aggregated information about relationships.

## Security considerations

Denial of service style attacks are possible, but mitigated with rate limiting and servers setting
sensible limits on the to/from range. For example, servers can retrieve all relations like it normally
would for the event referenced in the endpoint path then filter down from that set. Servers are
strongly discouraged from implementations which walk the DAG between the range points as the caller
might very well specify a start point of the room's create event and an end point of hundreds of years
into the future.

## Unstable prefix

While this MSC is not considered stable, the following transformations apply:

* `from_target` -> `org.matrix.msc3523.from_target`
* `to_target` -> `org.matrix.msc3523.to_target`
