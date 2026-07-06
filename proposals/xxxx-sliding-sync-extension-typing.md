# MSC4508: Sliding Sync Extension: Typing Notifications

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync)
only includes core room data and omits other data, such as typing notifications, from the sync
response. Instead, such data is left to "extensions", which clients opt into individually via the
`extensions` field of the sync request.

This MSC defines the extension for typing notifications, so that clients using sliding sync can show
typing indicators in rooms.

Supersedes [MSC3961](https://github.com/matrix-org/matrix-spec-proposals/blob/kegan/ssext-typing/proposals/3961-sliding-sync-typing.md).

# Proposal

A new sliding sync extension is added, with the extension key `typing`.

## Common extension semantics

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) defines the `extensions`
request field as a map from extension key to an extension config, but leaves the format of the
config to the MSCs defining each extension. As this is the first such MSC, it defines the following
semantics, which are expected to be common to all extensions. Future extension MSCs may reference
this definition rather than redefine them.

> [!NOTE]
>
> There are a myriad of different use cases for extensions, e.g. typing notifications, to-device
> messages, etc, all of which have different semantics. For typing notifications the client only
> needs the latest state (rather than all updates), while for to-device messages the client must
> (eventually) receive every missed to-device message in order.

All extensions include the following fields:

| Name | Type | Required | Comment |
| - | - | - | - |
| `enabled` | `bool` | No | Whether the extension is enabled. Defaults to `false`. The server only processes the extension if this is `true`. |

Extension MSCs MUST address the behaviour when an extension that was absent or disabled is later
enabled on an existing connection. Extensions SHOULD leave the behaviour up to server
implementations unless there is a client UX need, as clients SHOULD enable the extensions they need
at the beginning of the connection. This gives the server flexibility to track extension data
efficiently, regardless of whether extensions are toggled. Servers MUST allow toggling extensions,
even if they only send newly changed data, and MUST NOT reject the request.

Extension MSCs MUST specify the expected behaviour of clients when the sliding sync connection is
reset (via `M_UNKNOWN_POS`).

Extension MSCs MUST specify when the sync response should be returned immediately versus continuing
with long-polling. Some extensions MAY not require certain updates to be returned immediately.

As with unknown fields elsewhere in the client-server API, servers MUST ignore extensions with keys
they do not recognise (rather than rejecting the request), so that newer clients remain compatible
with older servers.

## Common per-room extension semantics

Some extensions apply on a per-room basis, of which this is the first. We define the generic
per-room semantics here.

The per-room extensions include the following fields (as well as the ones above):

| Name | Type | Required | Comment |
| - | - | - | - |
| `lists` | `[string]` | No | Which lists (by list key, from the `lists` request field) the extension applies to. Defaults to `["*"]`. |
| `rooms` | `[string]` | No | Which room subscriptions (by room ID, from the `room_subscriptions` request field) the extension applies to. Defaults to `["*"]`. |

The `lists` and `rooms` arguments control which rooms are "in scope" for the extension. A room is in
scope if either of the following holds:

- it is currently within the range of one of the lists named in `lists` (i.e. after applying the
  list's filters, the room's index in the filtered list is within the list's range), or
- it is one of the room subscriptions named in `rooms`.

The special value `"*"` acts as a wildcard: `{"lists": ["*"]}` matches all lists in the request and
`{"rooms": ["*"]}` matches all room subscriptions in the request. An empty array matches nothing,
e.g. `{"lists": [], "rooms": ["*"]}` applies the extension only to room subscriptions. List keys
that are not in the request, and rooms that are either unknown or inaccessible to the user, are
ignored.

Note that a room being in scope does *not* require the room to have an entry in the `rooms` section
of the *response*: a room within a list's range is in scope even if the room has no other updates to
send. Also note that a room being in scope does not mean that the user is currently joined to it
(they may be invited, knocked, or have left); extension MSCs MUST ensure data cannot be leaked from
rooms the user isn't in and shouldn't have access to.

If a room was in scope, drops out of scope and then re-enters scope, extensions MUST ensure that the
client ends up with up-to-date state OR knows there is missing state that must be fetched. Extensions
SHOULD ensure that the amount of data included in the response is bounded (to limit overall response
size, especially if there has been a large delay between requests).

> [!TIP]
>
> Extensions that include an unbounded stream of updates, such as thread updates, may choose to
> return only the latest data and give a pagination token that can be used to fetch older data from
> an endpoint.
>
> Other extensions may choose the opposite approach of sending down batches of updates in sequential
> sync responses. This ensures the client gets all the data appropriately quickly without bloating
> the initial request with all the missed updates.
>
> Which is appropriate depends entirely on what the data is and how clients use it.

## Extension request

The `typing` extension takes no arguments beyond the common ones:

```jsonc
{
    "extensions": {
        "typing": {
            "enabled": true,
            "lists": ["rooms", "dms"],
            "rooms": ["!abcd:example.com"]
        }
    }
}
```

## Extension response

If the extension is enabled, the server MAY include a `typing` section in the `extensions` response
field, with the following format:

| Name | Type | Required | Comment |
| - | - | - | - |
| `rooms` | `{string: Event}` | No | A map of room ID to the `m.typing` ephemeral event for that room. |

The value for each room is the same `m.typing` event that would appear in the room's
`ephemeral.events` array in a [`/v3/sync`
response](https://spec.matrix.org/v1.17/client-server-api/#typing-notifications), e.g.:

```jsonc
{
    "extensions": {
        "typing": {
            "rooms": {
                "!abcd:example.com": {
                    "type": "m.typing",
                    "content": {
                        "user_ids": ["@alice:example.com", "@bob:example.com"]
                    }
                }
            }
        }
    }
}
```

As in `/v3/sync`, the `user_ids` field contains the complete list of users currently typing in that
room: it replaces, rather than updates, any typing state the client previously had for the room.

## Semantics

The response only includes rooms that are in scope for the extension (see above). Additionally,
servers MUST only send typing notifications for rooms the user is currently joined to, as with
`/v3/sync` (where ephemeral events only appear under the `join` section). Note that rooms in other
membership states can still be *in scope*: for example,
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) keeps rooms the user has
been kicked or banned from in lists. Such rooms MUST NOT have typing notifications sent.

For the rooms that remain:

- Whenever a room enters scope on a connection, the server MUST send the room's current typing
  state. This applies on an initial sync (no `pos`), when the room first comes into scope on the
  connection, and when it re-enters scope after having dropped out (e.g. after falling out of a
  list's range). As a minor optimisation, the server MAY omit the room if there are no users typing
  and the previously sent state (if any) was also empty. If the extension is enabled partway through
  a connection, the server MAY omit this initial data for rooms already in scope, per the common
  extension semantics above.
- On an incremental sync, an in-scope room is included if its typing state has changed since the
  previous request's `pos`.

When starting a new connection with an initial sync (no `pos`), clients MUST discard all typing
state previously received via this extension. This includes the case where the server has expired a
previous connection with `M_UNKNOWN_POS`. Rooms with no users typing need not be included in the
initial response, so after this reset the absence of a room means nobody is typing in it.

When a room drops out of scope the client MUST clear the typing notifications locally, as the server
will not inform the client of any further updates to the room (unless the room comes back into
scope).

A change in typing state of an in-scope room counts as an update for the purposes of long-polling:
it causes a waiting `/sync` request to return, even if there is nothing else to send. This can
result in a response whose `rooms` section is empty but whose `typing` extension section is not.

Typing is pure "latest state" data: each `m.typing` event replaces the previous state for the room,
rather than building on it. When a room (re-)enters scope, the server brings the client up-to-date
by sending the room's current typing state; it never has to replay the individual updates the room
missed while out of scope. Consequently, the server does not need to track which typing state it has
previously sent on a connection (unless it wants to use the omission optimisation described above).

# Potential issues

A room within the range of a scoped list receives typing updates even if the user is not currently
viewing it, which is wasted bandwidth for clients that only show typing indicators inside the room
view. Clients can avoid this by scoping the extension: for example `{"lists": [], "rooms": ["*"]}`
together with a room subscription for the currently-open room limits typing updates to that room.

# Alternatives

The common extension arguments (`enabled`, `lists`, `rooms`) could be defined in a separate
"extensions framework" MSC that each extension MSC depends on, rather than in this one. That adds an
extra MSC to the process for little benefit; instead this MSC defines them in a way that later
extension MSCs can reference.

# Security considerations

As with `/v3/sync`, servers MUST only send typing notifications for rooms the user is currently
joined to (see Semantics). Note that a room being in scope for the extension is *not* by itself a
sufficient permission check:
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) intentionally keeps rooms
the user has been kicked or banned from in lists, so such rooms can be in scope. The joined-rooms
requirement prevents leaking typing activity from rooms the user can no longer see (e.g. post-ban
activity).

# Unstable prefix

The experimental implementations of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (e.g. Synapse, as used by
Element X) have supported this extension with the unprefixed `typing` key on the
`/_matrix/client/unstable/org.matrix.simplified_msc3575/sync` endpoint.

Until this MSC is accepted, implementations MUST use `org.matrix.msc4508.typing` (substituting this
proposal's MSC number) as the extension key on the stable
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) endpoint. The unprefixed
`typing` key remains in use on the unstable `org.matrix.simplified_msc3575` endpoint for
compatibility with existing implementations.

# Dependencies

This MSC builds on [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186), which
at the time of writing has passed FCP but has not yet been released in the spec.
