# MSC3030: Jump to date API endpoint

Add an API that makes it easy to find the closest messages for a given
timestamp.

The goal of this change is to have clients be able to implement a jump to date
feature in order to see messages back at a given point in time. Pick a date from
a calender, heatmap, or paginate next/previous between days and view all of the
messages that were sent on that date.

Alongside the [roadmap of feature parity with
Gitter](https://github.com/vector-im/roadmap/issues/26), we're also interested
in using this for a new better static Matrix archive. Our idea is to server-side
render [Hydrogen](https://github.com/vector-im/hydrogen-web) and this new
endpoint would allow us to jump back on the fly without having to paginate and
keep track of everything in order to display the selected date.

Also useful for archiving and backup use cases. This new endpoint can be used to
slice the messages by day and persist to file.

Related issue: [*URL for an arbitrary day of history and navigation for next and
previous days*
(vector-im/element-web#7677)](https://github.com/vector-im/element-web/issues/7677)


## Problem

These types of use cases are not supported by the current Matrix API because it
has no way to fetch or filter older messages besides a manual brute force
pagination from the most recent event in the room. Paginating is time-consuming
and expensive to process every event as you go (not practical for clients).
Imagine wanting to get a message from 3 years ago 😫


## Proposal

Add new client API endpoint `GET
/_matrix/client/v1/rooms/{roomId}/timestamp_to_event?ts=<timestamp>&dir=[f|b]`
which fetches the closest `event_id` to the given timestamp `ts` query parameter
in the direction specified by the `dir` query parameter. The direction `dir`
query parameter accepts `f` for forward-in-time from the timestamp and `b` for
backward-in-time from the timestamp. This endpoint also returns
`origin_server_ts` to make it easy to do a quick comparison to see if the
`event_id` fetched is too far out of range to be useful for your use case.

When an event can't be found in the given direction, the endpoint throws a 404
`"errcode":"M_NOT_FOUND",` (example error message `"error":"Unable to find event
from 1672531200000 in direction f"`).

In order to solve the problem where a homeserver does not have all of the history in a
room and no suitably close event, we also add a server API endpoint `GET
/_matrix/federation/v1/timestamp_to_event/{roomId}?ts=<timestamp>?dir=[f|b]` which other
homeservers can use to ask about their closest `event_id` to the timestamp. This
endpoint also returns `origin_server_ts` to make it easy to do a quick comparison to see
if the remote `event_id` fetched is closer than the local one. After the local
homeserver receives a response from the federation endpoint, it probably should
try to backfill this event via the federation `/event/<event_id>` endpoint so that it's
available to query with `/context` from a client in order to get a pagination token.

The heuristics for deciding when to ask another homeserver for a closer event if
your homeserver doesn't have something close, are left up to the homeserver
implementation, although the heuristics will probably be based on whether the
closest event is a forward/backward extremity indicating it's next to a gap of
events which are potentially closer.

A good heuristic for which servers to try first is to sort by servers that have
been in the room the longest because they're most likely to have anything we ask
about.

These endpoints are authenticated and should be rate-limited like similar client
and federation endpoints to prevent resource exhaustion abuse.

```
GET /_matrix/client/v1/rooms/<roomID>/timestamp_to_event?ts=<timestamp>&dir=<direction>
{
    "event_id": ...
    "origin_server_ts": ...
}
```

Federation API endpoint:
```
GET /_matrix/federation/v1/timestamp_to_event/<roomID>?ts=<timestamp>&dir=<direction>
{
    "event_id": ...
    "origin_server_ts": ...
}
```

---

In order to paginate `/messages`, we need a pagination token which we can get
using `GET /_matrix/client/r0/rooms/{roomId}/context/{eventId}?limit=0` for the
`event_id` returned by `/timestamp_to_event`.

We can always iterate on `/timestamp_to_event` later and return a pagination
token directly in another MSC ⏩


## Potential issues

### Receiving a rogue random delayed event ID

Since `origin_server_ts` is not enforcably accurate, we can only hope that an event's
`origin_server_ts` is relevant enough to its `prev_events` and descendants.

If you ask for "the message with `origin_server_ts` closest to Jan 1st 2018" you
might actually get a rogue random delayed one that was backfilled from a
federated server, but the human can figure that out by trying again with a
slight variation on the date or something.

Since there isn't a good or fool-proof way to combat this, it's probably best to just go
with `origin_server_ts` and not let perfect be the enemy of good.


### Receiving an unrenderable event ID

Another issue is that clients could land on an event they can't/won't render,
such as a reaction, then they'll be forced to desperately seek around the
timeline until they find an event they can do something with.

Eg:
 - Client wants to jump to January 1st, 2022
 - Server says there's an event on January 2nd, 2022 that is close enough
 - Client finds out there's a ton of unrenderable events like memberships, poll responses, reactions, etc at that time
 - Client starts paginating forwards, finally finding an event on January 27th it can render
 - Client wasn't aware that the actual nearest neighbouring event was backwards on December 28th, 2021 because it didn't paginate in that direction
 - User is confused that they are a month past the target date when the message is *right there*.

Clients can be smarter here though. Clients can see when events were sent as
they paginate and if they see they're going more than a couple days out, they
can also try the other direction before going further and further away.

Clients can also just explain to the user what happened with a little toast: "We
were unable to find an event to display on January 1st, 2022. The closest event
after that date is on January 27th."


### Abusing the `/timestamp_to_event` API to get the `m.room.create` event

Although it's possible to jump to the start of the room and get the first event in the
room (`m.room.create`) with `/timestamp_to_event?dir=f&ts=0`, clients should still use
`GET /_matrix/client/v3/rooms/{roomId}/state/m.room.create/` to get the room creation
event.

In the future, with things like importing history via
[MSC2716](https://github.com/matrix-org/matrix-spec-proposals/pull/2716), the first
event you encounter with `/timestamp_to_event?dir=f&ts=0` could be an imported event before
the room was created.


## Alternatives

We chose the current `/timestamp_to_event` route because it sounded like the
easiest path forward to bring it to fruition and get some real-world experience.
And was on our mind during the [initial discussion](https://docs.google.com/document/d/1KCEmpnGr4J-I8EeaVQ8QJZKBDu53ViI7V62y5BzfXr0/edit#bookmark=id.qu9k9wje9pxm) because there was some prior art with a [WIP
implementation](https://github.com/matrix-org/synapse/pull/9445/commits/91b1b3606c9fb9eede0a6963bc42dfb70635449f)
from @erikjohnston. The alternatives haven't been thrown out for a particular
reason and we could still go down those routes depending on how people like the
current design.


### Paginate `/messages?around=<timestamp>` from timestamp

Add the `?around=<timestamp>` query parameter to the `GET
/_matrix/client/r0/rooms/{roomId}/messages` endpoint. This will start the
response at the message with `origin_server_ts` closest to the provided `around`
timestamp. The direction is determined by the existing `?dir` query parameter.

Use topological ordering, just as Element would use if you follow a permalink.

This alternative could be confusing to the end-user around how this plays with
the existing query parameters
`/messages?from={paginationToken}&to={paginationToken}` which also determine
what part of the timeline to query. Those parameters could be extended to accept
timestamps in addition to pagination tokens but then could get confusing again
when you start mixing timestamps and pagination tokens. The homeserver also has
to disambiguate what a pagination token looks like vs a unix timestamp. Since
pagination tokens don't follow a certain convention, some homeserver
implementations may already be using arbitrary number tokens already which would
be impossible to distinguish from  a timestamp.

A related alternative is to use `/messages` with a `from_time`/`to_time` (or
`from_ts`/`to_ts`) query parameters that only accept timestamps which solves the
confusion and disambigution problem of trying to re-use the existing `from`/`to`
query parameters. Re-using `/messages` would reduce the number of round-trips and
potentially client-side implementations for the use case where you want to fetch
a window of messages from a given time. But has the same round-trip problem if
you want to use the returned `event_id` with `/context` or another endpoint
instead.


### Filter by date in `RoomEventFilter`

Extend `RoomEventFilter` to be able to specify a timestamp or a date range. The
`RoomEventFilter` can be passed via the `?filter` query param on the `/messages`
endpoint.

This suffers from the same confusion to the end-user of how it plays with how
this plays with `/messages?from={paginationToken}&to={paginationToken}` which
also determines what part of the timeline to query.


### Return the closest event in any direction

We considered omitting the `dir` parameter (or allowing `dir=c`) to have the server
return the closest event to the timestamp, regardless of direction. However, this seems
to offer little benefit.

Firstly, for some usecases (such as archive viewing, where we want to show all the
messages that happened on a particular day), an explicit direction is important, so this
would have to be optional behaviour.

For a regular messaging client, "directionless" search also offers little benefit: it is
easy for the client to repeat the request in the other direction if the returned event
is "too far away", and in any case it needs to manage an iterative search to handle
unrenderable events, as discussed above.

Implementing a directionless search on the server carries a performance overhead, since
it must search both forwards and backwards on every request. In short, there is little
reason to expect that a single `dir=c` request would be any more efficient than a pair of
requests with `dir=b` and `dir=f`.

### New `destination_server_ts` field

Add a new field and index on messages called `destination_server_ts` which
indicates when the message was received from federation. This gives a more
"real" time for how someone would actually consume those messages.

The contract of the API is "show me messages my server received at time T"
rather than the messy confusion of showing a delayed message which happened to
originally be sent at time T.

We've decided against this approach because the backfill from federated servers
could be horribly late.

---

Related issue around `/sync` vs `/messages`,
https://github.com/matrix-org/synapse/issues/7164

> Sync returns things in the order they arrive at the server; backfill returns
> them in the order determined by the event graph.
>
> *-- @richvdh, https://github.com/matrix-org/synapse/issues/7164#issuecomment-605877176*

> The general idea is that, if you're following a room in real-time (ie,
> `/sync`), you probably want to see the messages as they arrive at your server,
> rather than skipping any that arrived late; whereas if you're looking at a
> historical section of timeline (ie, `/messages`), you want to see the best
> representation of the state of the room as others were seeing it at the time.
>
> *-- @richvdh , https://github.com/matrix-org/synapse/issues/7164#issuecomment-605953296*


## Security considerations

We're only going to expose messages according to the existing message history
setting in the room (`m.room.history_visibility`). No extra data is exposed,
just a new way to sort through it all.



## Unstable prefix

While this MSC is not considered stable, the endpoints are available at `/unstable/org.matrix.msc3030` instead of their `/v1` description from above.

```
GET /_matrix/client/unstable/org.matrix.msc3030/rooms/<roomID>/timestamp_to_event?ts=<timestamp>&dir=<direction>
{
    "event_id": ...
    "origin_server_ts": ...
}
```

```
GET /_matrix/federation/unstable/org.matrix.msc3030/timestamp_to_event/<roomID>?ts=<timestamp>&dir=<direction>
{
    "event_id": ...
    "origin_server_ts": ...
}
```

Servers will indicate support for the new endpoint via a non-empty value for feature flag
`org.matrix.msc3030` in `unstable_features` in the response to `GET
/_matrix/client/versions`.
