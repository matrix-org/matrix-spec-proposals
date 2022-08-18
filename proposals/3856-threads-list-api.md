# MSC3856: Threads List API

An endpoint specific to listing the threads in a room is proposed to solve two
issues:

1. Clients wish to display threads by the most recently active.
2. Clients wish to display a list of threads the user is interested in.

It is currently difficult for clients to sort threads by the most recently
responded to. Clients can use the [`/messages`](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3roomsroomidmessages) API with a filter of
`"related_by_rel_types": ["m.thread"]` to fetch the list of threads in a room. This
returns the root thread events in topological order of those events (either
forwards or backwards depending on the `dir` parameter).

Each event also includes bundled aggregation, which will include the latest
event in each thread.

In order to sort threads by the latest event in that thread clients must
paginate through all of the threads in the room, inspect the latest event from
the bundled aggregations and attempt to sort them. This can require many round
trips to the server and is wasteful for both the client and server.

Additionally, even with all of the threads a client is not able to accurately
sort the threads since they lack the proper topological ordering of events. (The
closest they can get is by using `age` or `origin_server_ts`, but this is not
correct.)

For the second problem, it is currently not possible for a client to query for
threads that the user has participated in (as defined in
[MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#event-format)).
A client could add the user's MXID to the filter, e.g. `"related_by_senders":["@alice:example.com"]`,
but this misses threads where the user sent the root message and has not yet replied.

## Proposal

### Client-Server endpoint

A new endpoint is proposed to query for threads in a room. This endpoint requires
authentication and is subject to rate-limiting. This endpoint includes
[bundled aggregations](https://spec.matrix.org/v1.3/client-server-api/#aggregations)
in the response.

The returned threads are ordered by the most recently updated thread.

#### Request format

```
GET /_matrix/client/v1/rooms/{roomId}/threads
```

Query Parameters:

* **`include`**: `enum`

  Whether to include all threads in the room or only threads which the user has
  participated in, meaning that the user has created the root event of the thread
  or have created an event with a `m.thread` relation targeting the root.

  One of `[all participated]`. Defaults to `all`.
* **`from`**: `string`

  The token to start returning events from. This token can be obtained from a
  `prev_batch` or `next_batch` token returned by the `/sync` endpoint, or from
  an `end` token returned by a previous request to this endpoint.

  If it is not provided, the homeserver shall return a list of threads from the
  last visible event in the room history for the requesting user.
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

XXX Define how ignored users are handled, which has two cases:

1. If the ignored user sent the root thread event.
2. If the ignored user sent the latest thread event.

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

This MSC deprecates the [event filters added in MSC3440](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3440-threading-via-relations.md#fetch-all-threads-in-a-room)
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

## Unstable prefix

The client-server API will be: `/_matrix/client/unstable/org.matrix.msc3856/rooms/{roomId}/threads`

## Dependencies

N/A
