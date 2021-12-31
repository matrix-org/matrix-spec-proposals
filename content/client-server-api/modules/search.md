---
type: module
---

### Server Side Search

The search API allows clients to perform full text search across events
in all rooms that the user has been in, including those that they have
left. Only events that the user is allowed to see will be searched, e.g.
it won't include events in rooms that happened after you left.

#### Client behaviour

There is a single HTTP API for performing server-side search, documented
below.

{{% http-api spec="client-server" api="search" %}}

#### Search Categories

The search API allows clients to search in different categories of
items. Currently the only specified category is `room_events`.

##### `room_events`

This category covers all events that the user is allowed to see,
including events in rooms that they have left. The search is performed
on certain keys of certain event types.

The supported keys to search over are:

-   `content.body` in `m.room.message`
-   `content.name` in `m.room.name`
-   `content.topic` in `m.room.topic`

The search will *not* include rooms that are end to end encrypted.

The results include a `rank` key that can be used to sort the results by
relevancy. The higher the `rank` the more relevant the result is.

The value of `count` gives an approximation of the total number of
results. Homeservers may give an estimate rather than an exact value for
this field.

#### Ordering

The client can specify the ordering that the server returns results in.
The two allowed orderings are:

-   `rank`, which returns the most relevant results first.
-   `recent`, which returns the most recent results first.

The default ordering is `rank`.

#### Groups

The client can request that the results are returned along with grouping
information, e.g. grouped by `room_id`. In this case the response will
contain a group entry for each distinct value of `room_id`. Each group
entry contains at least a list of the `event_ids` that are in that
group, as well as potentially other metadata about the group.

The current required supported groupings are:

-   `room_id`
-   `sender`

#### Pagination

The server may return a `next_batch` key at various places in the
response. These are used to paginate the results. To fetch more results,
the client should send the *same* request to the server with a
`next_batch` query parameter set to that of the token.

The scope of the pagination is defined depending on where the
`next_batch` token was returned. For example, using a token inside a
group will return more results from within that group.

The currently supported locations for the `next_batch` token are:

-   `search_categories.<category>.next_batch`
-   `search_categories.<category>.groups.<group_key>.<group_id>.next_batch`

A server need not support pagination, even if there are more matching
results. In that case, they must not return a `next_batch` token in the
response.

#### Security considerations

The server must only return results that the user has permission to see.
