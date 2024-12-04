# MSC4147: Including device keys with Olm-encrypted to-device messages

Summary: a proposal to ensure that messages sent from a short-lived (but
genuine) device can be securely distinguished from those sent from a spoofed
device.

## Background

When a Matrix client receives an encrypted message, it is necessary to
establish whether that message was sent from a device genuinely belonging to
the apparent sender, or from a spoofed device (for example, a device created by
an attacker with access to the sender's account such as a malicious server
admin, or a man-in-the-middle).

In short, this is done by requiring a signature on the sending device's device
keys from the sending user's [self-signing cross-signing
key](https://spec.matrix.org/v1.12/client-server-api/#cross-signing). Such a
signature proves that the sending device was genuine.

Current client implementations check for such a signature by
[querying](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysquery)
the sender's device keys when an encrypted message is received.

However, this does not work if the sending device logged out in the time
between sending the message and it being received. This is particularly likely
if the recipient is offline for a long time. In such a case, the sending server
will have forgotten the sending device (and any cross-signing signatures) by
the time the recipient queries for it. This makes the received message
indistinguishable from one sent from a spoofed device.

Current implementations work around this by displaying a warning such as "sent
by a deleted or unknown device" against the received message, but such
messaging is unsatisfactory: a message should be either trusted or not.

We propose to solve this by including a copy of the device keys in the
Olm-encrypted message, along with the cross-signing signatures, so that the
recipient does not have to try to query the sender's keys.

## Proposal

The plaintext payload of to-device messages encrypted with the [`m.olm.v1.curve25519-aes-sha2` encryption
algorithm](https://spec.matrix.org/v1.12/client-server-api/#molmv1curve25519-aes-sha2)
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

We propose to add a new property: `sender_device_keys`, which is a copy of what
the server would return in response to a
[`/keys/query`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3keysquery)
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
  "sender_device_keys": {
    "algorithms": ["<supported>", "<algorithms>"],
    "user_id": "<user_id>",
    "device_id": "<device_id>",
    "keys": {
      "ed25519:<device_id>": "<sender_ed25519_key>",
      "curve25519:<device_id>": "<sender_curve25519_key>"
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
payload must be the same as the `sender_device_keys`.`keys`.`ed25519:<DEVICEID>`
property.  If they differ, the recipient should discard the event.

As the `keys` property is now redundant, it may be removed in a future version
of the Matrix specification.

## Potential issues

Adding this property will increase the size of the to-device message.  We found it
increased the length of a typical encrypted `m.room_key` message from about 1400 to 2400
bytes (a 70% increase). This will require increased storage on the recipient
homeserver, and increase bandwidth for both senders and recipients. See
[Alternatives](#alternatives) for discussion of mitigation strategies.

This proposal is not a complete solution. In particular, if the sender resets
their cross-signing keys, and also logs out the sending device, the recipient
still has no way to verify the sending device. The device signature in the Olm
message is meaningless. A full solution would require the recipient to be able
to obtain a history of cross-signing key changes, and to expose that
information to the user; that is left for the future.

## Alternatives

### Minor variations

The `sender_device_keys` property could be added to the cleartext.  That is, it could
be added as a property to the `m.room.encrypted` event.  This information is
already public, as it is accessible from `/keys/query` (while the device is
logged in), and does not need to be authenticated as it is protected by the
self-signing signature, so it does not seem to need to be encrypted. However,
there seems to be little reason not to encrypt the information. In addition, by
including it in the encrypted payload, it leaves open the possibility of
it replacing the `keys` property, which must be part of the encrypted payload
to prevent an [unknown key-share attack](https://github.com/element-hq/element-web/issues/2215).

The `sender_device_keys` property could be added to the cleartext by the sender's
homeserver, rather than by the sending client. Possibly within an `unsigned`
property, as that is where properties added by homeservers are customarily
added.  It is not clear what advantage there would be to having this
information being added by the client.

To mitigate the increased size of to-device events under this proposal, the
`sender_device_keys` could be sent only in pre-key messages (Olm messages
with `type: 0` in the `m.room.encrypted` event) — with the rationale that if
the Olm message is a normal (non-pre-key) message, this means that the
recipient has already decrypted a pre-key message that contains the
information, and so does not need to be re-sent the information), or if the
signatures change (for example, if the sender resets their cross-signing keys),
or if the sender has not yet sent their `device_keys`.  However, this requires
additional bookkeeping, and it is not clear whether this extra complexity is
worth the reduction in bandwidth.

### Alternative approach

A more radical proposal to decrease the overhead in to-device messages is to
instead specify that `/keys/query` must include deleted devices as well as
active ones, so that they can be reliably queried. Since the origin server
might be unreachable at the time the recipient receives the message, such
device lists would need to be cached on the recipient homeserver.

In other words, this approach would require all homeservers to keep a permanent
record of all devices observed anywhere in the federation, at least for as long
as there are undelivered to-device events from such devices.

Transparently: we have not significantly explored this approach. We have a
working solution, and it is unclear that the advantages of this alternative
approach outweigh the opportunity cost and delay in rollout of an important
security feature. If, in future, the overhead of including the device keys
in the to-device messages is found to be significant, it would be worth
revisiting this.

## Security considerations

If a device is logged out, there is no indication why it was logged out.  For
example, an attacker could steal a device and use it send a message.  The user,
upon realizing that the device has been stolen, could log out the device, but
the message may still be sent, if the user does not notice the message and
redact it.

## Unstable prefix

Until this MSC is accepted, the new property should be named
`org.matrix.msc4147.device_keys`.

## Dependencies

None
