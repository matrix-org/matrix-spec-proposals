# MSC4390: Room Blocking API

Room blocking (takedowns, shutdowns, takeovers, preventative blocks, deletes, etc) are an ever
increasingly useful trust & safety utility for homeserver administrators, allowing them to prevent
participation in harmful rooms, and take steps to prevent further participation should it have
already been established. This is further enhanced by tools like [Draupnir] and [Meowlnir],
which both allow server administrators to automate takedowns of these bad rooms by subscribing
to policy lists which will enact room bans. The problem that this proposal aims to achieve
is similar to what [MSC4323: User suspension & locking endpoints][msc4323] did: there currently
exists no standardised API endpoints for these tools to perform these actions, effectively resulting
in vendor lockin, since they typically only support the Synapse Admin API. This proposal will
introduce a couple new endpoints that will allow programs to enact room bans and deletes without
having to have knowledge of the underlying server implementation.

> [!NOTE]
> This proposal is inspired by a subset of the much larger [MSC4375: Admin Room Management][msc4375],
> but aims to tighten the scope to allow for easier implementation.

[Draupnir]: https://github.com/the-draupnir-project/Draupnir
[Meowlnir]: https://github.com/maunium/meowlnir
[msc4323]: https://github.com/matrix-org/matrix-spec-proposals/pull/4323
[msc4375]: https://github.com/matrix-org/matrix-spec-proposals/pull/4375

## Proposal

> [!IMPORTANT]
> [RFC2119](https://www.rfc-editor.org/rfc/rfc2119) is used here on out.
>
> What defines a "server administrator" is left up to the implementation itself as most already have
> their own systems for defining administrators (e.g. Synapse has a database flag, Conduit has room
> membership) which rarely has a reason to be exposed outside of their respective management
> interfaces.
>
> All of the proposed endpoints are restricted to authenticated users, are not permitted
> guest access, and MUST NOT be rate-limited.

Complementing [section 10.22 (Server Administration)][p1] of the client-to-server specification,
four new endpoints are introduced:

1. `GET /_matrix/client/v1/admin/rooms/{roomID}` - Get room information, including block status
2. `PUT /_matrix/client/v1/admin/rooms/{roomID}/blocked` - Block or unblock a room
3. `DELETE /_matrix/client/v1/admin/rooms/{roomID}` - Start deleting a room
4. `GET /_matrix/client/v1/admin/rooms/{roomID}/status` - Get the progress of room deletion

[p1]: https://spec.matrix.org/v1.16/client-server-api/#server-administration

Servers SHOULD advertise to clients that the authenticated user is capable of using these admin
endpoints via capabilities, like so:

```json
{
    "capabilities": {
        "m.room_moderation": {
            "enabled": true
        }
    }
}
```

### Get room information

`GET /_matrix/client/v1/admin/rooms/{roomID}`

This endpoint returns some basic information regarding the provided room, if known.

**TODO**: Instead suggest implementations allow admin override for /state? Reinventing the wheel
a bit here.

#### Response

**200 OK**: The server successfully processed the request and could retrieve relevant details:

```jsonc
{
    // The room's full room ID. MUST always be present.
    "room_id": "!example",
    // Whether this room is blocked. MUST always be present
    "blocked": false,
    // The name of this room, if available.
    "name": "Example Room",
    // The entire contents of the m.topic state event.
    // The entire event body is provided as topics may have more than one textual representation form
    "topic": {"topic": "hello orld"},
    // The MXC URI for this room's avatar, if set
    "avatar": "mxc://foo.bar",
    // The canonical alias of this room, if set.
    "canonical_alias": "#foo:example.org",
    // Any alternative aliases in the canonical alias event.
    // This SHOULD also include aliases set by local users that aren't in the canonical alias event.
    "alt_aliases": ["#foo:example.com", "#foo:example.net"],
    // The total number of members that are joined to this room.
    "joined_members": 0,
    // The total number of members that have pending invites to this room.
    "invited_members": 0,
    // The number of local members that are joined to this room.
    "local_members": 0,
    // The number of local members that have pending invites to this room.
    "invited_local_members": 0,
    // The `m.room.create` event for this room. MUST always be present.
    "create_event": {
        "sender": "@example:example.org",
        "content": {
            "room_version": "12"
        }
        // Other client-formatted event fields here
    },
    // The `m.room.join_rules` event body for this room, if known.
    "join_rules": {"join_rule": "restricted", "allow": []},
    // The history visibility (world_readable/shared/invited/joined) for this room.
    "history_visibility": "shared",
    // The m.room.power_levels event body for this room
    "power_levels": {"users": {}},
    // The m.room.server_acl event body for this room
    "acl": {"allow": ["*"]}
}
```

> [!IMPORTANT]
> The **only** REQUIRED keys in this body are `room_id`, `blocked`, and `create_event`.
> The implementation MAY omit unknown values, values that resolve to empty arrays,
> values that resolve to false, values that resolve to zero, however event bodies that themselves
> are found but empty SHOULD NOT be omitted.

Note that in some cases here, entire event bodies are included in the response. `topic` returns
the entire body as [`m.room.topic` allows multiple different representations][m.room.topic] of a
room's topic. `m.room.join_rules` may have additional restrictions that the caller may be interested
in, `m.room.power_levels` may reveal who is an administrator of relevant rooms, and
`m.room.server_acl` may reveal allowlists/denylists applied to the room that are relevant.

[m.room.topic]: https://spec.matrix.org/v1.16/client-server-api/#mroomtopic

**403 `M_FORBIDDEN`**: The requesting user does not have permission to view room details via the
admin API.

**404 `M_NOT_FOUND`**: The provided room is not known to the server.

### Block or Unblock room

`PUT /_matrix/client/v1/admin/rooms/{roomID}/blocked`

This endpoint allows the caller to block or unblock a room.
If a room is being blocked, inbound *and* outbound federation with the blocked room MUST be
halted. Servers SHOULD return errors for events pertaining to blocked rooms in
[`PUT /_matrix/federation/v1/send/{txnId}`][txn] rather than just silently discarding them.

Further requests to create local events in blocked rooms SHOULD return `M_FORBIDDEN`.
`M_NOT_FOUND`, or even silently discarding with a 200 OK, MAY be returned if the implementation
wishes to hide from the relevant caller that the room is blocked.
On the contrary, the server MAY wish to permit server admins access to the room, in order to inspect
its history, state, etc.

> [!TIP]
> `m.room.member` events with `membership: leave` SHOULD be allowed locally and federated outwards
> when relevant to indicate to remote rooms that local users have left.
>
> Out of scope for this proposal, however server implementations may wish to go a step further
> and restrict the visibility of blocked rooms, for example, removing them from sync responses,
> denying access to history and event fetches, denying access to room state, etc.

Attempts to join or invite to blocked rooms SHOULD return `M_FORBIDDEN`, both over federation and over
client-to-server. `M_NOT_FOUND` MAY also be used instead, if the implementation wishes to hide from
the relevant callers that the room is blocked.

Rooms MUST be able to be unblocked at any time - being blocked should be considered a temporary
state. When unblocking a room, the server should stop serving error responses for events and
requests pertaining to the room, and should resume federation and permitting invites/joins.

#### Request

```jsonc
{
    // Whether this room is blocked or not.
    "blocked": true
}
```

#### Response

**200 OK**: The server successfully processed this request.

```jsonc
{
    // Whether this room is now blocked (in most cases will mirror the input value)
    "blocked": true
}
```

**403 `M_FORBIDDEN`**: The requesting user does not have permission to un/block rooms via the
admin API.

**404 `M_NOT_FOUND`**: The room requested is not known to the server.

### Delete Room

`DELETE /_matrix/client/v1/admin/rooms/{roomID}`

Allows the removal of a room from the server.
As a convenience, blocking the room may also be done as part of this request. Blocking + removing
can be somewhat equated to "taking down", i.e. removing and preventing re-joins.

This SHOULD perform at least some the following tasks when deleting a room:

1. All local users that can, should drop their power level (i.e. remove themselves from `users`)
  before being removed from the room.
2. Remove all local users from the room
3. If `block` is `true`, users should be forbidden from re-joining the room after removal
4. Remove all local aliases to the room
5. Local room data removed (i.e. all events, state snapshots, etc)

If the server receives subsequent requests to start deleting a room when it is already doing so,
it MUST perform no duplicate actions, instead only returning the room's ID.

> [!IMPORTANT]
> Servers **MUST NOT** permit further actions with the room while it is being deleted.
> It is suggested that the implementation marks the room as unavailable **before** taking further
> actions, thus allowing this endpoint to be idempotent. Obviously, if the client did not request
> a room block, the block should be removed once the deletion is complete.
>
> Servers **MUST** take responsibility for ensuring the request is fulfilled eventually.
> Situations like mid-operation restarts cannot be allowed to permanently destroy the task, it must
> resume at the next available opportunity. Only once the task has completed should the room become
> available again. This removes the responsibility for ensuring this from the client.

#### Request

```jsonc
{
    // If present and `true`, this room should be blocked before it is deleted.
    // If false/omitted, users may be able to re-join after the removal is completed.
    "block": false
}
```

#### Response

**200 OK**: This room was successfully removed:

```jsonc
{
    // The ID of the room that was deleted. Must not be omitted.
    "room_id": "!example"
}
```

**403 `M_FORBIDDEN`**: The requesting user does not have permission to un/block rooms via the
admin API.

**404 `M_NOT_FOUND`**: The room in question was not found. If the client wanted to delete+block a
room by its hash, the client should instead send `PUT [...]/blocked`.

### Check room delete status

`GET /_matrix/client/v1/admin/rooms/{roomID}/delete/status`

This endpoint fetches the status or result of a room delete task.

#### Response

**200 OK**: There is an ongoing task, or the last one finished:

```jsonc
// All values are required even if empty
{
    // All users that are to be (or have been, if task is done) removed from the room.
    // Typically this will be all local participants in the room, including invited users.
    "users": ["@..."],
    // All aliases that are to be (or have been, if task is done) removed from the room.
    // Typically this will be all local aliases.
    "aliases": ["#..."],
    // A rough percentage of how far along this delete task is.
    // Must be between 0 and 100.
    "progress": 0,
    // A rough estimate of how much longer this delete task will take, in seconds.
    // If not known, should be set to zero.
    "eta": 0,
    // If this task is done, this is true, otherwise false.
    "done": false
}
```

## Potential issues

- The specification of what a server implementation should do once receiving a block/delete request
  is intentionally vague to permit application-specific behaviours under the hood. This may
  unintentionally work against the proposed endpoints, as clients might expect that the server
  performs a set of actions that it has actually silently chosen not to.

## Alternatives

Aside for the status quo, none known at the time of writing.

[MSC4375: Admin Room Management][msc4375] is intended to supersede this proposal once implemented,
so the APIs are fairly similar, except MSC4375 has a wider scope and will require more work.

## Security considerations

Looking at the OSWAP top ten (2021), the security issues regarding this proposal namely revolve
around insufficient authentication/validation leading to data loss (via deletes) and potentially
sensitive information leaks (via room information fetch).

The "room delete" endpoint may also potentially cause rooms to become administrator-less if the
server opts to puppet local users into revoking their power levels, which cannot be reversed.

## Unstable prefix

| Stable                | Unstable                                        |
| --------------------- | ----------------------------------------------- |
| `m.room_moderation`   | `uk.timedout.msc4390`                           |
| `/_matrix/client/v1/` | `/_matrix/client/unstable/uk.timedout.msc4390/` |

## Dependencies

This MSC has no dependencies itself, but becomes a dependency for MSC4375
