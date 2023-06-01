# MSC3700: Deprecate plaintext sender_key

This MSC proposes to deprecate superfluous fields from the plaintext event
content of encrypted events, increasing privacy and enhancing security.

An encrypted message that uses an algorithm of
[`m.megolm.v1.aes-sha2`](https://spec.matrix.org/v1.2/client-server-api/#mmegolmv1aes-sha2)
(such as an `m.room.encrypted` event) contains the following plain text keys in
its contents: `algorithm`, `session_id`, `sender_key` and `device_id`. Both the
`algorithm` and `session_id` are required for clients to be able to decrypt the
ciphertext: the algorithm explains how to decrypt and the session ID says which
session to use to decrypt the ciphertext.

The `sender_key` and `device_id` are currently used by clients to store and
lookup sessions in addition to the `session_id`, however the `session_id` is
globally unique and so no disambiguation using `sender_key` or `device_id` is
needed.

Session IDs are encoded ed25519 public keys. In particular, the session ID is
the public part of the key used to sign the session when it is shared.

## Proposal

The `sender_key` and `device_id` in `m.megolm.v1.aes-sha2` message contents are
deprecated. Clients must ignore those fields when processing events, but should
still include the fields when generating events to maintain backwards
compatibility. At a future time the fields will stop being included.

Similarly, the `sender_key` field in `m.room_key_request` to-device messages is
deprecated. Clients must ignore the field when processing the request, but
should still include it when generating *if* there is a `sender_key` field in
the event we're requesting keys for.

Clients must not store or lookup sessions using the sender key or device ID.

Client must continue to ensure that the event's sender and room ID fields match
those of the looked up session, e.g. by storing and looking up session using the
room ID and sender as well as the session ID.

When updating an existing session key, clients must ensure:
1. that the updated session data comes from a trusted source, e.g. either the
   session data has a) a valid signature, or b) comes from the user’s session
   key backup; and
2. that the new session key has a lower message index than the existing session
   key.

When clients receive an encrypted event with an unknown session they will need
to send a key request to all clients, rather than the device specified by
`sender_key` and `device_id`. This is the current behaviour used by Element
clients.

### Benefits

There are two main benefits of removing the `sender_key` and `device_id`:
enhanced privacy and better security.

Including these extra fields leaks which device was used to send the message,
and so removing them has an obvious privacy benefit.

On the security side, these fields are untrusted as: a malicious server (or
other man-in-the-middle (MITM) attacker) can change these values; and other
devices/users can simply lie about these values.

Currently, clients therefore need to take care to only use these values to look
up the session. If the client needs to know the associated `sender_key` they
must use the identity key of the Olm session that was used to send them the
Megolm session data, and not the `sender_key` in the event contents.

This is an obvious footgun, and therefore removing/ignoring these untrusted
fields reduces the risk of security bugs being introduced.

## Potential issues
Removing the `sender_key` and `device_id` means that clients don’t know which
remote device to ask for the session key if they don’t already have it. Instead,
clients will need to send a key request to all devices of the event sender. This
will also reduce the information available when debugging encryption issues.
