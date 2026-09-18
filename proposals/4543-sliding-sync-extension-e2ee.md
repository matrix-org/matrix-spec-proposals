# MSC4543: Sliding Sync Extensions: End-to-end encryption

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync)
only includes core room data and omits other data, such as the end-to-end encryption fields of
`/v3/sync`, from the sync response. Instead, such data is left to "extensions", which clients opt
into individually via the `extensions` field of the sync request.

This MSC defines the extension for the three end-to-end encryption fields that
[`/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#e2e-extensions-to-sync) carries
outside any room: `device_lists`, `device_one_time_keys_count` and
`device_unused_fallback_key_types`. A client uses them to keep its copy of other users' device lists
current and to keep the server supplied with one-time and fallback keys. Without them, a client
using sliding sync cannot tell when a device list is stale or when its keys need replenishing.

Supersedes [MSC3884](https://github.com/matrix-org/matrix-spec-proposals/pull/3884).

## Proposal

A new sliding sync extension is added, with the extension key `e2ee`.

The extension follows the common extension semantics defined by
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508). It is not a per-room
extension, so the common per-room fields (`lists` and `rooms`) do not apply.

### Extension request

The extension takes no fields beyond the common `enabled`:

```jsonc
{
    "extensions": {
        "e2ee": {
            "enabled": true
        }
    }
}
```

### Extension response

If the extension is enabled, the server MUST include an `e2ee` section in the `extensions` response
field:

- in the response to a request without `pos`;
- in the response to the request that enables the extension, whether for the first time on the
  connection or after having been disabled;
- whenever `changed` or `left` would be non-empty; and
- whenever `device_one_time_keys_count` or `device_unused_fallback_key_types` would differ from the
  values in the last `e2ee` section included at or before the request's `pos`.

It MAY omit the section otherwise. An absent section means nothing has changed.

"Enables" and "differ" are judged against the connection's state at the request's `pos`, not
against the last response the server sent.
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) does not let the server
assume the client received a response until it sees a request carrying that response's `pos`. If a
response with new key counts is lost and the client retries with the same `pos`, the retried
response MUST include the section again.

The `ExtensionResult` has the following format:

| Name | Type | Required | Comment |
| - | - | - | - |
| `device_lists` | `DeviceLists` | No | Users whose device lists have changed. Omitted in the response to a request without `pos`. Absent or empty when there are no changes. See [Device lists](#device-lists). |
| `device_one_time_keys_count` | `{string: int}` | Yes | For each key algorithm, the number of unclaimed one-time keys the server holds for this device. See [Key counts](#key-counts). |
| `device_unused_fallback_key_types` | `[string]` | Yes | The key algorithms for which the device has a fallback key that has not been used. |

A `DeviceLists` has the format of the `DeviceLists` in
[`/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#e2e-extensions-to-sync):

| Name | Type | Required | Comment |
| - | - | - | - |
| `changed` | `[string]` | No | Users who have updated their device identity or cross-signing keys, or who now share an encrypted room with the user. Defaults to empty. |
| `left` | `[string]` | No | Users with whom the user no longer shares any encrypted room. Defaults to empty. |

For example:

```jsonc
{
    "extensions": {
        "e2ee": {
            "device_lists": {
                "changed": ["@alice:example.com"],
                "left": ["@bob:example.com"]
            },
            "device_one_time_keys_count": {
                "signed_curve25519": 50
            },
            "device_unused_fallback_key_types": ["signed_curve25519"]
        }
    }
}
```

### Semantics

The fields have the meanings they have in `/v3/sync`. The rest of this section specifies how they
interact with connections.

#### Device lists

The response to a request without `pos` carries no `device_lists`. Otherwise, `changed` and `left`
cover at least the period since the request's `pos`, and an absent `device_lists` in a section means
there were no changes in that period.

A client therefore has no coverage for a period in two cases:

- a request without `pos`, including the first request after `M_UNKNOWN_POS`; and
- a request that enables the extension when the request that produced its `pos` did not, since the
  client is only guaranteed changes since that `pos` and nothing earlier on the connection.

In both cases the client MUST bring its tracked device lists up to date before use. A client SHOULD
persist the `pos` up to which it has applied device list changes, as it would the `next_batch` of
`/v3/sync`, and MAY call
[`/keys/changes`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3keyschanges)
with that `pos` as `from` and the end of the gap as `to`. The end of the gap is the `pos` returned
by the request without `pos` in the first case, and the `pos` the client sent in the enabling
request in the second. If it has no persisted `pos`, or the call fails with `M_UNKNOWN_POS`, it MUST
treat every device list it tracks as outdated and refresh them with
[`/keys/query`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixclientv3keysquery)
before use.

`changed` MAY be a superset of the users whose device lists have actually changed. A server MAY
include earlier changes from the same connection, for example from a period during which the
extension was disabled, and MAY include users it cannot cheaply rule out, for example every member
of a room the user has just joined, as `/v3/sync` permits. Clients MUST NOT rely on earlier changes
being included. The cost of an extra user is one redundant `/keys/query`. `left` MUST be accurate,
since a client stops tracking the users in it.

A `pos` can be used as `from` and `to` in `/keys/changes`, as
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) permits for `/messages` and
`/relations`. A server SHOULD keep a `pos` usable in `/keys/changes` after the connection that
issued it has expired, for longer than it keeps connections alive. A connection may be expired
within hours, but a client may need to catch up after days offline. `/keys/changes` MAY reject a
`pos` it can no longer resolve with a 400 and an error code of `M_UNKNOWN_POS`. The code is new for
this endpoint. Existing clients never pass a `pos`, so they never see it.

#### Key counts

A server MAY omit an algorithm whose count is `0` from `device_one_time_keys_count`. A client MUST
treat an unlisted algorithm as having a count of `0`. An explicit `0` and an unlisted algorithm are
equivalent, including when the server judges whether the field would differ from the last section
included at or before the request's `pos`.

> [!NOTE]
>
> `/v3/sync` lets a server omit an algorithm whose count is zero, and omit the whole field when
> every count is zero. Clients treated an omitted field as no change, so they never learned that
> their supply had run out
> ([matrix-spec-proposals#3298](https://github.com/matrix-org/matrix-spec-proposals/issues/3298)).
> Here the field is required whenever the section is present and replaces the client's state, so an
> unlisted algorithm is unambiguously zero. A count falling to zero is a change, so the section is
> sent, and the algorithm is unlisted or `0` in it.

`device_unused_fallback_key_types` lists the algorithms for which the device has uploaded a fallback
key that no
[`/keys/claim`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixclientv3keysclaim)
response has returned. An empty list means the device has no unused fallback key, whether because
none was uploaded or because it has been used.

Both fields describe current state. A client replaces the values it holds with the values received.

#### Connections

A client MAY enable the extension on more than one connection. Each connection receives
`device_lists` relative to its own `pos`, and the key fields are the same on every connection.
Sending the section on one connection does not change what any other connection receives.

#### Long-polling

A non-empty `changed` or `left` counts as an update for the purposes of long-polling. The server
MUST return immediately, even if there is nothing else to send. A change to
`device_one_time_keys_count` or `device_unused_fallback_key_types` need not. The server MAY return
immediately for it, or report it in the next response returned for another reason. Since the section
MUST be included whenever the key fields have changed, a client learns of the change at the latest
in the response returned when the request's `timeout` expires.

> [!NOTE]
>
> This is mainly an artefact of the Synapse implementation today, which we do not necessarily want
> to rule out as an approach. Synapse tracks the current key counts, but not the stream of updates.
> It therefore cannot tell when there has been a change and so doesn't wake up existing long-polling
> syncs. Instead, it always returns the current count in the response.

## Potential issues

The `changed` list for a connection has no upper bound. A server faced with an impractically large
one MAY expire the connection with `M_UNKNOWN_POS`, as MSC4186 permits. This does not spare the
server the work. The client will ask for the same list via `/keys/changes` from its persisted `pos`,
or, if the server also rejects that `pos`, query every device list it tracks with `/keys/query`.

## Alternatives

Device list changes could carry a token of their own, as the to-device extension
([MSC3885](https://github.com/matrix-org/matrix-spec-proposals/pull/3885)) does. The client would
keep its position across connection resets and never need to catch up, and the server would have to
honour that token for as long as the device exists. This MSC instead has the client keep the `pos`
up to which it has applied changes and catch up with `/keys/changes`. The client still holds a token
across connections, but the server is not obliged to keep it resolvable indefinitely, and the client
has a defined fallback when it cannot.

## Security considerations

The extension exposes the same information as the corresponding `/v3/sync` fields.

## Unstable prefix

The experimental implementations of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (e.g. Synapse, as used by
Element X) have supported this extension with the unprefixed `e2ee` key on the
`/_matrix/client/unstable/org.matrix.simplified_msc3575/sync` endpoint.

Until this MSC is accepted, implementations MUST use `org.matrix.msc4543.e2ee` as the extension key
on the stable [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) endpoint,
`/_matrix/client/v4/sync`. The unprefixed `e2ee` key remains in use on the unstable
`org.matrix.simplified_msc3575` endpoint for compatibility with existing implementations.

Per the common extension semantics of
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), servers advertise support
for this extension in `unstable_features` of
[`/_matrix/client/versions`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientversions)
by setting the following flags to `true`:

- `org.matrix.msc4543` while this MSC is unstable; and
- `org.matrix.msc4543.stable` once this MSC is accepted and the server supports the extension as
  specified here, under the unprefixed `e2ee` key on the stable endpoint, until it advertises the
  spec version containing this MSC.

## Dependencies

This MSC builds on [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) and
[MSC4508](https://github.com/matrix-org/matrix-spec-proposals/pull/4508), both of which have been
accepted.

## Appendix

### Changelog

Differences from the experimental implementations of simplified sliding sync in Synapse v1.151.0
and matrix-rust-sdk 0.19.0.

1. The `e2ee` section may be omitted when nothing has changed. Synapse always includes it, which
   remains permitted.
2. `/keys/changes` accepts a `pos` as a sync token and may return `M_UNKNOWN_POS`. Synapse's
   `StreamToken` parser does not accept the sliding sync token form, so the endpoint rejects a
   `pos`.
3. An algorithm unlisted in `device_one_time_keys_count` means a count of zero. matrix-rust-sdk
   treats it as unchanged.
