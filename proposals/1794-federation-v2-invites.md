# MSC 1794 - Federation v2 Invite API

This proposal adds a new `/invite` API to federation that supports different
room versions.

## Motivation

It is planned for future room versions to be able to change the format of events
in various ways. To support this, all servers must know the room version
whenever they need to parse an event.  Currently the `/invite` API does not
include the room version, so the target server would be unable to parse the event included in the payload.

## Proposal

Add a new version of the invite API under the prefix `/_matrix/federation/v2`,
which has a payload of:

```
PUT /_matrix/federation/v2/invite/<room_id>/<event_id>

{
    "room_version": <room_version>,
    "event": { ... },
    "invite_room_state": [ ... ]
}
```

The differences between this and `v1` are:

1. The payload in `v1` is the event, while in `v2` the event is instead placed
   under an `"event"` key. This is for consistency with other APIs, and to allow
   extra data to be added to the request payload separately from the event.
2. A required field called `"room_version"` is added that specifies the room
   version.
3. The `"invite_room_state"` is moved from the `unsigned` section of the event
   to a top level key. The key `invite_room_state` being in the `event.unsigned`
   was a hack due to point 1. above.


The response is identical to `v1`, except that:

1. If the receiving server does not support the given room version the
   appropriate incompatible-room-version error is returned, in the same way
   as e.g. for `/make_join` APIs.
2. The response payload is no longer in the format of `[200, { ... }]`, and is
   instead simply the `{ ... }` portion. This fixes a historical accident to
   bring the invite API into line with the rest of the federation API.


If a call to `v2` `/invite` results in an unrecognised request exception **AND**
the room version is `1` or `2` then the sending server should retry the request
with the `v1` API.


## Alternatives


### Reusing V1 API

One alternative is to add a `room_version` query string parameter to the `v1`
`/invite` API in a similar way as for the `/make_join` APIs. However, older
servers would ignore the query string parameter while processing an incoming
`/invite` request, resulting in the server attempting to parse the event in the
old `v1` format. This would likely result in either a `400` or `500` response,
which the sending server could interpret as the receiving server not supporting
the room version.

This method, however, is fragile and could easily mask legitimate `400` and
`500` errors that are not due to not supporting the room version.


### Using V1 API for V1 room versions

Instead of all servers attempting to use the new API and falling back if the API
is not found, servers could instead always use the current API for V1 and V2
rooms.

However, this would not allow us to deprecate the `v1` API.
