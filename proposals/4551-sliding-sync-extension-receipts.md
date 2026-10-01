# MSC4551: Sliding Sync Extensions: Receipts

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync)
only includes core room data in the sync response. Other data, such as read receipts, comes from
"extensions", which a client enables one by one in the `extensions` field of the request.

This MSC defines the extension for
[receipts](https://spec.matrix.org/v1.19/client-server-api/#receipts). A client uses other users'
receipts to show who has read what. It uses the user's own receipts to share a read position
between devices and to compute unread state.

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
[`m.receipt`](https://spec.matrix.org/v1.19/client-server-api/#mreceipt) event. It is a map of
event ID to receipt type to user ID to `Receipt`, where a `Receipt` has the optional `ts` and
`thread_id` fields defined there. A room with nothing to send MAY be omitted from `rooms`. An empty
`Receipts` is equivalent to an absent entry.

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
`content` fields. The extension only carries receipts, so the wrapper adds nothing. This matches
the typing extension of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508).

### Semantics

Receipts are deltas, as in `/v3/sync`. A receipt replaces the receipt the client holds for the same
user, receipt type and `thread_id` in that room, as described under [Client
behaviour](https://spec.matrix.org/v1.19/client-server-api/#client-behaviour-4) in the receipts
module. Receipts the response does not mention are unchanged. A client applies a `Receipts` as it
would the `content` of an `m.receipt` event from `/v3/sync`.

The server decides what to send from the connection's state at the request's `pos`.
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) does not let the server
assume the client received a response until it sees a request carrying that response's `pos`. A
retried request with the same `pos` MUST receive the receipts of the lost response again. As a
specific example, a retried request with the same `pos` and request body MUST receive the receipts
of the lost response again (unless they were since replaced).

#### Which rooms

`rooms` covers rooms that are in scope for the extension, as defined by the common per-room
extension semantics of [MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). A
room can be in scope without appearing in the top-level `rooms` section of the response.

Servers MUST only send receipts for rooms the user is currently joined to, as in `/v3/sync`, where
ephemeral events appear under the `join` section only.
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) keeps rooms the user has
left, or been kicked or banned from, in lists. For this extension, a room the user is not joined to
is out of scope, even if a list or subscription covers it. When the user rejoins a room, the room is
considered to have entered the scope for the first time when deciding [Which
receipts](#which-receipts), as though the connection had never seen it. The client applies the
initial receipts as it would after a connection reset, under [Connections](#connections).

Servers MUST NOT send another user's `m.read.private` receipts, as the receipts module requires. The
user's own `m.read.private` receipts are sent.

#### Which receipts

The receipts of a room grow with its membership and its thread count. A room accumulates a receipt
per member per receipt type per thread, most of them on events the client will never view. So the
extension does not send a room's full receipts. Instead, when a room enters scope, the server sends
the *initial receipts* of the room, which are:

- the receipts, of every user, on the events in the room's `timeline` in this response; and
- all of the user's own receipts in the room, of every receipt type, threaded and unthreaded,
  whether or not the events they refer to are in the timeline.

The user's own receipts are always included. A client needs them to learn the read position set by
its other devices and to compute unread state, and they are often on events outside the timeline.
Other users' receipts on events outside the timeline are not sent. The client learns them when they
next change, if the room is still in scope.

For an in-scope room:

- When the room enters scope on the connection for the first time, the server MUST send the room's
  initial receipts. This includes the response to a request without `pos`, and the response after
  the user rejoins the room.
- When the room re-enters scope after having dropped out, the server MUST send the receipts that
  changed after the `pos` of the first request on the connection in which the room was out of
  scope. A receipt that changed more than once need only be sent once, with its current value.
- Otherwise, the server MUST send the receipts that changed after the request's `pos`.

A server that cannot or does not want to send every change made while a room was out of scope MUST
NOT only send a partial subset of the receipts. It instead expires the connection by responding with
`M_UNKNOWN_POS`, which [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186)
permits when there are many updates to send. The client's next request then has no `pos`, and every
in-scope room receives its initial receipts, as under [Connections](#connections).

Additionally, whenever the room's entry in the top-level `rooms` section of the response has
`initial` or `expanded_timeline` set to `true`, the server MUST send the receipts, of every user, on
the events in the room's `timeline` in this response. These flags mean the response carries events
the client has not seen on this connection, so the client needs their receipts. This rule applies
in addition to the rules above. A room that re-enters scope with `expanded_timeline` set receives
both the receipts that changed while it was out and the receipts on the events in the timeline.

> [!Note]
>
> This rule ensures the client receives the receipts on every event that sync sends it. The aim is
> that a client can get the receipts on every event it receives, whichever endpoint returned the
> event. A later MSC could add receipts to `/messages` and the other endpoints that return events.

When a room drops out of scope, the client keeps the receipts it holds for it. The server sends no
further updates for the room until it re-enters scope, so the data may be stale until then.

#### Enabling partway through a connection

While the extension is disabled, no room is in scope for it.

When the extension is enabled for the first time on a connection, every in-scope room enters scope
for the first time, so under [Which receipts](#which-receipts) it receives its initial receipts. A
client can therefore enable the extension after its initial request.

> [!Note]
>
> When the extension is enabled partway through a connection, most in-scope rooms have no entry in
> the top-level `rooms` section, and those that do carry only the events since `pos`. The initial
> receipts are therefore the user's own receipts and the receipts on those events. Receipts on
> events sent earlier on the connection are not sent.

When the extension is re-enabled after being disabled on the same connection, the server MAY treat
it as if all past receipts had already been delivered. Only receipts received after the extension
was re-enabled need to be returned. This follows the common extension semantics of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), which leave this case to
server implementations. Rooms that had not been in scope on the connection enter scope for the first
time and receive their initial receipts.

Clients SHOULD NOT disable the extension once enabled.

#### Connections

Each connection receives changes relative to its own `pos`, and sending a receipt on one connection
does not affect what any other connection receives. A client MAY enable the extension on more than
one connection.

After a connection is reset with `M_UNKNOWN_POS`, the client's next request has no `pos`, so every
in-scope room enters scope for the first time and receives its initial receipts. The client keeps
the receipts it holds and applies the response like any other. A receipt the client already holds
is either still current or older than that user's current receipt, and is replaced when the current
receipt is among the initial receipts.

#### Long-polling

A change to the receipts of an in-scope room counts as an update for the purposes of
long-polling. The server MUST return immediately, even if there is nothing else to send. A change to
the receipts of a room that is not in scope does not count.

## Potential issues

The initial receipts of a room grow with the number of members who have read the events in the
timeline. In a large room a single event can carry thousands of receipts, and the timeline can
carry `timeline_limit` such events. A client can keep this down with a small `timeline_limit`, or
by scoping the extension to the rooms it is displaying, as for typing notifications in
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508).

A client does not receive other users' receipts on events it fetches from
[`/messages`](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3roomsroomidmessages).
The same applies to events outside the timeline of the response in which the room entered scope,
even if the client received those events earlier on the connection. Such events show no read markers
until a receipt on them changes.
A later MSC could add receipts to `/messages`.

When a room re-enters scope, the server has to send every receipt that changed while the room was
out. Only the current value of each receipt is needed, so this is bounded by one receipt per user
per receipt type per thread, the same bound as the room's full receipts. A server that does not
want to send that much can reset the connection instead, at the cost of the client resyncing every
room.

## Alternatives

The response could wrap each room's receipts in an `m.receipt` ephemeral event with `type` and
`content` fields, matching `/v3/sync` and the experimental implementations. The wrapper would let a
client reuse its `/v3/sync` parsing, but it is redundant when the extension only carries receipts.
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508) already drops it for typing
notifications.

The server could send all of a room's receipts when the room enters scope, as `/v3/sync` does on an
initial sync. The size of that grows with the room's membership, and most of it is for events the
client will never display. This is the reason
[MSC3960](https://github.com/matrix-org/matrix-spec-proposals/pull/3960) limited the initial
receipts to the timeline, and this MSC keeps that.

The server could send the initial receipts when a room re-enters scope, in place of the changes made
while it was out. However, clients would then not know which of the previously returned receipts
were stale and could would show the stale receipts on the older events.

[MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575) proposed delta tokens so
that a client could avoid receiving receipts it already holds on an initial sync. MSC4186 dropped
delta tokens, and this MSC does not reintroduce them.

## Security considerations

The extension exposes the same information as the `m.receipt` events of `/v3/sync`. Servers MUST
only send receipts for rooms the user is currently joined to, and MUST NOT send other users'
`m.read.private` receipts, as under [Which rooms](#which-rooms). A room being in a list or
subscription is not by itself a sufficient permission check, since
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) keeps rooms the user has
been kicked or banned from in lists. The joined-rooms requirement prevents leaking read activity
from rooms the user can no longer see.

## Unstable prefix

The experimental implementations of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (e.g. Synapse, as used by
Element X) have supported this extension with the unprefixed `receipts` key on the
`/_matrix/client/unstable/org.matrix.simplified_msc3575/sync` endpoint.

Until this MSC is accepted, implementations MUST use `org.matrix.msc4551.receipts` as the extension
key on the stable [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) endpoint,
`/_matrix/client/v4/sync`. The unprefixed `receipts` key remains in use on the unstable
`org.matrix.simplified_msc3575` endpoint for compatibility with existing implementations.

Per the common extension semantics of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), servers advertise support
for this extension in `unstable_features` of
[`/_matrix/client/versions`](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientversions)
by setting the following flags to `true`:

- `org.matrix.msc4551` while this MSC is unstable, covering the `org.matrix.msc4551.receipts` key
  on the stable endpoint; and
- `org.matrix.msc4551.stable` once this MSC is accepted and the server supports the extension as
  specified here, under the unprefixed `receipts` key on the stable endpoint, until it advertises
  the spec version containing this MSC.

Neither flag covers the unprefixed `receipts` key on the unstable endpoint, which keeps its existing
behaviour so that existing clients continue to work. See the
[appendix](#differences-from-experimental-implementations) for the known differences in Synapse.

## Dependencies

This MSC builds on [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) and
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), both of which have been
accepted.

## Appendix

### Differences from experimental implementations

Differences from the experimental implementations of simplified sliding sync in Synapse v1.151.0
and matrix-rust-sdk 0.19.0.

1. The per-room value in the response is the bare `content` of an `m.receipt` event, rather than
   the full event with `type` and `content` fields. Synapse sends, and matrix-rust-sdk expects, the
   full event.
2. The `receipts` section may be omitted when there is nothing to send. Synapse always includes it,
   which remains permitted.
3. When a room's entry in the top-level `rooms` section has `expanded_timeline` set, the server
   sends the receipts on the timeline in addition to the receipts that changed since the room was
   last sent, or since it dropped out of scope. Synapse sends the initial receipts instead, and
   omits changes on events outside the timeline.
