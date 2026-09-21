# MSCXXXX: Sliding Sync Extensions: Receipts

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync)
only includes core room data and omits other data, such as read receipts, from the sync response.
Instead, such data is left to "extensions", which clients opt into individually via the `extensions`
field of the sync request.

This MSC defines the extension for
[receipts](https://spec.matrix.org/v1.17/client-server-api/#receipts). A client uses other users'
receipts to show who has read what, and its own user's receipts to share a read position between
devices and to compute unread state.

Supersedes [MSC3960](https://github.com/matrix-org/matrix-spec-proposals/pull/3960).

## Proposal

A new sliding sync extension is added, with the extension key `receipts`.

The extension follows the common extension semantics defined by
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). It is a per-room
extension. The common per-room fields (`lists` and `rooms`) control which rooms' receipts are
returned.

### Extension request

The extension takes no fields beyond the common ones:

```jsonc
{
    "extensions": {
        "receipts": {
            "enabled": true,
            "lists": ["rooms", "dms"],
            "rooms": ["!abcd:example.com"]
        }
    }
}
```

### Extension response

If the extension is enabled, the server MUST include a `receipts` section in the `extensions`
response field whenever it has receipts to send, as defined under [Semantics](#semantics). It MAY
omit the section when there are none. An absent section means nothing has changed.

The `ExtensionResult` has the following format:

| Name | Type | Required | Comment |
| - | - | - | - |
| `rooms` | `{string: Receipts}` | No | A map of room ID to receipts in that room. Defaults to empty. |

A `Receipts` has the format of the `content` of an
[`m.receipt`](https://spec.matrix.org/v1.17/client-server-api/#mreceipt) event: a map of event ID
to receipt type to user ID to `Receipt`, where a `Receipt` has the optional `ts` and `thread_id`
fields defined there. A room with nothing to send MAY be omitted from `rooms`. An empty `Receipts`
is equivalent to an absent entry.

For example:

```jsonc
{
    "extensions": {
        "receipts": {
            "rooms": {
                "!abcd:example.com": {
                    "$1435641916114394fHBLK:example.com": {
                        "m.read": {
                            "@alice:example.com": {
                                "ts": 1436451550453,
                                "thread_id": "main"
                            }
                        },
                        "m.read.private": {
                            "@self:example.com": {
                                "ts": 1661384801651
                            }
                        }
                    }
                }
            }
        }
    }
}
```

Unlike `/v3/sync`, the receipts are *not* wrapped in an `m.receipt` ephemeral event with `type` and
`content` fields. The extension can only ever carry receipts, so the wrapper conveys no information.
This matches the typing extension of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508).

### Semantics

Receipts are deltas, as in `/v3/sync`. A receipt replaces the receipt the client holds for the same
user, receipt type and `thread_id` in that room, as described under [Client
behaviour](https://spec.matrix.org/v1.17/client-server-api/#client-behaviour-4) in the receipts
module. Receipts the response does not mention are unchanged. A client applies a `Receipts` as it
would the `content` of an `m.receipt` event from `/v3/sync`.

The server judges what to send against the connection's state at the request's `pos`.
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) does not let the server
assume the client received a response until it sees a request carrying that response's `pos`. A
retried request with the same `pos` MUST receive the receipts of the lost response again.

#### Which rooms

`rooms` covers rooms that are in scope for the extension, as defined by the common per-room
extension semantics of [MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). A
room can be in scope without appearing in the top-level `rooms` section of the response.

Servers MUST only send receipts for rooms the user is currently joined to, as in `/v3/sync`, where
ephemeral events appear under the `join` section only. A room in another membership state can still
be in scope: [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) keeps rooms
the user has been kicked or banned from in lists. Such rooms MUST NOT have receipts sent.

Servers MUST NOT send another user's `m.read.private` receipts, as the receipts module requires. The
user's own `m.read.private` receipts are sent.

#### Which receipts

The receipts of a room are unbounded: a room with many members accumulates a receipt per member per
thread, on events the client may never view. The extension therefore does not send a room's full
receipts. Instead, when a room enters scope, it sends the *initial receipts* of the room, which are:

- the receipts, of every user, on the events in the room's `timeline` in this response; and
- all of the user's own receipts in the room, of every receipt type, threaded and unthreaded,
  whether or not the events they refer to are in the timeline.

The user's own receipts are always included so that a client learns the read position set by the
user's other devices, and can compute unread state, without those receipts having to fall within the
timeline. Other users' receipts on events outside the timeline are not sent. The client learns them
when they next change, if the room is still in scope.

The server SHOULD also include receipts, of every user, on events it sent in the room's `timeline`
earlier on the connection. This matters when the room is not in the top-level `rooms` section of
the response, for example when the extension is enabled after the room was first sent. A server that
does not track which events it has sent MAY send only the receipts listed above.

For an in-scope, joined room:

- When the room enters scope on the connection for the first time, including in the response to a
  request without `pos`, the server MUST send the room's initial receipts.
- When the room re-enters scope after having dropped out, the server MUST send at least the receipts
  that changed after the `pos` of the first request on the connection in which the room was out of
  scope. The server MAY choose to send the room's initial receipts instead.
- Otherwise, the server MUST send the receipts that changed after the request's `pos`.

Additionally, whenever the room's entry in the top-level `rooms` section of the response has
`initial` or `expanded_timeline` set to `true`, the server MUST send the receipts, of every user, on
the events in the room's `timeline` in this response. These flags mean the response carries events
the client has not seen on this connection, and the client needs their receipts as it would on the
room first entering scope.

When a room drops out of scope, the client keeps the receipts it holds for it. The server sends no
further updates for the room until it re-enters scope, so the data may be stale until then.

#### Enabling partway through a connection

While the extension is disabled, no room is in scope for it.

When the extension is enabled for the first time on a connection, every in-scope room enters scope
for the first time, so under [Which receipts](#which-receipts) it receives its initial receipts. A
client can therefore defer the extension past its initial request.

When the extension is re-enabled after being disabled on the same connection, the server MAY send
only the receipts that changed after the request's `pos` for rooms it sent receipts for earlier on
the connection, in place of the re-entry rule under [Which receipts](#which-receipts). Changes made
while the extension was disabled are then not sent. Rooms that had not been in scope on the
connection enter scope for the first time and receive their initial receipts. Clients SHOULD NOT
disable the extension once enabled.

#### Connections

Each connection receives changes relative to its own `pos`, and sending a receipt on one connection
does not affect what any other connection receives. A client MAY enable the extension on more than
one connection.

After a connection is reset with `M_UNKNOWN_POS`, the client's next request has no `pos`, so every
in-scope room enters scope for the first time and receives its initial receipts. The client keeps
the receipts it holds and applies the response like any other. A receipt the client holds for a
user is either still current or older than that user's current receipt, and any receipt on an event
in the new timeline is replaced.

#### Long-polling

A change to the receipts of an in-scope, joined room counts as an update for the purposes of
long-polling. The server MUST return immediately, even if there is nothing else to send. A change to
the receipts of a room that is not in scope does not count.

## Potential issues

The initial receipts of a room grow with the number of members who have read the events in the
timeline. In a large room a single event can carry thousands of receipts, and the timeline can
carry `timeline_limit` such events. A client can keep this down with a small `timeline_limit`, or
by scoping the extension to the rooms it is displaying, as for typing notifications in
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508).

A client does not receive other users' receipts on events it fetches from
[`/messages`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3roomsroomidmessages),
nor on events the server sent earlier on the connection if the server does not track them. Such
events show no read markers until a receipt on them changes. A later MSC could add receipts to
`/messages`.

A server that sends the initial receipts when a room re-enters scope, rather than the changes since
it dropped out, leaves the client with stale receipts for users whose current receipt is on an
event outside the timeline. Receipts rarely move backwards, so the client shows such a user further
behind than they are, which is what a client that had just synced the room for the first time would
show too. The alternative, sending every change since the room dropped out, has no upper bound.

Receipts arrive for every in-scope room, whether or not the user is viewing it. Clients that only
show read markers inside the room view can scope the extension with `{"lists": []}` and a room
subscription for the open room.

## Alternatives

The response could wrap each room's receipts in an `m.receipt` ephemeral event with `type` and
`content` fields, matching `/v3/sync` and the experimental implementations. That would let clients
reuse an existing code path for parsing the event, but the wrapper is redundant when the extension
can only carry one type of data, and
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508) already drops it for typing
notifications.

The server could send all of a room's receipts when the room enters scope, as `/v3/sync` does on an
initial sync. The size of that is unbounded, and most of it is for events the client will never
display. This is the reason [MSC3960](https://github.com/matrix-org/matrix-spec-proposals/pull/3960)
limited the initial receipts to the timeline, and this MSC keeps that.

[MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575) proposed delta tokens so
that a client could avoid receiving receipts it already holds on an initial sync. MSC4186 dropped
delta tokens, and this MSC does not reintroduce them.

## Security considerations

The extension exposes the same information as the `m.receipt` events of `/v3/sync`. Servers MUST
only send receipts for rooms the user is currently joined to, and MUST NOT send other users'
`m.read.private` receipts, as under [Which rooms](#which-rooms). A room being in scope for the
extension is not by itself a sufficient permission check, since
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) keeps rooms the user has
been kicked or banned from in lists. The joined-rooms requirement prevents leaking read activity
from rooms the user can no longer see.

## Unstable prefix

The experimental implementations of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (e.g. Synapse, as used by
Element X) have supported this extension with the unprefixed `receipts` key on the
`/_matrix/client/unstable/org.matrix.simplified_msc3575/sync` endpoint.

Until this MSC is accepted, implementations MUST use `org.matrix.mscXXXX.receipts` as the extension
key on the stable [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) endpoint,
`/_matrix/client/v4/sync`. The unprefixed `receipts` key remains in use on the unstable
`org.matrix.simplified_msc3575` endpoint for compatibility with existing implementations.

Per the common extension semantics of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), servers advertise support
for this extension in `unstable_features` of
[`/_matrix/client/versions`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientversions)
by setting the following flags to `true`:

- `org.matrix.mscXXXX` while this MSC is unstable; and
- `org.matrix.mscXXXX.stable` once this MSC is accepted and the server supports the extension as
  specified here, under the unprefixed `receipts` key on the stable endpoint, until it advertises
  the spec version containing this MSC.

A server MUST NOT advertise either flag while its implementation does not comply with this MSC,
including under the unprefixed key on the unstable endpoint. See the [changelog](#changelog) for the
known differences in Synapse.

## Dependencies

This MSC builds on [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) and
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), both of which have been
accepted.

## Appendix

### Changelog

Differences from the experimental implementations of simplified sliding sync in Synapse v1.151.0
and matrix-rust-sdk 0.19.0.

1. The per-room value in the response is the bare `content` of an `m.receipt` event, rather than
   the full event with `type` and `content` fields. Synapse sends, and matrix-rust-sdk expects, the
   full event.
2. Receipts are only sent for rooms the user is joined to. Synapse sends them for any in-scope
   room.
3. The `receipts` section may be omitted when there is nothing to send. Synapse always includes it,
   which remains permitted.
4. When a room enters scope without being in the top-level `rooms` section of the response, the
   server SHOULD send receipts on events it sent in the room's timeline earlier on the connection.
   Synapse sends only the user's own receipts in that case.
