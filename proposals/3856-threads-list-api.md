# MSC3856: Threads List API

An endpoint specific to listing the threads in a room is proposed to solve two
client problems:

1. Clients wish to display threads ordered by the most recently active.
2. Clients wish to display a list of threads the user has participated in.

It is currently difficult for clients to sort threads by the most recently
responded to. Clients can use the [`/messages`](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3roomsroomidmessages)
API with a filter of `"related_by_rel_types": ["m.thread"]` (as defined in
[MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#fetch-all-threads-in-a-room))
to fetch the list of threads in a room. This returns the root thread events in
topological order of those events (either forwards or backwards depending on the
`dir` parameter).

Each event also includes bundled aggregation, which will include the latest
event in each thread.

In order to sort threads by the latest event in that thread clients must
paginate through all of the threads in the room, inspect the latest event from
the bundled aggregations and attempt to sort them. This can require many round
trips to the server and is wasteful for both the client and server.

Unfortunately even when a client has all the threads in a room is not able to accurately
sort the threads since the client lacks the proper topological ordering of events. (The
closest available information is the `age` or `origin_server_ts` of the events, but this
is not always correct.)

Additionally, it is currently not possible for a client to query for threads that
the user has participated in, as defined in
[MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#event-format):

> The user has participated if:
>
> * They created the current event.
> * They created an event with a m.thread relation targeting the current event.

Currently, clients add the requesting user's MXID to the `related_by_senders` filter
(as defined in
[MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#fetch-all-threads-in-a-room)),
e.g. `"related_by_senders":["@alice:example.com"]`, but this results in missing
threads where the user sent the root message and has not yet replied.

## Proposal

### Client-Server endpoint

A new endpoint is proposed to query for threads in a room. This endpoint requires
authentication and is subject to rate-limiting.

The endpoint returns events, which represent thread roots and includes
[bundled aggregations](https://spec.matrix.org/v1.3/client-server-api/#aggregations)
in the response (which includes the "latest event" of each thread, see
[MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#event-format)
for the format of bundled aggregations of threads).

The returned events are ordered by the latest event of each thread.

#### Request format

```
GET /_matrix/client/v1/rooms/{roomId}/threads
```

Query Parameters:

* **`include`**: `enum`

  Whether to include all thread roots in the room or only thread roots which the
  user has participated in, meaning that the user has created the root event of
  the thread or replied to the thread (they have created an event with a `m.thread`
  relation targeting the root event).

  One of `[all participated]`. Defaults to `all`.
* **`from`**: `string`

  The token to start returning events from. This token can be obtained from a
  `prev_batch` or `next_batch` token returned by the `/sync` endpoint, or from
  an `end` token returned by a previous request to this endpoint.

  If it is not provided, the homeserver shall return a list of thread roots starting
  from the most recent visible event in the room history for the requesting user.
* **`limit`**: Optional: a client-defined limit to the maximum
  number of threads to return per page. Must be an integer greater than zero.

  Server implementations should impose a maximum value to avoid resource
  exhaustion.
* **`to`**: `string`

  The token to stop returning events at. This token can be obtained from a
  `prev_batch` or `next_batch` token returned by the `/sync` endpoint, or from
  an `end` token returned by a previous request to this endpoint.

#### Response format

* **`chunk`**: [`[ClientEvent]`](https://spec.matrix.org/v1.3/client-server-api/#room-event-format) **Required**

  A list of room of events which are the root event of threads. Each event includes
  bundled aggregations. The order is chronological by the latest event in that thread.
* **`end`**: `string`

  A token corresponding to the end of `chunk`. This token can be passed back to
  this endpoint to request further events.

  If no further events are available (either because we have reached the start
  of the timeline, or because the user does not have permission to see any more
  events), this property is omitted from the response.
* **`start`**: `string` **Required**

  A token corresponding to the start of `chunk`. This will be the same as the
  value given in `from`.

If the sender of an event is ignored by the current user the results are modified
slightly. This has two situations:

1. If the ignored user sent the root thread event: the server should return the
   redacted form of the root event, but otherwise act as normal. This matches the
   information that a client would have if the threads list was aggregated locally
   (and generally matches the behavior if a thread root is unavailable, e.g. due
   to room history visibility).
2. If the ignored user sent the latest thread event: the server should treat the
   latest event as not existing and replace it with the latest event from a
   non-ignored user; with the caveat that the ordering of the threads is not
   re-arranged due to this replacement.

#### Example request:

```
GET /_matrix/client/v1/rooms/%21ol19s%3Ableecker.street/threads?
    limit=25&
    include=participated
```

#### Example response:

```json
{
  "chunk": [ClientEvent],
  "end": "...",
  "start": "..."
}
```

### MSC3440 Filtering

This MSC replaces the [event filters added in MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#fetch-all-threads-in-a-room)
(`related_by_rel_types` and `related_by_senders`) as the only known use-case is
more efficiently solved by this MSC.

## Potential issues

None forseen.

## Alternatives

Additional parameters could be added to the `/messages` API to control the ordering
of the returned results. This would likely not be compatible with all the other
options available on that endpoint.

Keeping this a separate API also gives the possibility of additional threads-specific
filtering in the future.

## Security considerations

As with other endpoints that accept a `limit`, homeservers should apply a hard
server-side maximum.

## Future extensions

It does not seem useful to be able to paginate in reverse order, i.e. starting with
the thread which was least recently updated. If there becomes a future need of this
a `dir` parameter could be added which takes an enum value of `[f b]` defaulting to
`b` to maintain backwards compatibility with this proposal.

## Unstable prefix

The client-server API will be: `/_matrix/client/unstable/org.matrix.msc3856/rooms/{roomId}/threads`

## Dependencies

N/A
