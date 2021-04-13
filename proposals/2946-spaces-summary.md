## MSC2946: Spaces Summary

This MSC depends on [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772), which
describes why a Space is useful:

> Collecting rooms together into groups is useful for a number of purposes. Examples include:
>
> * Allowing users to discover different rooms related to a particular topic: for example "official matrix.org rooms".
> * Allowing administrators to manage permissions across a number of rooms: for example "a new employee has joined my company and needs access to all of our rooms".
> * Letting users classify their rooms: for example, separating "work" from "personal" rooms.
>
> We refer to such collections of rooms as "spaces".

MSC2946 attempts to solve how the user of a space discovers rooms in that space. This
is useful for quickly exposing a user to many aspects of an entire community, using the
examples above, joining the "official matrix.org rooms" space might suggest joining a few
rooms:

* A room to discuss deevelopment of the Matrix Spec.
* An announements room for news related to matrix.org.
* An off-topic room for members of the space.

Note that it is implied that joining a space forces a user to join any of these, but
having a discovery mechanism is useful.

## Proposal

A new client-server API (and corresponding server-server API) is added which allows
for querying for the rooms and spaces contained within a space. This allows a client
to display a hierarchy of rooms to a user in an efficient manner (i.e. without having
to walk the full state of the space).

### Client-server API

Walks the space tree, starting at the provided room ID ("the root room"),
and visiting other rooms/spaces found via `m.space.child`
events, recursing through those children into their children, etc.

Example request:

```jsonc
POST /_matrix/client/r0/rooms/{roomID}/spaces

{
    "max_rooms_per_space": 5,
    "suggested_only": true
}
```

or:

```text
GET /_matrix/client/r0/rooms/{roomID}/spaces?
    max_rooms_per_space=5&
    suggested_only=true
```

Example response:

```jsonc
{
    "rooms": [
        {
            "room_id": "!ol19s:bleecker.street",
            "avatar_url": "mxc://bleeker.street/CHEDDARandBRIE",
            "guest_can_join": false,
            "name": "CHEESE",
            "num_joined_members": 37,
            "topic": "Tasty tasty cheese",
            "world_readable": true,

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
                "suggested": true
            },
            "room_id": "!ol19s:bleecker.street",
            "sender": "@alice:bleecker.street"
        },
        { ... }
    ]
}
```

Request params:

* **`suggested_only`**: Optional. If `true`, return only child events and rooms where the
  `m.space.child` event has `suggested: true`. Defaults to
  `false`.  (For the POST request, must be a boolean. For GET, must be either
  `true` or `false`, case sensitive.)
* **`max_rooms_per_space`**: Optional: a client-defined limit to the maximum
  number of children to return per space. Doesn't apply to the root space (ie,
  the `room_id` in the request). The server also has its own internal limit
  (currently 50) (which *does* apply to the root room); attempts to exceed this
  limit are ignored. Must be a non-negative integer.

Response fields:

* **`rooms`**: for each room/space, starting with the root room, a
  summary of that room. The fields are the same as those returned by
  `/publicRooms` (see
  [spec](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-publicrooms)),
  with the addition of:
  * **`room_type`**: the value of the `m.type` field from the
    room's `m.room.create` event, if any.
* **`events`**: child events of the returned rooms. For each event, only the
  following fields are returned: `type`, `state_key`, `content`, `room_id`,
  `sender`.

We start by looking at the root room, and add it to `rooms`. We also add any
`child` events in the room to `events`. We then recurse into the targets of
the `child` events, adding the rooms to `rooms` and any child events to
`events`. We then move onto grandchildren, and carry on in this way until
either all discovered rooms have been inspected, or we hit the server-side
limit on the number of rooms (currently 50).

Other notes:

* No consideration is currently given to `parent` events.
* If the user doesn't have permission to view/peek the root room (including if
  that room does not exist), a 403 error is returned with `M_FORBIDDEN`. Any
  inaccessible children are simply omitted from the result (though the `child`
  events that point to them are still returned).
* There could be loops in the returned child events - clients should handle this
  gracefully.
* Similarly, note that a child room might also be a grandchild.
* `suggested_only` applies transitively. For example, if a space A has child
  space B which is *not* suggested, and space B has suggested child room C, and
  the client makes a summary request for A with `suggested_only=true`,
  neither B **nor** C will be returned.
* The current implementation doesn't honour `order` fields in child events.

### Server-server API

Much the same interface as the C-S API.

Example request:

```jsonc
POST /_matrix/federation/v1/spaces/{roomID}
{
    "exclude_rooms": ["!a:b", "!b:c"],
    "max_rooms_per_space": 5,
    "suggested_only": true
}
```

Response has the same shape as the C-S API.

Request params are the same as the C-S API, with the addition of:

* **`exclude_rooms`**: Optional. A list of room IDs that can be omitted
  from the response.

This is largely the same as the C-S API, but differences are:

* The calling server can specify a list of spaces/rooms to omit from the
  response (via `exclude_rooms`).
* `max_rooms_per_space` applies to the root room as well as any returned
  children.
* If the target server is not a member of any discovered children (so
  would have to send another request over federation to inspect them), no
  attempt is made to recurse into them - they are simply omitted from the
  response.
  * If the target server is not a member of the root room, an empty
    response is returned.
* Currently, no consideration is given to room membership: the spaces/rooms
  must be world-readable (ie, peekable) for them to appear in the results.
  XXX: this will have to change for private rooms.

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix

During development of this feature it will be available at an unstable endpoints.
The client-server API will be:

`/_matrix/client/unstable/org.matrix.msc2946/rooms/{roomID}/spaces`

And the server-server API will be:

`/_matrix/federation/unstable/org.matrix.msc2946/spaces/{roomID}`

Note that the unstable identifiers from [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) also apply:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`type` | property in `m.room.create` | `org.matrix.msc1772.type`
`m.space` | value of `type` in `m.room.create` | `org.matrix.msc1772.space`
`m.space.child` | event type | `org.matrix.msc1772.space.child`
`m.space.parent` | event type | `org.matrix.msc1772.space.parent`
