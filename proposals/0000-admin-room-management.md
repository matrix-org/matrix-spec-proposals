# MSC0000: Admin Room Management

*See also: [MSC4323: User suspension & locking endpoints][MSC4323]*

Every Matrix server supports rooms, big or small. What every server doesn't support, however, is the
ability to manage the rooms that their server is participating in. Synapse has
[the Synapse admin API][s1], Dendrite has [the Dendrite admin API][d1], Conduit and its derrivatives
have [the admin room][c1], and other lesser known servers either have their own site-specific
interfaces, or even none at all.

Such fragmentation in administration interfaces presents a great challenge to ecosystem developers
who wish to provider room management capabilities to their users. Clients and moderation tools
(which will be grouped together for this proposal) usually have to choose between supporting the
Synapse admin API as it is the most deployed homeserver, guessing which implementation is in use and
maintaining several implementation-specific calls, or just not supporting anything at all.
Translation layers, such as [conduwuit Admin API proxy][caap] (defunct) can be used to alleviate the
problem at hand, however they simply shift the burden to another project, and introduce another
moving part that has the potential to flake or fail. When it comes to moderation and administration,
flakes and failures are generally not an acceptable risk, unless there is no other option.

As [MSC4343][MSC4323] did, this proposal is introducing some new client-to-server API endpoints that
will allow the clients of priviliged users to have greater management capabilities over the
homeserver. It will define interfaces to allow the listing of rooms the server has stored, fetching
information regarding rooms, evacuating rooms (removing all local users), purging rooms, and
blocking (to prevent future joins).

The reader is also encouraged to consider the usage of proposals such as
[MSC4204: `m.takedown` moderation policy recommendation][MSC4204], which allows clients such as
[Draupnir][draupnir] and [Meowlnir][meowlnir] to issue room "takedowns", which typically results in
the client attempting to block + purge the room.

[MSC4323]: https://github.com/matrix-org/matrix-spec-proposals/pull/4323
[s1]: https://element-hq.github.io/synapse/latest/usage/administration/admin_api/index.html
[d1]: https://element-hq.github.io/dendrite/administration/adminapi
[c1]: https://continuwuity.org/admin_reference#admin-rooms-moderation
[caap]: https://github.com/nexy7574/conduwuit-admin-api-proxy
[MSC4204]: https://github.com/matrix-org/matrix-spec-proposals/pull/4204
[draupnir]: https://github.com/the-draupnir-project/Draupnir
[meowlnir]: https://github.com/maunium/meowlnir

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
eight new endpoints are introduced:

- `GET /_matrix/client/v1/admin/rooms` - List rooms known to the homeserver
- `GET /_matrix/client/v1/admin/rooms/{roomID}` - Get room information (e.g. name, members, topic)
- `POST /_matrix/client/v1/admin/rooms/{roomID}/evacuate` - Start removing all local users from a room
- `GET /_matrix/client/v1/admin/rooms/{roomID}/evacuate/status` - Get room evacuation status
- `PUT /_matrix/client/v1/admin/rooms/{roomID}/blocked` - Block or unblock a room
- `DELETE /_matrix/client/v1/admin/rooms/{roomID}` - Start purging a room
- `GET /_matrix/cleint/v1/admin/rooms/{roomID}/delete/status` - Check the progress of a purge task
- `POST /_matrix/client/v1/admin/rooms/{roomID}/takeover` - Take over a room

[p1]: https://spec.matrix.org/v1.16/client-server-api/#server-administration

### List rooms

**`GET /_matrix/client/v1/admin/rooms`**

This endpoint allows the caller to iterate over the rooms known to the homeserver, allowing them to
act upon the known room IDs (e.g. hash match, fetch information, purge, etc).

As homeservers might be aware of five or even six-digit room counts, this endpoint is restricted to
returning only room IDs, expecting the client to fetch room data in follow-up for the rooms it may
be interested in. In order to accomodate this same situation, the pagination for this endpoint MAY
have a higher than normal cap on the number of entries that can be returned.

#### Request Parameters

The endpoint has the following parameters:

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `from` | string | Required | The end of the previous chunk (if any) |
| `dir` | string (`f` or `b`) | Required | The direction to paginate (forward or backwards) |
| `order_by` | string (see below) | `name` | The field to order the returned room IDs by |
| `exclude_empty` | boolean | `false` | Exclude rooms with zero local members |
| `exclude_private` | boolean | `false` | Exclude rooms with a join rule other than `public` |
| `exclude_public` | boolean | `false` | Exclude rooms with a join rule of `public` |
| `exclude_encrypted` | boolean | `false` | Exclude encrypted rooms |
| `exclude_unencrypted` | boolean | `false` | Exclude unencrypted rooms |
| `exclude_federated` | boolean | `false` | Exclude rooms where `m.federate` is missing or `true` |
| `exclude_unfederated` | boolean | `false` | Exclude rooms where `m.federate` is `false` |
| `only_origins` | [glob[]][spec-glob] | `["*"]` | Only include rooms where any of the provided globs match the `m.room.create` `sender` |

**Order by** can be any of the following:
- `name`: Sort by room name in [lexographical order](https://en.wikipedia.org/wiki/Lexicographic_order).
  Rooms with no `m.room.name` event are considered to have an empty string for a room name.
- `local_members`: Sort by local member count in descending order (largest -> smallest).
- `total_members`: Sort by total member count in descending order (largest -> smallest).
- `created_at`: Sort by the room creation timestamp (newest -> oldest).
- `room_version`: Sort by the room version (oldest -> newest). Unstable room versions are treated as
  "newest", and sorted lexographically.
- `latest_event`: Sort by the timestamp of the latest received event (oldest -> newest). Events that
  soft-failed SHOULD be considered in the sorting.

Servers MUST NOT allow `limit`s greater than 500, and MUST wrap the provided `limit` to the cap
if it exceeds it.

`order_by` MUST be case insensitive and servers MUST ignore any unknown values.

#### Response

**200 OK**: The sever successfully processed the request.

```jsonc
{
  "end": "...",  // a pagination token represending the end of the chunk, if any.
  "chunk": ["!room1", "!room2", "..."],  // an array of room IDs the server knows about
}
```

Clients MUST stop paginating once they encounter a response with an empty or missing `end`, as this
indicates there are no more rooms.

**400 `M_INVALID_PARAM`**: The request is not well formed (e.g. mismatched type).

**403 `M_FORBIDDEN`**: The user does not have permission to list homeserver rooms.

### Get room information

**`GET /_matrix/client/v1/admin/rooms/{roomID}`**

In order to provide clients with a general overview of a room without joining, even if it is
a non-public room, a limited subset of the room state is provided to clients. This allows them to
fetch vital information, such as who created the room, the name/avatar/topic of the room, its join
rules, guest access, canonical alias(es), and history visibility. This information can be used
(for example) to render the room to a user, and potentially to determine an abuse risk value.

The `m.room.create` event **MUST** be returned.

The following state events SHOULD be returned, if present:

- `m.room.name`
- `m.room.avatar`
- `m.room.join_rules`
- `m.room.power_levels`
- `m.room.guest_access`
- `m.room.history_visibility`
- `m.room.canonical_alias`
- `m.room.topic`

The following state events MAY be returned, if present:

- `m.room.server_acl`
- `m.room.parent` (all keys)
- `m.room.pinned_events`

`m.room.member` events MUST NOT be present unless `include_members` is true.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

This endpoint has the following query parameters:

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `include_members` | boolean | `false` | Include **all** user IDs currently joined to the room |

#### Response

**200 OK**: The server successfully fetched the information requested.

State events should be fully formatted client events, not stripped.

```json
{
  "state": [
    {
      "type": "...",
      "sender": "...",
      "content": "...",
      "state_key": "..."
      // ...
    }
  ]
}
```

**400 `M_INVALID_PARAM`**: `include_members` was not a valid boolean, or the `roomID` was malformed.

**403 `M_FORIDDEN`**: The user does not have permission to fetch room information as they are not an
administrator.

**404 `M_NOT_FOUND`**: The room provided is not known to the server

### Start room evacuation

**`POST /_matrix/client/v1/admin/rooms/{roomID}/evacuate`**

This endpoint exposes a method to allow clients to "evacuate" rooms. Evacuating rooms is usually a
step taken before purging or blocking them, to ensure that local users are no longer participating
in a room as ghosts when further action is taken.

Evacuate also has the capability to replace a room with a new one, to inform users that they were
evacuated.

> [!IMPORTANT]
> This endpoint is expected to potentially take a long time to process, so an "asynchronous"
> approach is taken. Implementations SHOULD fork off the task into a background process, immediately
> returning to the client, however MAY block the request until the evacuation is complete.
>
> As specified below, clients may specify a preference for this behaviour.

Servers MUST NOT permit concurrent evacuations on the same room ID.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

#### Request Body

The request body for this endpoint is shaped like the following:

```jsonc
{
  // Don't abort the evacuation if removing a member fails or there is some other non-fatal error.
  "force": false,
  // If false, request that the server doesn't cast the task to the background, instead blocking
  // the request until the evacuation completes.
  // If true, request that the server casts the evacuation into a background task as soon as
  // possible.
  // If omitted, the server chooses what happens.
  "background": true,

  // Details for creating a replacement room that all evacuated members will be joined to.
  // If omitted, no new room is created.
  "replace_with": {
    // The user ID who will create this room. Defaults to the calling user if omitted.
    "creator": "@abuse:example.org",
    // The initial state for this new room. The same as /createRoom.
    "initial_state": [
      { // e.g.
        "type": "m.room.name",
        "state_key": "",
        "content": {
          "name": "Content Violation Notice"
        }
      }
    ]
  }
}
```

Clients SHOULD allow for a large timeout on requests to this endpoint, especially if they set
`"background": false`.

Servers MAY ignore the `background` preference, if specified.

#### Response

**200 OK**: The server processed the request successfully.

```jsonc
{
  // Boolean indicating if the evacuation is carrying on in the background.
  "background": true,
  // The number of members removed from the room, if any. Can be omitted when background processing.
  // Must be a non-negative integer if provided.
  "removed": 0
}
```

**400 `M_BAD_JSON`**: `force` or `background` were not booleans.

**400 `M_INVALID_PARAM`**: The request is not well formed (e.g. room ID is malformed).

**403 `M_FORBIDDEN`**: The requesting user does not have permission to evacuate rooms.

**429 `M_LIMIT_EXCEEDED`**: An evacuation for this room is already in progress, try again later.

Unlike other endpoints, `M_NOT_FOUND` MUST NOT be returned. Evacuating an unknown room should always
return `200 OK` with `background: false` and `removed: 0`.

### Get room evacuation status

**`GET /_matrix/client/v1/admin/rooms/{roomID}/evacuate/status`**

This endpoint allows a client to check on the status of a room evacuation task.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

#### Response

**200 OK**: The server is processing an evacuation and returned the following information:

```jsonc
{
  // Unix milliseconds indicating the time at which this evacuation started.
  "started_at": 123456789,
  // The total number of users that need to be evacuated
  "total": 0,
  // The number of users that have been evacuated so far (excluding failed)
  "evacuated": 0,
  // The number of users that could not be evacuated so far.
  "failed": 0
}
```

The server MAY omit keys whose value is zero.

**403 `M_FORBIDDEN`**: The requesting user does not have permission to evacuate rooms.

**404 `M_NOT_FOUND`**: There is no ongoing evacuation task for this room.

### Block or unblock a room

**`PUT /_matrix/client/v1/admin/rooms/{roomID}/blocked`**

This endpoint blocks or unblocks a room. Blocked rooms cannot be joined by future local members.
Servers SHOULD NOT require that the room has been evacuated before being blocked, as preventing
future joins may be more critical than ensuring that there are no ghosts, and evacuations may take
a long time.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

#### Request Body

The request body for this endpoint is shaped like the following:

```jsonc
{
  "blocked": true  // or false
}
```

#### Response

**200 OK**: The room was blocked or unblocked. An empty response (`{}`) is returned.

**400 `M_INVALID_PARAM`**: The request is not well formed (e.g. room ID is malformed).

**400 `M_BAD_JSON`**: The value of `blocked` is neither `true` nor `false`.

**403 `M_FORBIDDEN`**: The requesting user does not have permission to un/block rooms.


### Start room purge

**`DELETE /_matrix/client/v1/admin/rooms/{roomID}`**

This endpoint exposes a method to allow clients to "purge" rooms. "Purging" a room is left as an
implementation-specific, but generally involves deleting as much of the stored data associated with
the room as possible, such as stored events and memberships.

> [!IMPORTANT]
> This endpoint is expected to potentially take a long time to process, so an "asynchronous"
> approach is taken. Implementations SHOULD fork off the task into a background process, immediately
> returning to the client, however MAY block the request until the purge is complete.
>
> As specified below, clients may specify a preference for this behaviour.

Servers MUST NOT permit concurrent purges on the same room ID.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

#### Request Body

The request body for this endpoint is shaped like the following:

```jsonc
{
  // Ignore any local restrictions (such as requiring a room be evacuated) and any non-fatal errors
  "force": false,
  // If false, request that the server doesn't cast the task to the background, instead blocking
  // the request until the purge completes.
  // If true, request that the server casts the purge into a background task as soon as possible.
  // If omitted, the server chooses what happens.
  "background": true
}
```

Clients SHOULD allow for a large timeout on requests to this endpoint, especially if they set
`"background": false`.

Servers MAY ignore the `background` preference, if specified.

#### Response

**200 OK**: The server processed the request successfully.

```jsonc
{
  // Boolean indicating if the purge is carrying on in the background.
  "background": true
}
```

**400 `M_BAD_JSON`**: `force` or `background` were not booleans.

**400 `M_INVALID_PARAM`**: The request is not well formed (e.g. room ID is malformed).

**403 `M_FORBIDDEN`**: The requesting user does not have permission to purge rooms.

**429 `M_LIMIT_EXCEEDED`**: A purge for this room is already in progress, try again later.

Unlike other endpoints, `M_NOT_FOUND` MUST NOT be returned. Purging an unknown room should always
return `200 OK` with `background: false`.

### Get room purge status

**`GET /_matrix/client/v1/admin/rooms/{roomID}/delete/status`**

This endpoint allows a client to check on the status of a room purge task.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

#### Response

**200 OK**: The server is processing a purge and returned the following information:

```jsonc
{
  // Unix milliseconds indicating the time at which this purge started.
  "started_at": 123456789
}
```

The server MAY omit keys whose value is zero.

**400 `M_INVALID_PARAM`**: The request is not well formed (e.g. room ID is malformed).

**403 `M_FORBIDDEN`**: The requesting user does not have permission to evacuate rooms.

**404 `M_NOT_FOUND`**: There is no ongoing purge task for this room.

### Take over room

**`POST /_matrix/client/v1/admin/rooms/{roomID}/takeover`**

This endpoint allows the calling user to "take over" the room by puppeting a local user in the room
that is able to escalate the caller's power level. This typically means finding local users that can
send `m.room.power_level` state events, sorting for the one with the higest power level, and
sending a new power level event with the calling user at the same power level as the puppetted user.

If the calling user is not in the room, servers SHOULD take similar steps to puppet a local user
into producing an invite for the calling user. This ensures that the user is able to join and use
their new power level regardless of room access restrictions. This may also involve unbanning the
calling user, if they were previously banned.

#### Request Parameters

The request has the `roomID` path param which must be a fully qualified room ID (i.e. a string
starting with the `!` sigil).

#### Request Body

```jsonc
{
  // The user ID to give the new power level to. Defaults to the authenticated user.
  // MUST be local to the current homeserver.
  "user_id": "@admin:example.com"
}
```

#### Response

**200 OK**: The server successfully updated the power levels and optionally invited the caller.
An empty response (`{}`) is returned.

**400 `M_INVALID_PARAM`**: The request is not well formed (e.g. room ID is malformed).

**400 `M_FORBIDDEN`**: The server was unable to take over the room, usually due to a lack of
privileged local users.

**403 `M_FORBIDDEN`**: The requesting user does not have permission to evacuate rooms.

**404 `M_NOT_FOUND`**: The room is not known to the server

## Potential issues

TODO

## Alternatives

Aside from the status quo, none are known at this time.

## Security considerations

Rooms are the lifeblood of Matrix, so this proposal introduces some incredibly powerful endpoints.
Misuse of the powers granted can result in permenant data loss (namely in the event of local-only
rooms being purged) and potentially irreversible privilage escalation via takeovers.

This propsal assumes the server is secure and administrator rights are only granted to trustworthy
people. There is inherently no way to defend against such malicious usage that remains in-scope of
this proposal.

## Unstable prefix

| Stable | Unstable |
| `/_matrix/client/v1/` | `/_matrix/client/unstable/uk.timedout.msc0000/` |

Servers SHOULD advertise support for this functionality via `/_matrix/client/versions`,
OPTIONALLY only to authenticated users.
Servers MUST NOT advertise support UNLESS they support AT LEAST the following endpoints:

- `GET /_matrix/client/v1/admin/rooms`
- `GET /_matrix/client/v1/admin/rooms/{roomID}`
- `POST /_matrix/client/v1/admin/rooms/{roomID}/evacuate`
  - If `GET /_matrix/client/v1/admin/rooms/{roomID}/evacuate/status` is not supported, `background`
    must always be `false`.
- `PUT /_matrix/client/v1/admin/rooms/{roomID}/blocked`

## Dependencies

None
