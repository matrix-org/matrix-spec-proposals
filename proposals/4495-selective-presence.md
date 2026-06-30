# MSC4495: Selective Presence

Presence is widely known to be one of the most expensive features in the Matrix specification. Even with continued
efforts to improve server implementations[^1][^2], large public deployments still disable outbound federated
presence, citing its substantial performance impact. Presence, as it stands, is fundamentally flawed: users receive
presence EDUs for every user they share a room with, even if the users have never interacted or have no interest in
each other's presence; server operators often have no choice but to disable presence altogether to limit the
excessive federation load; and users who do _not_ want to share potentially trackable information with public,
federated rooms \- a limitation [acknowledged by the current specification][presence-v1-privacy] \- the only option
they typically have is to, again, disable presence outright.

This proposal introduces "Selective Presence," a system for users to decide precisely _who_ their
presence is shared with. The benefits of this are twofold:
1. the overall load on homeservers implementing presence is reduced substantially, as users only share their
   presence with interested parties, and
2. users benefit from improved privacy by only sharing such sensitive information with those they want to have
   access to it.

## Prior Art

Prior to [MSC1819], a mechanism known as "presence lists" allowed users to subscribe to others' presence. In
theory, it also offered a mechanism for other users to request your presence. However, Synapse historically
[accepted all presence requests automatically][#4417], ultimately resulting in the feature's removal prior to r0.

[MSC4325: Presence privacy][MSC4325] attempts to solve this problem by reintroducing a concept similar to Selective
Presence. However, MSC4325 lacks some features integral to this proposal's goal of keeping UX similar to the
current approach; room hints, for example, allow rooms to recommend that clients prompt users about whether they
would like to share their presence, or forbid sharing presence altogether. This keeps presence usable for small
communities, private rooms, and DMs, while reducing the load from federating presence in large public rooms.

## Proposal

### User Presence Sharing Preferences

A new [`account_data`] entry, `m.presence.sharing`, is stored for modification by clients and use by homeservers.

This event contains four properties:
* The boolean `share_locally` enables sharing presence with all users with mutual rooms on the local homeserver
  (default `false`)
* Three **presence sharing map** objects, mapping one of several entity types to presence sharing behaviour:
  1. `users` mapping [User IDs][mxid-format] (default `{}`)
  2. `rooms` mapping [Room IDs][roomid-format] (default `{}`)
  3. `servers` mapping [Server Names][servername-format] (default `{}`)

While homeservers SHOULD follow these defaults, operators and implementations MAY override them where appropriate;
however, they MUST NOT overrule a user's wishes to deny presence sharing. For example, an operator may default
`share_locally` to `true` in an organisation environment.

No glob resolution is supported for any key in a presence sharing map.

The string values of these presence sharing maps may be any of the following:
* `"deny"`: Explicitly forbid sending presence to the entity  
  The `"deny"` state MUST NOT be specified for room IDs under the `"rooms"` object.
* `"allow"`: Permit sharing presence with the entity  
  The `"allow"` state MUST NOT be specified for entire homeservers under the `"servers"` object.

Servers MUST treat users without `m.presence.sharing` in their `account_data` as though the default values were
specified.

Sample `m.presence.sharing` account data event:
```json
{
    "share_locally": true,
    "users": {
        "@alice:example.com": "allow",
        "@mallory:example.com": "deny",
    },
    "rooms": { "!family-group-chat": "allow" },
    "servers": { "matrix.org": "deny" }
}
```

### Room Presence Sharing Hints

A new room state event is introduced, `m.room.presence_sharing`. This state event contains one field,
`presence_sharing`, which is a string with two possible values: `"suggest"` and `"forbid"`. If the event is not
present, the room is treated as though its value is `"forbid"` by default.

Servers MUST NOT include rooms with a `presence_sharing` value of `"forbid"` when they calculate a user's recipient
user set, even if the user `"allow"`s presence to be shared with the room.

The `m.room.presence_sharing` hint SHOULD be [transferred upon room upgrade][room-upgrades].

#### Presence Sharing Prompts

A new [`account_data`] entry, `m.presence.prompted`, is introduced to improve the user experience for clients with
presence sharing prompts. To allow users to dismiss a prompt on one client and have this register across all of
their clients, so that they do not have to answer the prompt several times, the following standard properties are
used:
* `users`: An array of [User IDs][mxid-format] (default `[]`)
* `rooms`: An array of [Room IDs][roomid-format] (default `[]`)

Sample `m.presence.prompted` account data event:
```json
{
    "users": [
        "@joey:example.com",
        "@chandler:example.com",
    ],
    "rooms": ["!apartment-group-chat"]
}
```

Clients implementing presence sharing prompts SHOULD show a prompt resembling "Would you like to share your
presence with this room?" for a relevant entity, which is the user in an `m.direct` room with **exactly one** other
joined user or the room itself otherwise, in the following circumstances:
* The room's `presence_sharing` is set to `"suggest"`
* The relevant entity is not in the user's corresponding `m.presence.prompted` array or `m.presence.sharing` map

Clients MAY wish to check room predecessor chains to avoid showing previously dismissed prompts in upgraded rooms.
They SHOULD carry settings over when starting and following a room upgrade. They MUST NOT prompt the user to share
presence in a room with a `presence_sharing` value of `"forbid"`.

#### Room Defaults

[`POST /_matrix/client/v3/create_room`][cs-createroom] SHOULD use the `preset` parameter to set the
`m.room.presence_sharing` state event in created rooms to the following template values:

| room creation `preset` | `m.room.presence_sharing`           |
| ---------------------- | ----------------------------------- |
| `private_chat`         | `{ "presence_sharing": "suggest" }` |
| `trusted_private_chat` | `{ "presence_sharing": "suggest" }` |
| `public_chat`          | `{ "presence_sharing": "forbid" }`  |

### Modifications to the [`m.presence` EDU]

The federation [User Presence Update] type is modified to include:
* An optional map, `recipients`, containing two arrays of [User IDs][mxid-format] belonging to the destination
  server, `add` and `delete`.
* A pair of integer identifiers, `stream_id` and `prev_id`, which are unique per `user_id`. These values do not need to
  be sequential or in any particular order, only unique.

The `add` and `delete` arrays of `recipients` represent an incremental update to a user's recipient user set,
adding and removing users respectively. A server MUST NOT send updates lacking a populated `add` to a destination
homeserver after their last user is updated out of the recipient set.

`stream_id` and `prev_id` form a sequence representing the state of the user's recipient user set, similar to the
behaviour of the [Device List Update] type. `recipients` may only be present if `prev_id` is present. If a user's
`stream_id` is replaced but no changes are relevant to the receiving homeserver, the sending server uses empty `add`
and `delete` lists.

`m.presence` EDU (as received by `example.com`):
```json
{
    "content": {
        "push": [
            {
                "currently_active": true,
                "last_active_ago": 5000,
                "presence": "online",
                "status_msg": "Making cupcakes",
                "user_id": "@john:matrix.org",
                "recipients": {
                    "add": ["@alice:example.com"],
                    "delete": ["@geoff:example.com"],
                },
                "stream_id": 1,
                "prev_id": 0,
            }
        ]
    },
    "edu_type": "m.presence"
}
```

#### Dispatch Algorithm

The **recipient user set** of a user's presence transition is determined as follows:
1. Include all members of rooms both **listed as `"allow"`** in the user's `m.presence.sharing` configuration and
   with an `m.room.presence_sharing` state event with `presence_sharing` set to `"suggest"`. Servers MUST NOT
   include rooms that do not satisfy this criteria.
2. Exclude any user IDs with a server name corresponding to **any server listed as `"deny"`** in the user's
   `m.presence.sharing` configuration.
3. Include all local users if the user's `m.presence.sharing` configuration has `share_locally` set to `true`.
   Servers SHOULD only include local users that the sender shares at least one room with.
4. Include all **users listed as `"allow"`** in the user's `m.presence.sharing` configuration. Servers SHOULD only
   include users from this list that the sender shares at least one room with.
5. Exclude any **users listed as `"deny"`** in the user's `m.presence.sharing` configuration.

Determine the delta from the previous recipient user set. If there is no previous state, the entire set is an addition.
If the recipient user set is left unchanged, emit a presence EDU using only the prior `stream_id` \- no `recipients`, no
`prev_id`. Otherwise, generate a `stream_id` for the new state. Emit a presence EDU for each destination of the
recipients in these updates, with `prev_id` set to the last `stream_id` sent to the destination if applicable,
`stream_id` set according to the new state, and `recipients` populated with the updates for the destination.

#### Inbound Processing

When a server receives a `m.presence` EDU over federation, servers follow these rules for distributing the presence
change over both `/sync` and `/_matrix/client/v3/presence/{userId}/status`:
* **`stream_id` missing:** Servers SHOULD distribute the presence transition to every local user that shares a room
  with the `user_id` of the EDU, following current presence behaviour.
* **`recipients` missing, `prev_id` missing:** If `stream_id` matches the server's latest known ID, it MUST reuse
  its current view of the recipient user set to distribute the presence change to users in the set.
* **`recipients` present, `prev_id` missing:** Servers MUST initialise this as a new set using `recipients` if they
  have no existing state for the user, and only distribute the presence change to users added by `recipients`.
* **`recipients` present, `prev_id` present:** Servers MUST apply the delta to the set corresponding to `prev_id`
  and only distribute the presence change to users in the resulting set, superseding `prev_id` in the process.

If `prev_id` is present but differs from the previous `stream_id`, or `stream_id` is present on its own but
unrecognised, servers SHOULD query the `GET /_matrix/federation/v1/query/presence_recipients` endpoint on the
origin server.

### Server-Server Endpoint `GET /_matrix/federation/v1/query/presence_recipients`

Servers that do not recognise a `stream_id` or `prev_id` in an incoming `m.presence` EDU need a way to ask the
origin server for the user's latest `stream_id` and a snapshot of its recipient user set. This proposal introduces
a new federation endpoint to address this need. If a server cannot determine the proper recipient user set \- for
example, if this endpoint returns an error \- it SHOULD be assumed to be empty (`[]`) until the server can fetch
the full set.

<table>
  <tbody>
    <tr>
      <th scope="row">Rate limited:</th>
      <td>No</td>
    </tr>
    <tr>
      <th scope="row">Requires authentication:</th>
      <td>Yes</td>
    </tr>
  </tbody>
</table>

#### Request

##### Request parameters

| Name      | Type     | Description                                                                |
|-----------|----------|----------------------------------------------------------------------------|
| `user_id` | `string` | **Required:** The user ID to query. Must be local to the queried server.   |

#### Responses

| Status | Description                                                                                |
|--------|--------------------------------------------------------------------------------------------|
| `200`  | The corresponding user's latest `stream_id` and recipient user set for the sending server. |
| `404`  | The user does not have a recipient set available for the sending server.                   |

The 404 response uses the same format as in the existing query endpoints.

##### 200 response

| Name         | Type                        | Description                                                                      |
|--------------|-----------------------------|----------------------------------------------------------------------------------|
| `stream_id`  | `integer`                   | **Required:** A unique identifier for the user's current recipient user set.     |
| `recipients` | `[`[`User`][mxid-format]`]` | **Required:** An array of local recipients the user intends to push presence to. |

```json
{
    "stream_id": 1,
    "recipients": [
        "@jesse:example.com",
        "@jane:example.com"
    ]
}
```

### Client-Server Capability

Servers implementing Selective Presence MUST include the capability `m.selective_presence` in their response to the `GET
/_matrix/client/v3/capabilities` endpoint. This allows clients to identify servers using Selective Presence so they MAY
avoid showing inapplicable UI on servers without it, or inform users when their servers are upgraded to use it.

## Potential issues

### Presence Access

Selective Presence *disables presence by default*. This may complicate future proposals that require publicly
accessible presence information, and may change the way users interact with presence features. However, as
previously mentioned, presence should not be public by default. A future proposal may address public, fetchable
presence (see [Alternatives](#Alternatives)).

### Presence Data "Leaks"

* Presence information may be exposed to unintended or undesirable users by bad-acting servers if any of their
  users are included in the recipient user set. This proposal is a best-effort approach and cannot combat this.
* Presence information may be exposed to unintended or undesirable users by the user's own homeserver, for instance
  if the administrator modifies their account data to trick them.
* Remote homeservers may deduce parts of users' exclusion lists probabilistically. The scope of this is limited by
  only sending relevant data to each homeserver.
* The introduced account data for exclusion lists is sensitive and not encryptable (as in [MSC4483]), but this is
  information the server would likely know by other means (e.g. [`m.ignored_user_list`])

### Lack of Presence Requests

Prior to [MSC1819], Presence Lists provided for a "presence request" feature. This may be desirable in the future,
but it is considered out of scope for this proposal.

### Performance

Homeserver operators and implementers may wish to limit the performance impacts of presence, particularly as the
goal of Selective Presence is to make presence viable for popular use. Potential options for doing so may include:
* Limiting the ability of users to share presence with rooms above a certain number of members
* Limiting the number of entities (or total recipient users) users can have in their presence sharing maps

### Presence EDU Batch Sizes

Homeserver implementations or the specification may, in future, limit EDU sizes in the same way PDU sizes are limited.
This proposal does not specify a strict limit on batch sizes because it is currently unclear what the size limit of EDUs
may be, so a batch size will need to be specified if this happens. If the limit turns out to be 64KiB, as it is for
PDUs, and assuming the `status_msg` stays within 255 bytes, you cannot fit more than 250 full 255 byte entities into a
presence EDU with a single state transition.

## Alternatives

### Pull-based Presence

A pull-based system leads to unnecessary requests over federation on polling intervals when no presence updates are
available, creating inefficiencies that may be intolerable for mainstream use and still requiring access control to
achieve any privacy benefits. An auxiliary fetchable presence system is considered complementary follow-up work to
allow users to make their presence public.

### Receiver Resolution

Instead of sending a finalised list of recipient users to remote servers, the user's preferences (allowed rooms and
users, denied users) could be sent over federation. This proposal uses sender-side user resolution to avoid sending
a "block list" to third parties, and to keep resolution consistent with the sending homeserver's state.

### Entity Selection Affordances

Servers could be permitted in the inclusion list, and rooms could be permitted in the exclusion list. The authors
of this proposal found no reason for doing so. In organisation environments where it may be desired to share
presence with an entire homeserver, users are almost certainly on the same local homeserver, where `share_locally`
applies, or share a room with everyone in the organisation, which the users can set as `"allow"`. Excluding a room
has no practical benefits as users can simply not include it in the configuration.

Globs were prohibited in presence sharing maps to avoid introducing security issues for servers running glob parsing on
arbitrary user-provided strings, and because users are not typically namespaced beyond servers in a way that would be
suitable for glob selection.

### Entity Resolution Ordering

The inclusion and exclusion lists could be applied in different orders; for example, if a user of a homeserver is set to
`"allow"`, and the homeserver is set to `"deny"`, should the user become an exception, or should the whole homeserver be
prevented from receiving the presence? It was decided that users should always be the overriding rule, otherwise a user
wouldn't explicitly `"allow"` them, and only allowing one other entity type for either option prevents conflicts.

### Per-Room Hint Following

In this proposal, the `"allow"` state means "follow the room's hint state." Instead, the user's configuration could
be decoupled from room hints, meaning users could broadcast their presence to all users of a room regardless of
whether the room administrators have enabled the hint. This can create issues in large rooms and conflicts with the
recommendation purpose of the hints system.

Allowing room administrators to suggest that their members share presence means users can still see presence for
members of small rooms (assuming they opt in to this behaviour) without explicitly creating user lists. These are
the rooms where presence matters most: small groups of friends, organisation environments, etc.

Only allowing users to follow hints via `"allow"` means a `"forbid"` hint state explicitly forbids presence sharing
for all users of a room. This allows room administrators to retroactively *disable* presence sharing for rooms as
they grow; for example, if a previously private room grows to be public and contain many members, a room
administrator may wish to disable presence sharing in the room.

### `m.room.presence_sharing` states

There are multiple potential states for room hints, and just as many potential defaults. It was ultimately
determined that this proposal should only specify the actual states of `"suggest"` or `"forbid"`, leaving the
decision of when to ask users if they would like to enable presence up to the clients.

### Room Account Data

It was proposed that a user's `m.presence.sharing` `"rooms"` configuration could live in room account data, but
this proposal opted against doing so to avoid fragmenting the configuration between different sources.

### Fallback Behaviours

#### Client-Server Sync

If a server were to receive an EDU with no `stream_id`, it could either ignore the EDU, or sync it to clients of its
local users that share a room with the `user_id` in the EDU, as is the current behaviour. To preserve backwards
compatibility for older servers unaware of the `recipients` system, this proposal specifies that the current behaviour
should be invoked for these EDUs. The authors of this proposal intend for this fallback behaviour to be removed when a
sufficient proportion of the network has updated to use Selective Presence, which will entirely remove the excess
traffic of publicly broadcasted presence and allow implementers to simplify processing on receiving homeservers.

#### Server-Server Dispatch

If a user's `account_data` were missing `m.presence.sharing` configuration, the sending server could either invoke the
current behaviour by sending a presence EDU with no `stream_id`, or avoid sending presence for the user entirely. While
backwards compatibility is important where it is possible, allowing *clients* to induce this behaviour intentionally
would create a user-controlled bypass for Selective Presence altogether, defeating its purpose. Therefore, this proposal
opts to forbid sending presence for users that have not set an `m.presence.sharing` configuration.

## Security considerations

This proposal does not introduce any new security considerations as far as its authors are aware.

## Future work

The following complementary proposals are planned:
* Increasing presence TTLs and improving batching behaviour
* Fetchable presence, possibly involving [MSC4133]'s profile key-value fields
* Sliding Sync extension for presence
* Presence Requests

## Unstable prefix

| Stable identifier         | Purpose                                                            | Unstable identifier                                          |
| ------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------ |
| `recipients`              | Recipient users to add and delete in federation presence EDU       | `org.continuwuity.presence_v2.msc4495.recipients`            |
| `stream_id`               | Current recipient user set identifier federation presence EDU      | `org.continuwuity.presence_v2.msc4495.stream_id`             |
| `prev_id`                 | Previous recipient user set identifier in federation presence EDU  | `org.continuwuity.presence_v2.msc4495.prev_id`               |
| `m.presence.sharing`      | `account_data` entry for presence sharing config                   | `org.continuwuity.presence_v2.msc4495.presence.sharing`      |
| `m.presence.prompted`     | `account_data` entry for persisting presence hint prompt responses | `org.continuwuity.presence_v2.msc4495.presence.prompted`     |
| `m.room.presence_sharing` | Room state event for presence sharing hint                         | `org.continuwuity.presence_v2.msc4495.room.presence_sharing` |
| `m.selective_presence`    | Capability to announce Selective Presence behaviour to clients     | `org.continuwuity.presence_v2.msc4495.selective_presence`    |

Servers may advertise support for Selective Presence by listing `org.continuwuity.presence_v2.msc4495` in the
`unstable_features` section of the response to [`GET /_matrix/client/versions`][cs-versions].

The stable endpoint `/_matrix/federation/v1/query/presence_recipients` will use the unstable identifier
`/_matrix/federation/unstable/org.continuwuity.presence_v2.msc4495/query/presence_recipients`.

Once this proposal completes FCP, servers may advertise support for the stable identifiers by listing
`org.continuwuity.presence_v2.msc4495.stable` in `unstable_features`; clients may use this while they
are waiting for the server to adopt a version of the spec that includes it.

## Dependencies

None.

[^1]: Synapse has had a meta-issue open about improving presence performance for 5 years: [#9478]
[^2]: Since 2018, homeserver operators have had performance concerns related to presence, and even raised them
      as bugs in Synapse. [#3971] [#9339]

[#3971]: https://github.com/matrix-org/synapse/issues/3971
[#4417]: https://github.com/matrix-org/synapse/issues/4417
[#9339]: https://github.com/matrix-org/synapse/issues/9339
[#9478]: https://github.com/matrix-org/synapse/issues/9478
[MSC1819]: https://github.com/matrix-org/matrix-spec-proposals/pull/1819
[MSC4133]: https://github.com/matrix-org/matrix-spec-proposals/pull/4133
[MSC4325]: https://github.com/matrix-org/matrix-spec-proposals/pull/4325
[MSC4483]: https://github.com/matrix-org/matrix-spec-proposals/pull/4483
[presence-v1-privacy]: https://spec.matrix.org/v1.17/client-server-api/#security-considerations-4
[`m.presence` EDU]: https://spec.matrix.org/v1.18/server-server-api/#definition-mpresence
[User Presence Update]: https://spec.matrix.org/v1.18/server-server-api/#definition-mpresence_user-presence-update
[Device List Update]: https://spec.matrix.org/v1.18/server-server-api/#definition-mdevice_list_update_device-list-update
[mxid-format]: https://spec.matrix.org/v1.18/appendices/#user-identifiers
[roomid-format]: https://spec.matrix.org/v1.18/appendices/#room-ids
[servername-format]: https://spec.matrix.org/v1.18/appendices/#server-name
[`account_data`]: https://spec.matrix.org/v1.18/client-server-api/#client-config
[cs-versions]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions
[cs-createroom]: https://spec.matrix.org/v1.18/client-server-api/#post_matrixclientv3createroom
[`m.ignored_user_list`]: https://spec.matrix.org/v1.18/client-server-api/#mignored_user_list
[room-upgrades]: https://spec.matrix.org/v1.18/client-server-api/#server-behaviour-21
