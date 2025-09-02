# MSC4282: Hint that a /rooms/{room_id}/messages request is interactive

The endpoint [/rooms/{room_id}/messages](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3roomsroomidmessages)
is used by clients to retrieve older events from a homeserver, when the direction is set to
backwards (a phenomenon also called "back-pagination" throughout this MSC). This can be useful in a
few contexts:

- after a gappy sync (i.e. that set the `limited` flag), so as to retrieve events included in the
  gap, that is, all the events not included in the last sync response, and that have been sent to the
  homeserver after the last time we've sync'd. This applies both to sync v2 and simplified sliding
  sync.
- as an out-of-sync mechanism to go through all the events in a room from the end to the start, so
  as to apply some mass operation on them, like indexing them for a search engine.

In fact, this mechanism is crucial in the context of [simplified sliding sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186).
This sync mechanism indeed generates thin server responses including a minimal set of events
(controlled by the `timeline_limit` request parameter), so as to provide better initial sync times
and ultimately more responsive clients. The client is then expected to use the
`/rooms/{room_id}/messages` endpoint to retrieve the previous events of a room.

As a result, clients should be able to expect this endpoint to be *fast*, when the user session is
interactive (i.e. a user is waiting for these events to be retrieved). While it's hard to define
*how* fast, it's expected that this endpoint would return in a matter of seconds, in the worst
cases. Otherwise, the user experience on the clients may be severely degraded.

However, some server implementations, including
[Synapse](https://github.com/element-hq/synapse/blob/5c84f258095535aaa2a4a04c850f439fd00735cc/synapse/handlers/pagination.py#L575-L584),
[Conduit](https://gitlab.com/famedly/conduit/-/blob/a7e6f60b41122761422df2b7bcc0c192416f9a28/src/api/client_server/message.rs#L201)
and
[Conduwuit](https://github.com/girlbossceo/conduwuit/blob/0f81c1e1ccdcb0c5c6d5a27e82f16eb37b1e61c8/src/api/client/message.rs#L94-L101),
may generate, under some implementation-specific conditions, federation requests to
[backfill](https://spec.matrix.org/v1.14/server-server-api/#backfilling-and-retrieving-missing-events)
the room timeline, and fetch more events from other servers. This slows down reception of the
response in the client, since it is now blocking on the server waiting for the federation responses
to come. Moreover, the time spent retrieving those responses is theoretically unbounded, so the
homeserver and the clients may have to wait forever for such requests to complete.

We need a more responsive way to fetch older events from the server, without having to wait for
federation responses to come back. This is the point of this MSC.

## Proposal

It is proposed that the `/rooms/{room_id}/messages` endpoint be modified to allow clients to
specify a new boolean query parameter `interactive`, which indicates that the client is interested
in getting the response *quickly*.

If the parameter is missing, then it's considered to be `false` by default. Thus, this is not a
semantics breaking change, in that the server behavior will remain the same if the query parameter
hasn't been set.

When the query parameter is set to `true`, then the server is expected to do a best-effort attempt
at providing a response *in a reasonably short time*. There are several cases to consider:

- if the homeserver has reached its known end of the room, and must backfill older events from
  federation, then it shall:
    - either block on the backfill request to complete, before returning the response to the
      client,
    - or race the completion of the backfill request with a timeout, and return an empty response
      if the backfill request didn't complete in time. In that case, clients are expected to retry
      the back-pagination request later.
- otherwise, the server shall immediately return events it had in its local state, and if needed it
  shall start a backfill request in the background (so the next request has chances to complete
  quickly, be it interactive or not).

### Why is it fine to ignore the hint in the first case?

Let's consider the case where the server is mandated to respect the hint in the first case. If the
server must backfill to fetch older events from federation, and if, in that case, it would
immediately return, then a client would get an empty response from the server. Such a client might
be tempted to ask for more events, i.e. send a similar request to the server… which will respond
immediately again. This would cause the client to busy-loop until the backfill request has
completed, wasting CPU and bandwidth on both the client and the server (and potentially leading to
battery exhaustion on mobile clients). That's why the server shall ignore the hint in this very
specific case, to avoid the busy-loop behavior.

## Potential issues

Before, it was possible that clients would miss events in a room, because they back-paginated
through it using `/messages`, and the server received new events after a netsplit, at a position that
the client had already paginated through. This would result in the client not receiving those
events, or receiving them through sync but in a non-topological ordering (i.e. an ordering that
would be different that the one they would've observed by paginating with `/messages`).

This MSC doesn't resolve this problem, and it may make it more apparent on the contrary, if *all*
`/messages` requests end up *not* causing any federation backfill. The most likely consequence of
this is that events might be more frequently misordered across clients.

## Alternatives

Instead of an additional query parameter, this MSC could mandate that this becomes the expected
behavior of all the implementations. This would be an implicit breaking change, and it may inhibit
use cases where clients might prefer a perfectly backfilled room over a quick response time.

Since this problem is more frequent with simplified sliding sync, one could imagine that a client
would find a simplified-sliding-sync specific solution. For instance, it could increase the
`timeline_limit` window to get more and more events from the end of the room, up to the previous
latest event they knew about, and thus *not* cause backfill requests. This is a workaround that
would work, but not be optimal in terms of bandwidth and server CPU activity, as it would mean
including lots of events the client has already seen before (viz., the increasing tail of the
room's timeline).

We could also have a new separate paginated endpoint to retrieve the previous events in the *sync*
ordering, thus not causing any backfill requests. It would be strictly more work to implement, and
it is unclear that it would achieve more than the current proposal.
