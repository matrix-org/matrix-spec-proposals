# MSC4538: Sliding Sync Extensions: To-Device messages

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync)
only includes core room data and omits other data, such as to-device messages, from the sync
response. Instead, such data is left to "extensions", which clients opt into individually via the
`extensions` field of the sync request.

This MSC defines the extension for to-device messages. End-to-end encryption distributes keys over
to-device messages, so without this extension a client using sliding sync must also poll
[`/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync) to take part
in encryption.

Supersedes [MSC3885](https://github.com/matrix-org/matrix-spec-proposals/pull/3885).

## Proposal

A new sliding sync extension is added, with the extension key `to_device`.

The extension follows the common extension semantics defined by
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). It is not a per-room
extension, so the common per-room fields (`lists` and `rooms`) do not apply.

The server deletes a to-device message once the client has acknowledged it. Acknowledgement is
therefore tracked by a token of the extension's own (`since`/`next_batch`) rather than by the
connection's `pos`. See [Acknowledgement](#acknowledgement) and [Alternatives](#alternatives).

### Extension request

In addition to the common `enabled` field, the `ExtensionConfig` has the following fields:

| Name | Type | Required | Comment |
| - | - | - | - |
| `limit` | `int` | No | The maximum number of messages to return in one response. Must be a positive integer. Defaults to 100. |
| `since` | `string` | No | The `next_batch` from the last response of this extension the client processed. Omitted until the client has received one. |

For example:

```jsonc
{
    "extensions": {
        "to_device": {
            "enabled": true,
            "limit": 100,
            "since": "1234"
        }
    }
}
```

A `limit` that is not a positive integer MUST be rejected with a 400 and an error code of
`M_INVALID_PARAM`. The server MAY return fewer messages than `limit`. The send-to-device module
recommends a limit of 100 for `/v3/sync`, and servers SHOULD support at least that here.

Clients MUST treat `next_batch` as opaque. A client MUST send as `since` the `next_batch` from the
last response of this extension it processed, on any connection (see [Connections](#connections)),
or omit `since` if it has not yet received one. A `next_batch` MUST only be used by the device it
was issued to.

A `since` the server could not have issued MUST be rejected with a 400 and an error code of
`M_INVALID_PARAM`. A `next_batch` the server has issued MUST remain valid for as long as the device
it was issued to exists.

### Extension response

If the extension is enabled, the server MUST include a `to_device` section in the `extensions`
response field whenever it has messages to send. It MAY omit the section when there are none. If
the section is absent, the client sends the same `since` in its next request.

The `ExtensionResult` has the following format:

| Name | Type | Required | Comment |
| - | - | - | - |
| `next_batch` | `string` | Yes | The token to send as `since` in the next request. |
| `events` | `[ToDeviceEvent]` | Yes | The messages for this device, in order of arrival. Empty when there are none. |

A `ToDeviceEvent` has the format of the `Event` in the `to_device` section of
[`/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#extensions-to-sync):

| Name | Type | Required | Comment |
| - | - | - | - |
| `type` | `string` | Yes | The type of the message. |
| `sender` | `string` | Yes | The user ID of the sender. |
| `content` | `object` | Yes | The content of the message. |

For example:

```jsonc
{
    "extensions": {
        "to_device": {
            "next_batch": "1247",
            "events": [
                {
                    "type": "m.room_key_request",
                    "sender": "@alice:example.com",
                    "content": { "...": "..." }
                }
            ]
        }
    }
}
```

### Semantics

The server returns the messages queued for the requesting device after the position `since` names,
up to `limit` of them. If `since` is omitted, the server returns every message it holds for the
device, up to `limit`.

Messages from one sending device MUST be returned in the order that device sent them.

Servers MUST scope both the read and the deletion to the authenticated user and the device the
request was made with.

If more messages are queued than `limit`, the server returns `limit` of them and answers the next
request immediately (see [Long-polling](#long-polling)), so that a client drains its queue without
waiting out long polls.

#### Acknowledgement

The send-to-device module defines acknowledgement for
[`/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync):

> When the client calls `/sync` again with the `next_batch` token from the first response, the server
> should infer that any send-to-device messages in that response have been delivered successfully,
> and delete them from the store.

This extension keeps that mechanism, with its own token in place of the `next_batch` of `/v3/sync`.
Sending a `since` acknowledges every message up to and including the position it names. The server
MUST NOT return an acknowledged message again, and SHOULD delete it: the module exists to carry
signalling data without storing it permanently.

A client MUST NOT send a `since` covering messages it has not durably handled. The server will not
return them again.

`/v3/sync` reads the same queue and acknowledges it up to its own `since`. A client MUST NOT use
`/v3/sync` and this extension concurrently on one device: each would delete messages the other has
not yet returned. Migrating between the two is safe if only one is in flight at a time.

A message is therefore delivered at least once. A client receives a message more than once only
when it repeats a request with the same `since` (a retry), or omits `since` after receiving the
message. The spec change for this MSC amends the send-to-device module's claim that a message is
delivered exactly once to each device.

#### Connections

The token is independent of the connection.

- Enabling the extension partway through a connection, whether for the first time or after
  disabling it, returns every message queued after `since`, including any that arrived while the
  extension was disabled. No messages are lost.
- After a connection is reset with `M_UNKNOWN_POS`, the client sends its last `next_batch` as
  `since` on the new connection.
- A `since` can be used across connections. The queue is per-device, so acknowledging a message on
  one connection deletes it for every connection of that device, including one that has not yet
  received it. A client MUST coordinate the connections that share a queue, for example by enabling
  the extension on only one connection at a time. See [Potential issues](#potential-issues).

#### Long-polling

A message queued for the requesting device after the position `since` names counts as an update for
the purposes of long-polling: the server MUST return immediately while one exists, even if there is
nothing else to send.

## Potential issues

The queue is per-device, so two sync loops for one device (a push notification process and the main
application, for example) can delete each other's messages unless they coordinate, as required
under [Connections](#connections).

The same collision is why a client cannot use `/v3/sync` and this extension at once (see
[Acknowledgement](#acknowledgement)). A client migrating to sliding sync has to stop one before
starting the other.

Clients manage two sync tokens rather than one.

A client that asks for a `limit` above the server's cap cannot tell from the response size whether
it has drained the queue.

This MSC gives a server no way to expire a `since` token while its device exists. The state a server
keeps to honour old tokens is small next to the queued messages themselves.

## Alternatives

The extension could take its position from the connection's `pos` rather than a token of its own.
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) already forbids a server
from treating a response as delivered until it receives a request carrying that response's `pos`,
which is the acknowledgement rule above. The `pos` would then have to encode a position in the
to-device stream, and there would be no second token to manage.

However:

- A client should handle each to-device message once. Messages carry no IDs, so a client cannot
  recognise one it has already handled. Under `pos`, every connection reset (`M_UNKNOWN_POS`, or a
  client starting afresh) would re-deliver the unacknowledged messages, and the client would handle
  them again. A connection reset does not change the separate token (so a message is re-delivered
  only on a retry where the client discarded the earlier response unprocessed).
- A client can persist `since` in the same store as the handled to-device messages, which may be
  separate from, and more durable than, wherever it keeps `pos`.

## Security considerations

The server scopes the read and the deletion to the authenticated user and device (see
[Semantics](#semantics)), so a `since` token names a position in that device's queue and nothing
else. Possession of one grants no access to another device's messages.

## Unstable prefix

The experimental implementations of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (e.g. Synapse, as used by
Element X) have supported this extension with the unprefixed `to_device` key on the
`/_matrix/client/unstable/org.matrix.simplified_msc3575/sync` endpoint.

Until this MSC is accepted, implementations MUST use `org.matrix.msc4538.to_device` as the extension
key on the stable [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) endpoint.
The unprefixed `to_device` key remains in use on the unstable `org.matrix.simplified_msc3575`
endpoint for compatibility with existing implementations.

Per the common extension semantics of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), servers advertise support
for this extension in `unstable_features` of
[`/_matrix/client/versions`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientversions):

- `org.matrix.msc4538` while this MSC is unstable, covering both the `org.matrix.msc4538.to_device`
  key on the stable endpoint and the unprefixed `to_device` key on the unstable endpoint; and
- `org.matrix.msc4538.stable` once the server supports the extension as specified here, under the
  unprefixed `to_device` key on the stable endpoint, until it advertises the spec version containing
  this MSC.

## Dependencies

No dependencies.

## Appendix

### Changelog

Differences from the experimental implementation of simplified sliding sync in Synapse v1.151.0.

1. `limit` must be a positive integer, and is rejected with `M_INVALID_PARAM` otherwise. Synapse
   rejects a non-integer but accepts zero, which returns an empty response and acknowledges
   everything queued.
2. The `to_device` section may be omitted when there are no messages to send. Synapse always
   includes it.
