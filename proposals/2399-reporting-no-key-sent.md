# Reporting that decryption keys are withheld

When an encrypted message is sent in a room, the megolm key might not be
sent to all devices present in the room. Sometimes this may be inadvertent (for
example, if the sending device is not aware of some devices that have joined),
but some times, this may be purposeful.  For example, the sender may have
blacklisted certain devices or users, or may be choosing to not send the megolm
key to devices that they have not verified yet.

Currently, when this happens, there is no feedback given to the affected
devices; devices that have not received keys do not know why they did not
receive the key, and so cannot inform the user as to whether it is expected
that the message cannot be decrypted.  To address this, this proposal defines a
message that senders can (optionally) send to devices indicating that they
purposely did not send a megolm key.

A similar issue happens with keyshare requests; devices are not informed when
other devices decide not to send back keys, and so do not know whether to
expect to receive a key in response to the request.

## Proposal

Devices that purposely do not send megolm keys to a device may instead send an
`m.room_key.withheld` event as a to-device message to the device to indicate
that it should not expect to receive keys for the message.  This message may
also be sent in reply to a `m.room_key_request`.  The `m.room_key.withheld` event has
the properties:

- `room_id`: Required if `code` is not `m.no_olm`. The ID of the room that the
  session belongs to.
- `algorithm`: Required. The encryption algorithm that the key is for.
- `session_id`: Required if `code` is not `m.no_olm`. The ID of the session.
- `sender_key`: Required.  The unpadded base64-encoded device curve25519 key of the session creator.
- `code`: Required.  A machine-readable code for why the megolm key was not sent.
  Possible values are:
  - `m.blacklisted`: the user/device was blacklisted
  - `m.unverified`: the user/devices is unverified
  - `m.unauthorised`: the user/device is not allowed have the key.  For
    example, this would usually be sent in response to a key request if the
    user was not in the room when the message was sent
  - `m.unavailable`: sent in reply to a key request if the device that the key
    is requested from does not have the requested key
  - `m.no_olm`: an olm session could not be established.  This may happen, for
    example, if the sender was unable to obtain a one-time key from the
    recipient.
- `reason`: A human-readable reason for why the key was not sent.  The
  receiving client should only use this string if it does not understand the
  `code`.

An `m.room_key.withheld` event should only be sent once per session; the
recipient of the event should assume that the event applies to all messages in
that session.  If a sender unblocks a recipient, it may re-use the existing
session for which the recipient was previously informed that it was blocked, in
which case, the recipient of the `m.room_key.withheld` message should assume
that the event applies to all messages in the session prior to the index of the
first key that it has received for that session.

A `code` of `m.no_olm` is used to indicate that the sender is unable to
establish an olm session with the recipient.  When this happens, multiple
sessions will be affected.  In order to avoid filling the recipient's device
mailbox, the sender should only send one `m.room_key.withheld` message with no
`room_id` nor `session_id` set.  If the sender retries and fails to create an
olm session again in the future, it should not send another
`m.room_key.withheld` message with a `code` of `m.no_olm`, unless another olm
session was previously established successfully.  In response to receiving an
`m.room_key.withheld` message with a `code` of `m.no_olm`, the recipient may
start an olm session with the sender and send an `m.dummy` message to notify
the sender of the new olm session.  The recipient may assume that this
`m.room_key.withheld` message applies to all encrypted room messages sent
before it receives the message.

### Interaction with key sharing

If Alice withholds a megolm session from Bob for some messages in a room, and
then later on decides to allow Bob to decrypt later messages, she can send Bob
the megolm session, ratcheted up to the point at which she allows Bob to
decrypt the messages.  If Bob logs into a new device and uses key sharing to
obtain the decryption keys, the new device will be sent the megolm sessions
that have been ratcheted up.  Bob's old device can include the reason that the
session was initially not shared by including a `withheld` property in the
`m.forwarded_room_key` message that is an object with the `code` and `reason`
properties from the `m.room_key.withheld` message.

## Potential issues

This does not handle all possible reasons why a device may not have received
megolm keys.

There is currently no way of indicating that part of a session was withheld in
key backups.

## Security considerations

A user might not want to notify another user of the reason why it was not sent
the keys.  Sending `m.room_key.withheld` is optional.

## Unstable prefix

While in development, clients will send events of type
`org.matrix.room_key.withheld`.
