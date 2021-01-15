## Spaces Summary API

*This MSC depends on [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772).*

Spaces are rooms with `m.space` as the [room type](https://github.com/matrix-org/matrix-doc/pull/1840).
Spaces can include state events to specify parent/child relationships.
These relationships point to other rooms, which may themselves be spaces.
This means spaces can have subspaces and rooms. This creates a graph: a space directory.

This MSC defines a new endpoint which can be used to reveal information about the space directory.

Consider the graph:
```
    A
    ^
    |___
    |   |
    V   V
    B   R1
    ^
    |
    V
    R2

R1,R2 = rooms
A,B   = spaces
<-->  = parent/child relationship events
```
This MSC aims to create a way for clients to produce a tree view along the lines of:
```
Space A
   |
   |___ Room 1
   |
   Space B
     |
     |___ Room 2
```
Clients are able to do this currently by peeking into all of these rooms
(assuming they have permission to) but this is costly and slow.

### Client API

```
POST /_matrix/client/r0/rooms/{roomID}/spaces
{
    "max_rooms_per_space": 5,      // The maximum number of rooms/subspaces to return for a given space, if negative unbounded. default: -1.
    "auto_join_only": true,        // If true, only return m.space.child events with auto_join:true, default: false, which returns all events.
    "limit": 100,                  // The maximum number of rooms/subspaces to return, server can override this, default: 100.
    "batch": "opaque_string"       // A token to use if this is a subsequent HTTP hit, default: "".
}
```

which returns:

```
{
    "next_batch": "opaque string",
    "rooms": [
        {
            "aliases": [
                "#murrays:cheese.bar"
            ],
            "avatar_url": "mxc://bleeker.street/CHEDDARandBRIE",
            "guest_can_join": false,
            "name": "CHEESE",
            "num_joined_members": 37,
            "room_id": "!ol19s:bleecker.street",
            "topic": "Tasty tasty cheese",
            "world_readable": true,

            "num_refs": 42,
            "room_type": "m.space"
        },
        { ... }
    ],
    "events": [
        {
            "type": "m.space.child",
            "state_key": "!efgh:example.com",
            "content": {
                "via": ["example.com"],
                "present": true,
                "order": "abcd",
                "auto_join": true
            }
        },
        {
            "type": "m.space.parent",
            "state_key": "!space:example.com",
            "content": {
                "via": ["example.com"]
            }
        }
    ]
}
```

Justifications for the request API shape are as follows:
 - The HTTP path: Spaces are scoped to a specific room to act as an anchor point for
   navigating the directory. Alternatives are `/r0/spaces` with `room_id` inside the
   body, but this feels less idiomatic for room-scoped requests.
 - The HTTP method: there's a lot of data to provide to the server, and GET requests
   shouldn't have an HTTP body, hence opting for POST. The same request can produce
   different results over time so PUT isn't acceptable as an alternative.
 - `max_rooms_per_space`: UIs can only display a set number of rooms per space, so allowing
   clients to specify this limit is desirable. Subsequent rooms can be obtained by paginating.
   The graph has 2 distinct types of nodes, and some UIs may want to weight one type above
   the other. However, it's impossible to always know what type of node a given room ID falls
   under because the server may not be joined to that room (to determine the room type) or the
   caller may not have permission to see this information.
 - `limit`: The maximum number of events to return in `events`. It is desirable for clients
   and servers to be able to put a maximum cap on the amount of data returned to the client.
   **This limit may be exceeded if the root room has `> limit` rooms.**
 - `auto_join_only`: If `true`, only a subset of the graph is returned based on the presence
   of `auto_join: true` in the `content` field of `m.space.child`. Some clients may only
   care about the "main" or "default" rooms, which are rooms with this flag set. This does
   not affect parent state events: they are still returned. This does not modify the value
   of `num_refs`.
 - `batch`: Required for pagination. Could be a query parameter but it's easier if
   request data is in one place.

Justifications for the response API shape are as follows:
 - `rooms`: These are the nodes of the graph. The objects in the array are exactly the same as `PublicRoomsChunk` in the
   [specification](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-publicrooms)
   as the information displayed to users is the same. There are two _additional_ keys
   which are:
     * `num_refs` which is the total number of state events which point to or from this room (inbound/outbound edges).
        This includes all `m.space.child` events in the room, _in addition to_ `m.space.parent` events which point to
        this room as a parent.
     * `room_type` which is the room type, which is `m.space` for subspaces. It can be omitted if there is no room type
       in which case it should be interpreted as a normal room.
 - `events`: These are the edges of the graph. The objects in the array are complete (or stripped?) `m.space.parent`
   or `m.space.child` events.
 - `next_batch`: Its presence indicates that there are more results to return.

Server behaviour:
 - Extract the room ID from the request. Sanity check request data. Begin walking the graph
   starting with the room ID in the request in a queue of unvisited rooms according to the
   following rules:
    * If this room has already been processed, skip. NB: do not remember this between calls,
      as servers will need to visit the same room more than once to return additional events.
    * Mark this room as processed.
    * Is the caller currently joined to the room or is the room `world_readable`?
      If no, skip this room. If yes, continue.
    * If this room has not ever been in `rooms` (across multiple requests), extract the
      `PublicRoomsChunk` for this room.
    * Get all `m.space.child` and `m.space.parent` state events for the room. *In addition*, get
      all `m.space.child` and `m.space.parent` state events which *point to* (via `state_key`)
      this room. This requires servers to store reverse lookups. Add the total number of events
      to `PublicRoomsChunk` under `num_refs`. Add `PublicRoomsChunk` to `rooms`.
      Do NOT include state events which are missing the `content.via` field, as this indicates
      a redacted link. These events do not contribute to `num_refs` and should not be returned
      to the caller.
    * If this is the root room from the original request, insert all these events into `events` if
      they haven't been added before (across multiple requests).
    * Else add them to `events` honouring the `limit` and `max_rooms_per_space` values. If either
      are exceeded, stop adding events. If the event has already been added, do not add it again.
    * For each referenced room ID in the events being returned to the caller (both parent and child)
      add the room ID to the queue of unvisited rooms. Loop from the beginning.
  - This guarantees that all edges for the root node are given to the client. Not all edges of subspaces
    will be returned, nor will edges of all rooms be returned. This can be detected by clients in two ways:
      * Comparing `num_refs` with the *total number* of edges pointing to/from the room.
      * Comparing the number of `m.space.child` state events in the room with `max_rooms_per_space`, where
        `max_rooms_per_space` is 1 greater than the actual desired maximum value.
  - If not all events were returned due to reaching a `limit` or `max_rooms_per_space`, return a
    `next_batch` token. The server SHOULD NOT return duplicate events or rooms on subsequent
    requests: this can be achieved by remembering the event/room IDs returned to the caller between calls.
    This results in each request uncovering more nodes/edges until the entire tree has been explored.


Client behaviour:
 - Decide which room should be the root of the tree, then call this endpoint with the root room ID.
 - The data in `rooms` determines _what_ to show. The events in `events` determine _where_ to show it.
   Take all the data in `rooms` and key them by room ID.
 - Loop through the `events` and keep track of parent->child relationships by looking at the `state_key`
   which is the child room ID. Clients may want to treat child->parent relationships
   (`m.space.parent` events) the same way or differently. Treating them the
   same way will guarantee that the entire graph is exposed on the UI, but can cause issues because it
   can result in multiple roots (a child can refer to a new unknown parent). If a child->parent relationship
   exists but a corresponding parent->child relationship does not exist, this room is a "secret" room which
   should be indicated as such. If a parent->child relationship exists but a corresponding child->parent
   relationship does not exist, this room is a "user-curated collection" and should be indicated as such.
   Persist the mappings in a map: one child can have multiple parents and one parent can have multiple
   children.
 - Starting at the root room ID:
     * Compare the `num_refs` value in `rooms.$room_id` to the total number of events which reference this
       room in `events` (across all rooms). If they differ, a partial response has been returned for this
       space and additional results should be loaded when required. The API guarantees that *all* events for
       the root room ID will be returned, regardless of how many events there are (even if they exceed `limit`).
     * Lookup all children for this room ID. For each child:
        - If there is no corresponding room data for this room ID then this room is either a subspace or a room.
          The room is not world readable or the server does not have any information about this room. Clients
          MAY be able to join this room by issuing a `/join` request.
        - If the child is a room (not a space, check the `room_type` field), look up the room data from
          `rooms` and render it.
        - Else the child is a space, render the space as a heading (using the room name/topic) and
          restart the lookup using the new space room ID.


### Federation API


Servers may not be joined to all subspaces in the graph. If this happens, they will lack the room state to form a response.
Servers may get this information by peeking into the room, but this includes a live stream of events which is unecessary and
is a single request per room in the graph. It would be preferable if there was a federation endpoint which included this
information and nothing more. This is more performant and is a single request per _server_ (which may have many nodes
of the graph). Effectively, this federation API requests the view of the graph from the point of view of the destination
server.

```
POST /_matrix/federation/v1/spaces/{roomID}
{
    "exclude_rooms": ["!a:b", "!b:c"] // Optional. Do not return state events in these rooms, nor include these rooms in `rooms`.
    "max_rooms_per_space": 5,         // The maximum number of rooms/subspaces to return for a given space, if negative unbounded. default: -1.
    "limit": 100,                     // The maximum number of rooms/subspaces to return, server can override this, default: 100.
    "batch": "opaque_string"          // A token to use if this is a subsequent HTTP hit, default: "".
}
```

Justifications for the request API shape are the same as before with one exception:
 - The HTTP path: Per-room federation endpoints are not put under `/rooms` so this proposal doesn't either.
 - The `exclude_rooms` parameter: In order to stop redundant information being sent to the server, this field allows requesting
   servers the ability to suppress node/edge information on a per-room basis. If a room ID is present in this list,
   the server should not return node information under `rooms` nor should it return _any state events in this room_. NB: state
   events which _point to_ this room should still be included.

The response body remains unchanged from the client format. Servers are unable to verify the auth chain of the returned events
as they are typically not joined to the rooms returned. Servers MUST NOT persist these events in any potential room DAG that may
be created if the server were to join the room.

Sending server behaviour:
 - When walking the spaces graph, if the server is not joined to a given room, remember the `via` server names and the room ID.
 - Send a federated request to a server in `via` for the unknown room, marking rooms the server is already joined to
   in `exclude_rooms`.
 - Servers MAY eagerly request graph information and SHOULD cache the response for a configurable duration. This proposal recommends
   1 hour.

Receiving server behaviour:
 - Validate the request and check sender signatures.
 - Walk the graph in the same way as the CS API endpoint, remembering to exclude rooms in `exclude_rooms`. "Exclude" in this
   context merely means do not add the room or state events in that room to the response. The room itself MUST still be walked
   so servers can extract transitive rooms e.g `A -> B -> C` and the requesting server requests `room_id: A, exclude_rooms: [B]`
   must return `C`.
 - Servers are authorised to see node/edge information if they are either joined to the room or the room is `world_readable`.
   A well-behaved server will not send requests for rooms they are already joined to, so they should only be shown `world_readable`
   rooms.
