# MSC3673 - Encrypting ephemeral data units

## Problem

With the introduction of [MSC2477](https://github.com/matrix-org/matrix-doc/pull/2477)
we now have the ability to send and receive custom, user-defined ephemeral data 
units. This is a great mechanism for transferring short-lived data, applicable in
a variety of situations where persistence is not desired.

Unfortunately E2E encryption for EDUs isn't currently defined and some 
situations, like live user location sharing, come with privacy concerns, moment 
in which that becomes a problem.

## Proposal

This MSC proposes a generic mechanism for end to end encrypted ephemeral data 
units, building on top of [MSC2477](https://github.com/matrix-org/matrix-doc/pull/2477)

We would like to wrap them inside the standard encryption envelope:

```json5
{
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "device_id": "<sender_device_id>",
    "session_id": "<outbound_group_session_id>",
    "ciphertext": "<encrypted_payload_base_64>"
}
```

in which the `ciphertext` will contain the custom EDUs payload and which will be 
sent to `rooms/{roomId}/ephemeral/m.room.encrypted/{txnId}`, similar to 
encrypted timeline events .

The Megolm keys required to decrypt this EDU should be shared over Olm just like
regular encrypted timeline events.

Clients will receive the encrypted payloads in the `/sync`s `ephemeral` 
dictionary where `type` will be equal to `m.room.encrypted` and which can be 
decrypted using the pre-shared Megolm keys.

## Alternatives

We are not aware of any other straightforward solution for sharing sensisitive 
ephemeral data between users.
