# Key verification in DMs

Currently, key verification is done using `to_device` messages.  However, since
`to_device` messages are not part of a timeline, there is no user-visible
record of the key verification.

As well, the current key verification framework does not provide any feedback
when interacting with clients that do not support it; if a client does not
support the key verification framework, there is no way for users to discover
this other than waiting for a while and noticing that nothing is happening.

This proposal will solve both problems.

## Proposal

The current [key verification
framework](https://matrix.org/docs/spec/client_server/r0.5.0#key-verification-framework)
will be replaced by a new framework that uses room messages rather than
`to_device` messages.  Key verification messages will be sent in a [Direct
Messaging](https://matrix.org/docs/spec/client_server/r0.5.0#id185) room.  If
there is no Direct Messaging room between the two users involved, the client
that initiates the key verification will create one.

In this proposal, we use "Alice" to denote the user who initiates the key
verification, and "Bob" to denote the other user involved in the key
verification.

### General framework

#### Requesting a key verification

To request a key verification, Alice will send an `m.room.message` event with the
following properties in its contents:

- `body`: a fallback message to alert users that their client does not support
  the key verification framework, and that they should use a different method
  to verify keys.  For example, "Alice is requesting to verify keys with you.
  However, your client does not support this method, so you will need to use
  the legacy method of key verification."

  Clients that do support the key verification framework should hide the body
  and instead present the user with an interface to accept or reject the key
  verification.

  The event may also contain `format` and `formatted_body` properties as
  described in the [m.room.message
  msgtypes](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-message-msgtypes)
  section of the spec.  Clients that support the key verification should
  similarly hide these from the user.
- `msgtype`: `m.key.verification.request`
- `methods`: the verification methods supported by Alice's client
- `to`: Bob's Matrix ID.  Users should only respond to verification requests if
  they are named in this field.  Users who are not named in this field and who
  did not send this event should ignore all other events that have a
  `m.reference` relationship with this event.
- `from_device`: Alice's device ID.  This is required since some verification
  methods may use the device IDs as part of the verification process.

Key verifications will be identified by the event ID of the key verification
request event.

Clients should ignore verification requests that have been accepted or
cancelled, or if they do not belong to the sending or target users.

The way that clients display this event can depend on which user and device the
client belongs to, and what state the verification is in.  For example:

- If the verification has been completed (there is an `m.key.verification.done`
  or `m.key.verification.cancel` event), the client can indicate that the
  verification was successful or had an error.
- If the verification has been accepted (there is an `m.key.verification.start`
  event) but has not been completed, the two devices involved can indicate that
  the verification is in progress and can use this event as a place in the
  room's timeline to display progress of the key verification and to interact
  with the user as necessary.  Other devices can indicate that the verification
  is in progress on other devices.
- If the verification has not been accepted, clients for the target user can
  indicate that a verification has been requested and allow the user to accept
  the verification on that device.  The sending client can indicate that it is
  waiting for the request to be accepted, and the sending user's other clients
  can indicate the that a request was initiated on a different device.

Clients may choose to display or not to display events of any other type that
reference the original request event; but it must not have any effect on the
verification itself.

#### Accepting a key verification

To accept a key verification, Bob will send an `m.key.verification.ready` event
with the following properties in its contents:

TODO: MSC1849 may use `m.relationship` rather than `m.relates_to`, in which
case this proposal should follow suit.

- `m.relates_to`: an object with the properties:
  - `rel_type`: `m.reference`
  - `event_id`: the event ID of the key verification request that is being
    accepted
- `methods`: an array of verification methods that the device supports
- `from_device`: Bob's device ID.  This is required since some verification
  methods may use the device IDs as part of the verification process.

Clients should ignore `m.key.verification.ready` events that correspond to
verification requests that they did not send.

After this, either Alice or Bob may start the verification by sending an
`m.key.verification.start` event with the following properties in its contents:

- `m.relates_to`: an object with the properties:
  - `rel_type`: `m.reference`
  - `event_id`: the event ID of the key verification request that is being
    started
- `method`: the key verification method that is being used.  This should be a
  method that both Alice's and Bob's devices support.
- `from_device`: The user's device ID.

If both Alice and Bob send an `m.key.verification.start` message, and they both
specify the same verification method, then the event sent by the user whose
user ID is the smallest is used, and the other event is ignored.  If they both
send an `m.key.verification.start` message and the method is different, then
the verification should be cancelled with a `code` of `m.unexpected_message`.

After the `m.key.verification.start` event is sent, the devices may exchange
messages (if any) according to the verification method in use.

#### Rejecting a key verification

To reject a key verification, Alice or Bob will send an
`m.key.verification.cancel` event with the following properties in its
contents:

- `m.relates_to`: an object with the properties:
  - `rel_type`: `m.reference`
  - `event_id`: the event ID of the key verification that is being cancelled
- `body`: A human readable description of the `code`. The client should only
  rely on this string if it does not understand the `code`.
- `code`: The error code for why the process/request was cancelled by the
  user. The contents are the same as the `code` property of the currently
  defined [`m.key.verification.cancel` to-device
  event](https://matrix.org/docs/spec/client_server/r0.5.0#m-key-verification-cancel),
  or as defined for specific key verification methods.

This message may be sent at any point in the key verification process.  Any
subsequent key verification messages relating to the same request are ignored.
However, this does not undo any verifications that have already been done.

#### Concluding a key verification

When the other user's key is verified and no more messages are expected, each
party will send an `m.key.verification.done` event with the following
properties in its contents:

- `m.relates_to`: an object with the properties:
  - `rel_type`: `m.reference`
  - `event_id`: the event ID of the key verification that is being cancelled

This provides a record within the room of the result of the verification.

Any subsequent key verification messages relating to the same request are
ignored.

Although a client may have successfully completed its side of the verification,
it may wait until receiving an `m.key.verification.done` (or
`m.key.verification.cancel`) event from the other device before informing the
user that the verification was successful or unsuccessful.

#### Other events

Key verification methods may define their own event types, or extensions to the
above event types.  All events sent as part of a key verification process
should have an `m.relates_to` property as defined for
`m.key.verification.accept` or `m.key.verification.cancel` events.

Clients should ignore events with an `m.relates_to` that have a `rel_type` of
`m.reference` that refer to a verification where it is neither the requester
nor the accepter.

Clients should not redact or edit verification messages.  A client may ignore
redactions or edits of key verification messages, or may cancel the
verification with a `code` of `m.unexpected_message` when it receives a
redaction or edit.

### SAS verification

The messages used in SAS verification are the same as those currently defined,
except that instead of the `transaction_id` property, an `m.relates_to`
property, as defined above, is used instead.

If the key verification messages are encrypted, the hash commitment sent in the
`m.key.verification.accept` message MUST be based on the decrypted
`m.key.verification.start` message contents, and include the `m.relates_to`
field, even if the decrypted message contents do not include that field.  For
example, if Alice sends a message to start the SAS verification:

```json
{
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "ABCDEFG...",
    "device_id": "Dynabook",
    "sender_key": "alice+sender+key",
    "session_id": "session+id",
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$verification_request_event"
    }
  },
  "event_id": "$event_id",
  "origin_server_ts": 1234567890,
  "sender": "@alice:example.org",
  "type": "m.room.encrypted",
  "room_id": "!room_id:example.org"
}
```

which, when decrypted, yields:

```json
{
  "room_id": "!room_id:example.org",
  "type": "m.key.verification.start",
  "content": {
    "from_device": "Dynabook",
    "hashes": [
      "sha256"
    ],
    "key_agreement_protocols": [
        "curve25519"
    ],
    "message_authentication_codes": [
        "hkdf-hmac-sha256"
    ],
    "method": "m.sas.v1",
    "short_authentication_string": [
        "decimal",
        "emoji"
    ]
  }
}
```

then the hash commitment will be based on the message contents:

```json
{
  "from_device": "Dynabook",
  "hashes": [
    "sha256"
  ],
  "key_agreement_protocols": [
      "curve25519"
  ],
  "message_authentication_codes": [
      "hkdf-hmac-sha256"
  ],
  "method": "m.sas.v1",
  "short_authentication_string": [
      "decimal",
      "emoji"
  ],
  "m.relates_to": {
    "rel_type": "m.reference",
    "event_id": "$verification_request_event"
  }
}
```

## Alternatives

Messages sent by the verification methods, after the initial key verification
request message, could be sent as to-device messages.  The
`m.key.verification.ready`, `m.key.verification.cancel`, and
`m.key.verification.done` messages must be still be sent in the room, as the
`m.key.verification.ready` notifies the sender's other devices that the request
has been acknowledged, and the `m.key.verification.cancel` and
`m.key.verification.done` provide a record of the status of the key
verification.

However, it seems more natural to have all messages sent via the same
mechanism.

## Potential issues

If a user wants to verify their own device, this will require the creation of a
Direct Messaging room with themselves.  Instead, clients may use the current
`to_device` messages for verifying the user's other devices.

Direct Messaging rooms could have end-to-end encryption enabled, and some
clients can be configured to only send decryption keys to verified devices.
Key verification messages should be granted an exception to this (so that
decryption keys are sent to all of the target user's devices), or should be
sent unencrypted, so that unverified devices will be able to be verified.

Users might have multiple Direct Messaging rooms with other users.  In this
case, clients could need to prompt the user to select the room in which they
want to perform the verification, or could select a room.

## Security considerations

Key verification is subject to the room's visibility settings, and may be
visible to other users in the room.  However, key verification does not rely on
secrecy, so this will no affect the security of the key verification.  This may
reveal to others in the room that Alice and Bob know each other, but this is
already revealed by the fact that they share a Direct Messaging room.

This framework allows users to see what key verifications they have performed
in the past.  However, since key verification messages are not secured, this
should not be considered as authoritative.

## Conclusion

By using room messages to perform key verification rather than `to_device`
messages, the user experience of key verification can be improved.
