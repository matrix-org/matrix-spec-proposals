# MSC4081: Claim fallback key on network failures

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
specifically impacting forward secrecy, which protects past sessions against future compromises of keys or passwords.
The risk is that if the private part of the fallback key is exposed, an attacker may use the key to decrypt earlier
sessions. This can be mitigated by cycling the fallback key (and hence deleting the private key) once it has been
"used", with some lag time to account for slow networks.

## Proposal

Currently, fallback keys are _only_ claimed on key exhaustion, not due to transient network failures. This MSC
proposes to change the semantics to allow fallback keys to be returned by the `/keys/claim` endpoint if the server
the target device is on is unreachable. In order for servers to return fallback keys during the network failure,
the fallback keys must be cached _in advance_ on the claiming user's homeserver. This MSC proposes adding a new
key `fallback_keys` to the `m.device_list_update` EDU. This MSC proposes changing the spec wording (bold is new):

> Servers must send `m.device_list_update` EDUs to all the servers who share a room with a given local user, and
> must be sent whenever that user’s device list changes (i.e. for new or deleted devices, when that user joins a
> room which contains servers which are not already receiving updates for that user’s device list, or changes in
> device information such as the device’s human-readable name **or fallback key**).

The following key/values are added to the `DeviceKeys` object definition (bold is new):

| Name             | Type                    | Description                                                                                                                                                                                               |
|------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| algorithms       | [string]                | Required: The encryption algorithms supported by this device.                                                                                                                                             |
| device_id        | string                  | Required: The ID of the device these keys belong to. Must match the device ID used when logging in.                                                                                                       |
| keys             | {string: string}        | Required:  Public identity keys. The names of the properties should be in the format  <algorithm>:<device_id>. The keys themselves should be encoded as specified by the key algorithm.                   |
| signatures       | Signatures              | Required:  Signatures for the device key object. A map from user ID, to a map from  <algorithm>:<device_id> to the signature.   The signature is calculated using the process described at  Signing JSON. |
| user_id          | string                  | Required: The ID of the user the device belongs to. Must match the user ID used when logging in.                                                                                                          |
| **fallback_key** | **{string: KeyObject}** | **The fallback key for this device, if set. The format of this object is identical to the /keys/claim response for a single device. This replaces any previously sent fallback key.**                                                                         |

An example of the new field:
```js
{
    // ...
    "fallback_key": {
        "signed_curve25519:AAAAHg": {
            "key": "zKbLg+NrIjpnagy+pIY6uPL4ZwEG2v+8F9lmgsnlZzs",
            "signatures": {
                "@alice:example.com": {
                    "ed25519:JLAFKJWSCS": "FLWxXqGbwrb8SM3Y795eB6OA8bwBcoMZFXBqnTn58AYWZSqiD45tlBVcDa2L7RwdKXebW/VzDlnfVJ+9jok1Bw"
                }
            }
        }
    }
}
```

As a reminder, clients SHOULD rotate their fallback key when they realise it has been "used", with some lag time
to account for federation. As per MSC2732, 1 hour is recommended. When clients change their fallback key, a new
`m.device_list_update` EDU MUST be sent.

The definition of when a fallback key is "used" also needs to change. Previously, a key is "used"
_if it is claimed by another device_. When this happens, the client is told this via `/sync`, either by reducing
the one-time key count by 1, or by removing the algorithm from the `device_unused_fallback_key_types` array. This proposal
makes it impossible to know if the fallback key has been claimed by another device, as it is sent eagerly over
federation. Therefore, this changes the definition of "used" to be "when the device receives and successfully
decrypts an initial pre-key to-device event which uses that key". As per the specification, this is identified as
`type: 0` messages. This will require client-side changes to change when new fallback keys get uploaded.

Due to this change, it is recommended that the fallback key is also **cycled periodically**
_even if the key isn't "used"_, e.g once per week. This reduces the risk of >1 session being established with the same
key, but for some reason the client isn't able to detect it.

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

Ultra secure clients may be unhappy that fallback keys are being returned and not one-time keys, because they
dislike the slightly weaker security properties fallback keys provide. This could be resolved by adding a flag to
the `/keys/claim` endpoint to state whether returning a fallback key is acceptable to the client or not. If this
flag is not set/missing, fallback keys would not be returned in place of OTKs, meaning this MSC would be entirely
opt-in, and hence require client-side changes. However, a malicious server can trivially ignore this flag and
return the fallback key anyway, and the client would not be able to detect this. For this reason, it feels like
security theater to add this flag.

A malicious actor who can control network conditions can force a client to use a fallback key by temporarily
preventing two homeservers from communicating. Previously, the only way a malicious actor could force a client to
use a fallback key would be to claim all the OTKs before the client had a chance to upload more. Therefore, this
MSC increases the ways attackers can force clients to use fallback keys. Fallback keys weaken forward secrecy. It
is assumed that "most" sessions will be set up using OTKs and not the fallback key. If this assumption holds,
forcing use of a fallback key does nothing to compromise those sessions. This means this attack is only useful for
_active attacks_, where an attacker wants to compromise _sessions that have yet to be established_, and wants to
force those sessions to be set up with the fallback key.

By sending the fallback key eagerly, an attacker would have access to the public key for a longer period of time than
before. Without this MSC, the fallback key remains on the uploader's homeserver until a federated user requests it.
At that point, the client is notified via `/sync` that the fallback key has been used and hence should be rotated.
With this MSC, the client would not be notified when the fallback key is used on the remote server, because this MSC
is robust to network partitions. Instead, the user will be notified when they receive a to-device event encrypted with
the fallback key. If having access to the public part of the fallback key
_for an extended period of time_ is useful for an attacker, then this MSC decreases security. The author is not aware
of any scenario where having access to the public key for a longer period of time is a security risk. If there is a
risk, other decentralised systems such as bitcoin, etheruem and libp2p which all rely on long-lived public keys as
addresses would also be vulnerable. Furthermore, the user's own homeserver has access to the fallback key today. If
access to the key for an extended time is a security risk, and the user does not trust their own homeserver (not
unreasonable given this is for E2EE) then any concerns _are already present today_, just not over federation.

## Alternatives

Do nothing. In this scenario, if the remote server is unreachable when the client calls `/keys/claim`, the message
will not be encrypted for that device, and the end user will be unable to decrypt the message. What's worse, this
will persist until the client decides to retry the `/keys/claim` endpoint, which could be seconds or much longer.
As a data point, Matrix Rust SDK currently uses [15 seconds](https://github.com/matrix-org/matrix-rust-sdk/issues/2804)
and this is seen as very low.


