# MSC4081: Eagerly sharing fallback keys with federated servers

*Abstract: This MSC aims to increase the robustness of the Olm session setup protocol over federation.
With this MSC, transient network failures over federation will not cause undecryptable messages due to
failing to claim OTKs.*

In order for clients to establish secure communication channels between devices, they need to "claim" one-time keys
(OTKs) that were previously uploaded by the device they wish to talk to. One-time keys, as the name suggests, must
only be used once. However, this presents several problems:
 - what happens when the device does not upload more keys and the uploaded keys are all used up? (key exhaustion)
 - what happens if the OTK cannot be claimed due to transient network failures.

[MSC2732](https://github.com/matrix-org/matrix-spec-proposals/pull/2732) introduced the concept of "fallback keys"
which can be claimed when OTKs are exhausted. Fallback keys provide weaker security properties than one-time keys,
specifically impacting forward secrecy, which protects past sessions against future compromises of keys or
passwords. The risk is that if the private part of the fallback key is exposed, an attacker may use the key to
decrypt earlier sessions. This can be mitigated by creating a new fallback key as soon as the old one has been used
(and hence later deleting the private key, with some lag time to account for slow networks).

For reference, https://crypto.stackexchange.com/a/52825 is a good explanation of why OTKs are preferable
to fallback keys, where they are available. (The question is about Signal rather than Olm, however the principles
are much the same. Signal uses the terms "prekey" to refer to "fallback key" and "one-time prekey" to refer to
OTK.)

## Proposal

Currently, fallback keys are _only_ used on key exhaustion, not due to transient network failures. This MSC
proposes to change the semantics to allow fallback keys to be returned by the `/keys/claim` endpoint if the server
the target device is on is unreachable. In order for servers to return fallback keys during the network failure,
the fallback keys must be cached _in advance_ on the claiming user's homeserver.

### Extend `/_matrix/client/v3/keys/upload` request

Clients have to opt in to this process when uploading fallback keys. To allow this, we extend the [`POST
/_matrix/client/v3/keys/upload`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3keysupload)
endpoint with a new request body parameter, `eager_share_fallback_keys`, as follows (bold is new):

| Name                  | Type                      | Description                                                                                                                                                                                               |
|-----------------------|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `device_keys`         | `DeviceKeys`              | Identity keys for the device. May be absent if no new identity keys are required.
| `fallback_keys`       | `OneTimeKeys`	            | The public key which should be used if the device’s one-time keys are exhausted, **or if the user's homeserver is unreachable**. [etc]
| `one_time_keys`       | `OneTimeKeys`	            | One-time public keys for “pre-key” messages. The names of the properties should be in the format <algorithm>:<key_id>. The format of the key is determined by the key algorithm. May be absent if no new one-time keys are required.
| **`eager_share_fallback_keys`** | **`boolean`**   | **Whether the `fallback_keys` should immediately be sent to other homeservers which have a user which share a room with this user. Omitting this property is the same as setting it to `false`.**

### Extend `m.device_list_update` EDU

This MSC proposes adding a new key `fallback_keys` to the [`m.device_list_update`
EDU](https://spec.matrix.org/v1.9/server-server-api/#definition-mdevice_list_update). We change the spec wording as
follows:

> Servers must send `m.device_list_update` EDUs to all the servers who share a room with a given local user, and
> must be sent whenever that user’s device list changes (i.e. for new or deleted devices, when that user joins a
> room which contains servers which are not already receiving updates for that user’s device list, or changes in
> device information such as the device’s human-readable name **or, if the client has opted into eager sharing of
> fallback keys, the fallback keys**).

A new property `fallback_keys` is added to the body of the `m.device_list_update` EDU, as shown below (bold is new):

| Name                  | Type                      | Description                                                                                                                                                                                               |
|-----------------------|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `deleted`             | `boolean`	                | True if the server is announcing that this device has been deleted.
| `device_display_name` | `string`	                | The public human-readable name of this device. Will be absent if the device has no name.
| `device_id`           | `string`                  | Required: The ID of the device whose details are changing.
| `keys`                | `DeviceKeys`              | The updated identity keys (if any) for this device. May be absent if the device has no E2E keys defined.
| `prev_id`             | `[integer]`               | The `stream_ids` of any prior `m.device_list_update` EDUs sent for this user which have not been referred to already in an EDU’s `prev_id` field. If the receiving server does not recognise any of the `prev_ids`, it means an EDU has been lost and the server should query a snapshot of the device list via `/user/keys/query` in order to correctly interpret future `m.device_list_update` EDUs. May be missing or empty for the first EDU in a sequence.
| `stream_id`           | `integer`                 | Required: An ID sent by the server for this update, unique for a given `user_id`. Used to identify any gaps in the sequence of m.device_list_update EDUs broadcast by a server.
| `user_id`             | `string`                  | Required: The user ID who owns this device.
| **`fallback_keys`**   | **`{string: KeyObject}`** | **The fallback keys for this device, if set, and if the client has opted in to eager sharing. This is the same as the most recent `fallback_keys` uploaded by this device via [`POST /_matrix/client/v3/keys/upload`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3keysupload).**


An example of an EDU with the new property:
```js
{
  "content": {
    "device_display_name": "Mobile",
    "device_id": "QBUAZIFURK",
    "keys": {
      "algorithms": [
        "m.olm.v1.curve25519-aes-sha2",
        "m.megolm.v1.aes-sha2"
      ],
      "device_id": "JLAFKJWSCS",
      "keys": {
        "curve25519:JLAFKJWSCS": "3C5BFWi2Y8MaVvjM8M22DBmh24PmgR0nPvJOIArzgyI",
        "ed25519:JLAFKJWSCS": "lEuiRJBit0IG6nUf5pUzWTUEsRVVe/HJkoKuEww9ULI"
      },
      "signatures": {
        "@john:example.com": {
          "ed25519:JLAFKJWSCS": "dSO80A01XiigH3uBiDVx/EjzaoycHcjq9lfQX0uWsqxl2giMIiSPR8a4d291W1ihKJL/a+myXS367WT6NAIcBA"
        }
      },
      "user_id": "@john:example.com"
    },
    "prev_id": [
      5
    ],
    "stream_id": 6,
    "user_id": "@john:example.com",
    "fallback_keys": {
        "signed_curve25519:AAAAHg": {
            "fallback": true,
            "key": "zKbLg+NrIjpnagy+pIY6uPL4ZwEG2v+8F9lmgsnlZzs",
            "signatures": {
                "@johh:example.com": {
                    "ed25519:JLAFKJWSCS": "FLWxXqGbwrb8SM3Y795eB6OA8bwBcoMZFXBqnTn58AYWZSqiD45tlBVcDa2L7RwdKXebW/VzDlnfVJ+9jok1Bw"
                }
            }
        }
    }
  },
  "edu_type": "m.device_list_update"
}
```

### Changed semantics for `/keys/claim`

[`POST /_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3keysclaim) can
now respond with a cached fallback key if the remote server is unreachable. "Unreachable" includes:
 - unable to connect to the server
 - the sending server is backing off the remote server
 - the remote server responded with an error code such as 429 Too Many Requests.

### Changed semantics for rotating fallback keys

As a reminder, clients SHOULD upload a new fallback key when they realise it has been "used".

The definition of when a fallback key is "used" is changed by this MSC. Previously, a fallback key is "used"
_if it is claimed by another device_. When this happens, the client is told this via `/sync`, by removing the
algorithm from the `device_unused_fallback_key_types` array. This is no longer a useful mechanism, as the key is
sent eagerly over federation.

Therefore, we change the definition of "used" to be "when the device receives and successfully decrypts an initial
pre-key to-device event which uses that key". As soon as such an event is received, a new fallback key should be
created and uploaded via `/keys/upload`. (As above, this will then trigger `m.device_list_update` EDUs.)

We also add a recommendation that the fallback key is also **rotated periodically** _even if the key isn't "used"_,
e.g once per week. This reduces the risk of the key being used without the client knowing about it (such as a
networking problem). Some clients [already do this](https://github.com/matrix-org/matrix-rust-sdk/pull/3151).

Once a new key has been uploaded, the private part of the old key should be scheduled for deletion. This cannot
happen immediately, since there may be other messages in flight which rely on the old key. This was also true of
the original fallback keys implementation
([MSC2732](https://github.com/matrix-org/matrix-spec-proposals/pull/2732)), however there could now be a much more
significant delay between the old key being used to encrypt a message and that message being received at the
recipient, and MSC2732's recommendation (the lesser of "as soon as the new key is used" and 1 hour) is inadequate
We therefore recommend significantly increasing the period for which an old fallback key is kept on the client, to
30 days after the key was replaced, but making sure that at least one old fallback key is kept at all
times. (Since we recommend rotating keys every week, normally there will be several old keys on the
client. However, if a user does not use their client for a month, there could be a backlog of messages for the most
recent old key; this is why we always keep at least one.)

## Comparisons with X3DH (Signal)

X3DH is very similar to Matrix's key agreement protocol. Due to this similarity, it is worth researching what X3DH
does with respect to OTKs.

> To perform an X3DH key agreement with Bob, Alice contacts the server and fetches a "prekey bundle" containing the following values:
>
>   - Bob's identity key IKB
>   - Bob's signed prekey SPKB
>   - Bob's prekey signature Sig(IKB, Encode(SPKB))
>   - (Optionally) Bob's one-time prekey OPKB

https://signal.org/docs/specifications/x3dh/#sending-the-initial-message


Signal uses the terms "prekey" to refer to "fallback key" and "one-time prekey" to refer to OTK. In X3DH, one-time
keys are optional. If they are exhausted, the protocol simply continues without it. If they are present, an additional
DH operation is performed.

This optionality makes the protocol robust to OTK exhaustion and transient network failures (e.g to a database to
claim OTKs as Signal is not federated).

## Security Considerations

1. Ultra secure clients may be unhappy that fallback keys are being returned and not one-time keys, because they
   dislike the slightly weaker security properties fallback keys provide. Since fallback keys are marked as such
   with `fallback: true`, such clients can detect this situation and act accordingly (eg by refusing to send a
   message, or by retrying later).

2. A malicious actor who can control network conditions (but not the servers themselves) can force a client to use
   a fallback key by temporarily preventing two homeservers from communicating. Previously, the only way such an
   actor could force a client to use a fallback key would be to claim all the OTKs before the client had a chance
   to upload more. Therefore, this MSC increases the ways attackers can force clients to use fallback
   keys. Fallback keys weaken forward secrecy. It is assumed that "most" sessions will be set up using OTKs and not
   the fallback key. If this assumption holds, forcing use of a fallback key does nothing to compromise those
   sessions. This means this attack is only useful for _active attacks_, where an attacker wants to compromise
   _sessions that have yet to be established_, and wants to force those sessions to be set up with the fallback
   key.

3. By sending the fallback key eagerly, an attacker would have access to the public key for a longer period of time
   than before. Without this MSC, the fallback key remains on the uploader's homeserver until a federated user
   requests it.  At that point, the client is notified via `/sync` that the fallback key has been used and hence
   should be rotated.  With this MSC, the client would not be notified when the fallback key is used on the remote
   server, because this MSC is robust to network partitions. Instead, the user will be notified when they receive a
   to-device event encrypted with the fallback key. If having access to the public part of the fallback key _for an
   extended period of time_ is useful for an attacker, then this MSC decreases security.

   We are not aware of any scenario where having access to the public key for a longer period of time is a security
   risk. If there is a risk, other decentralised systems such as bitcoin, etheruem and libp2p which all rely on
   long-lived public keys as addresses would also be vulnerable. Furthermore, the user's own homeserver has access
   to the fallback key today. If access to the key for an extended time is a security risk, and the user does not
   trust their own homeserver (not unreasonable given this is for E2EE) then any concerns _are already present
   today_, just not over federation.

## Alternatives

1. Do nothing. In this scenario, if the remote server is unreachable when the client calls `/keys/claim`, the
   message will not be encrypted for that device, and the end user will be unable to decrypt the message. What's
   worse, this will persist until the client decides to retry the `/keys/claim` endpoint, which could be seconds or
   much longer.  As a data point, Matrix Rust SDK currently uses [15
   seconds](https://github.com/matrix-org/matrix-rust-sdk/issues/2804) and this is seen as very low.

2. Clients could remember that they were unable to claim keys for a given device, and retry periodically. The main
   problem with this approach (other than increased complexity in the client) is that it requires the sending
   client to still be online when the remote server comes online, and to notice that has happened. There may be
   other benefits to such an approach, but we feel that this MSC nevertheless represents an achievable, incremental
   improvement in reliability.
