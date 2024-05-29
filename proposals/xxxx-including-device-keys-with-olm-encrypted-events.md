# MSCxxxx: Including device keys with Olm-encrypted events

When a Megolm session is sent from one device to another via Olm, the recipient
can
[query](https://spec.matrix.org/unstable/client-server-api/#post_matrixclientv3keysquery)
the sender's device keys and check whether the device has been cross-signed in
order to determine whether the sending device can be trusted.  However, this
does not work if the sending device has since logged out as the recipient will
not be able to query the sender's device keys.  For example, this can happen if
the recipient is offline for a long time.

One way to solve this is to include a copy of the device keys in the
Olm-encrypted message, along with the cross-signing signatures, so that the
recipient does not have to try to query the sender's keys.

## Proposal

The plaintext payload of the [`m.olm.v1.curve25519-aes-sha2` encryption
algorithm](https://spec.matrix.org/unstable/client-server-api/#molmv1curve25519-aes-sha2)
is currently of the form:

```json
{
  "type": "<type of the plaintext event>",
  "content": "<content for the plaintext event>",
  "sender": "<sender_user_id>",
  "recipient": "<recipient_user_id>",
  "recipient_keys": {
    "ed25519": "<our_ed25519_key>"
  },
  "keys": {
    "ed25519": "<sender_ed25519_key>"
  }
}
```

We propose to add a new property: `device_keys`, which is a copy of what the
server would return in response to a
[`/keys/query`](https://spec.matrix.org/unstable/client-server-api/#post_matrixclientv3keysquery)
request, as the device keys for the sender's device.  In other words, the
plaintext payload will now look something like:

```json
{
  "type": "<type of the plaintext event>",
  "content": "<content for the plaintext event>",
  "sender": "<sender_user_id>",
  "recipient": "<recipient_user_id>",
  "recipient_keys": {
    "ed25519": "<our_ed25519_key>"
  },
  "keys": {
    "ed25519": "<sender_ed25519_key>"
  },
  "device_keys": {
    "algorithms": ["<supported>", "<algoriithms>"],
    "user_id": "<user_id>",
    "device_id": "<device_id>",
    "keys": {
      "ed25519:<device_id>": "<our_ed25519_key>",
      "curve25519:<device_id>": "<our_curve25519_key>"
    },
    "signatures": {
      "<user_id>": {
        "ed25519:<device_id>": "<device_signature>",
        "ed25519:<ssk_id>": "<ssk_signature>",
      }
    }
  }
}
```

If this property is present, the `keys`.`ed25519` property of the plaintext
payload must be the same as the `device_keys`.`keys`.`ed25519:<DEVICEID>`
property.

As the `keys` property is now redundant, it may be removed in a future version
of Olm.

## Potential issues

Adding this property will increase the size of the event.  This could be
mitigated by only sending the `device_keys` in pre-key messages (Olm messages
with `type: 0` in the `m.room.encrypted` event -- with the rationale that if
the Olm message is a normal (non-pre-key) message, this means that the
recipient has already decrypted a pre-key message that contains the
information, and so does not need to be re-sent the information), or if the
signatures change (for example, if the sender resets their cross-signing keys),
or if the sender has not yet sent their `device_keys`.  However, this requires
additional bookkeeping, and it is not clear whether this extra complexity is
worth the reduction in bandwidth.

If the sender resets their cross-signing keys, then the self-signing signature
in the `device_keys` is meaningless.  The recipient will need to re-query the
device keys, and will need to treat the sender as untrusted if it fails to do
so.  The sender could include the self-signing key, signed by the
master-signing key, in the plaintext event, so that if the user only resets
their self-signing key but retains their masster-signing key, the recipient can
still check the sender's device keys.  However, this will further increase the
size of the event, and it is not common for clients to reset the self-signing
key without also resetting the master-signing key, so this is unlikely to give
much benefit.

## Alternatives

The `device_keys` property could be added to the cleartext.  That is, it could
be added as a property to the `m.room.encrypted` event.  This information is
already public, as it is accessible from `/keys/query` (while the device is
logged in), and does not need to be authenticated as it is protected by .the
self-signing signature, so it does not seem to need to be encrypted.  However,
there seems to be little reason not to encrypt the information.

The `device_keys` property could be added to the cleartext by the sender's
homeserver, rather than by the sending client.  Possibly within an `unsigned`
property, as that is where properties added by homeservers are customarily
added.  It is not clear what advantage there would be to having this
information being added by the client.

## Security considerations

If a device is logged out, there is no indication why it was logged out.  For
example, an attacker could steal a device and use it send a message.  The user,
upon realizing that the device has been stolen, could log out the device, but
the message may still be sent, if the user does not notice the message and
redact it.  Thus the recipient device should still indicate that the message
came from a deleted device.

## Unstable prefix

Until this MSC is accepted, the new property should be named
`org.matrix.mscxxxx.device_keys`.

## Dependencies

None
