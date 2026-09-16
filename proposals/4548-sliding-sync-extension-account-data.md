# MSC4548: Sliding Sync Extensions: Account data

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync)
only includes core room data and omits other data, such as account data, from the sync response.
Instead, such data is left to "extensions", which clients opt into individually via the `extensions`
field of the sync request.

This MSC defines the extension for [account
data](https://spec.matrix.org/latest/client-server-api/#client-config), both global and per-room.
Account data carries per-user settings, such as push rules, room tags, read markers, etc.

Supersedes [MSC3959](https://github.com/matrix-org/matrix-spec-proposals/pull/3959).

## Proposal

A new sliding sync extension is added, with the extension key `account_data`.

The extension follows the common extension semantics defined by
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). It is a per-room
extension. The common per-room fields (`lists` and `rooms`) control which rooms' account data is
returned. Global account data is returned whenever the extension is enabled, regardless of `lists`
and `rooms`.

### Extension request

The extension takes no fields beyond the common ones:

```jsonc
{
    "extensions": {
        "account_data": {
            "enabled": true,
            "lists": ["rooms", "dms"],
            "rooms": ["!abcd:example.com"]
        }
    }
}
```

### Extension response

If the extension is enabled, the server MUST include an `account_data` section in the `extensions`
response field whenever it has account data to send, as defined under [Semantics](#semantics). It
MAY omit the section when there is none. An absent section means nothing has changed.

The `ExtensionResult` has the following format:

| Name | Type | Required | Comment |
| - | - | - | - |
| `global` | `[AccountData]` | No | Global account data. Defaults to empty. |
| `rooms` | `{string: [AccountData]}` | No | A map of room ID to that room's account data. Defaults to empty. |

An `AccountData` has the format of the entries of the `account_data` sections of
[`/v3/sync`](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3sync_response-200_account-data):

| Name | Type | Required | Comment |
| - | - | - | - |
| `type` | `string` | Yes | The type of the account data. |
| `content` | `object` | Yes | The content of the account data. |

Each list contains at most one entry per `type`. A room with nothing to send MAY be omitted from
`rooms`. An empty list is equivalent to an absent entry.

For example:

```jsonc
{
    "extensions": {
        "account_data": {
            "global": [
                {
                    "type": "m.direct",
                    "content": { "@alice:example.com": ["!abcd:example.com"] }
                }
            ],
            "rooms": {
                "!abcd:example.com": [
                    {
                        "type": "m.tag",
                        "content": { "tags": { "m.favourite": { "order": 0.1 } } }
                    }
                ]
            }
        }
    }
}
```

### Semantics

Account data is keyed by `type` within a scope (global, or one room). An entry replaces the content
the client holds for that `type` in that scope. Account data cannot be deleted, so a `type` absent
from a response is unchanged.

The server judges what to send against the connection's state at the request's `pos`.
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) does not let the server
assume the client received a response until it sees a request carrying that response's `pos`. A
retried request with the same `pos` MUST receive the account data of the lost response again.

#### Global account data

The response to a request without `pos` MUST contain all of the user's global account data.
Otherwise, `global` MUST contain the global account data of every `type` that changed after the
request's `pos`.

As in [`/v3/sync`](https://spec.matrix.org/latest/client-server-api/#push-rules-events), the user's
push rules are global account data of type
[`m.push_rules`](https://spec.matrix.org/latest/client-server-api/#mpush_rules). A change to a push
rule is a change to that account data.

#### Room account data

`rooms` covers rooms that are in scope for the extension, as defined by the common per-room
extension semantics of [MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). A
room can be in scope without appearing in the top-level `rooms` section of the response.

Room account data is returned for an in-scope room regardless of the user's membership in it,
whereas `/v3/sync` returns it for joined and left rooms only. The user can set account data for any
room ID, including invites and knocks.

For an in-scope room:

- When the room enters scope on the connection for the first time, including in the response to a
  request without `pos`, the server MUST send all of the room's account data.
- When a room re-enters scope, the server MUST send at least the account data of every `type` that
  changed while the room was out of scope. The server MAY choose to send all account data for the
  room instead.
- Otherwise, the server MUST send the room's account data of every `type` that changed after the
  request's `pos`.

When a room drops out of scope, the client keeps the account data it holds for it. The server sends
no further updates for the room until it re-enters scope, so the data may be stale until then.

As in `/v3/sync`, room tags are room account data of type
[`m.tag`](https://spec.matrix.org/latest/client-server-api/#mtag), and fully read markers are room
account data of type [`m.fully_read`](https://spec.matrix.org/latest/client-server-api/#mfully_read).
A change made through the tags or read markers endpoints is a change to that account data.

#### Enabling partway through a connection

While the extension is disabled, no room is in scope for it.

When the extension is enabled for the first time on a connection, the response MUST contain all of
the user's global account data, as for a request without `pos`. Every in-scope room enters scope for
the first time, so under [Room account data](#room-account-data) it receives all of its account
data. A client can therefore defer the extension past its initial request.

When the extension is re-enabled after being disabled on the same connection, the server MAY send
only the account data that changed after the request's `pos`. This applies to `global` and to
`rooms`. Changes made while the extension was disabled MAY not be sent. Clients SHOULD NOT disable
the extension once enabled.

This matches the suggested semantics given in
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508).

#### Connections

Account data is per-user. Each connection receives changes relative to its own `pos`, and sending
a change on one connection does not affect what any other connection receives. A client MAY enable
the extension on more than one connection.

After a connection is reset with `M_UNKNOWN_POS`, the client's next request has no `pos` and
receives the full data under the rules above.

#### Long-polling

A change to global account data, or to the account data of an in-scope room, counts as an update
for the purposes of long-polling. The server MUST return immediately, even if there is nothing else
to send. A change to the account data of a room that is not in scope does not count.

## Potential issues

The response to a request without `pos` contains all global account data. `m.push_rules` and
`m.direct` grow with the number of rooms and can reach hundreds of kilobytes on large accounts. A
client can defer enabling the extension until after its first request, at the cost of one further
round trip before it has the data.

The extension has no filtering by `type`. A client receives all of its account data, including
types it does not use. A `types` request field could be added by a later MSC.

Account data cannot currently be deleted. An MSC that adds deletion, such as
[MSC3391](https://github.com/matrix-org/matrix-spec-proposals/pull/3391), would need to define how
this extension conveys it.

## Alternatives

`global` and each entry of `rooms` could be a map of `type` to `content` rather than a list. A map
encodes the one-entry-per-type property in the wire format. The list matches the
`account_data` sections of `/v3/sync`, so clients reuse their parsing, and it is the format
existing implementations use.

## Security considerations

The extension exposes the same information as the `account_data` sections of `/v3/sync`. Servers
MUST only return the account data of the authenticated user. A room being in scope for the extension
exposes nothing about the room itself, since the room account data returned is data the user set.

## Unstable prefix

The experimental implementations of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (e.g. Synapse, as used by
Element X) have supported this extension with the unprefixed `account_data` key on the
`/_matrix/client/unstable/org.matrix.simplified_msc3575/sync` endpoint.

Until this MSC is accepted, implementations MUST use `org.matrix.msc4548.account_data` as the
extension key on the stable [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186)
endpoint, `/_matrix/client/v4/sync`. The unprefixed `account_data` key remains in use on the unstable
`org.matrix.simplified_msc3575` endpoint for compatibility with existing implementations.

Per the common extension semantics of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), servers advertise support
for this extension in `unstable_features` of
[`/_matrix/client/versions`](https://spec.matrix.org/latest/client-server-api/#get_matrixclientversions)
by setting the following flags to `true`:

- `org.matrix.msc4548` while this MSC is unstabl; and
- `org.matrix.msc4548.stable` once this MSC is accepted and the server supports the extension as
  specified here, under the unprefixed `account_data` key on the stable endpoint, until it
  advertises the spec version containing this MSC.

## Dependencies

This MSC builds on [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) and
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), both of which have been
accepted.

## Appendix

### Changelog

Differences from the experimental implementation of simplified sliding sync in Synapse v1.151.0.

1. The `account_data` section may be omitted when there is nothing to send. Synapse always includes
   it, which remains permitted.
2. Enabling the extension for the first time on a connection returns all global account data.
   Synapse returns only the global account data that changed after `pos`.
