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
  to verify keys.  The message should contain Bob's Matrix ID in order to
  trigger a notification so that Bob's client will highlight the room for him,
  making it easier for him to find it.  For example, "@bob:example.com: Alice
  is requesting to verify keys with you.  However, your client does not support
  this method, so you will need to use the legacy method of key verification."

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
  `m.key.verification` relationship with this event.

Key verifications will be identified by the event ID of the key verification
request event.

Clients should ignore verification requests that have been accepted or cancelled.

#### Accepting a key verification

To accept a key verification, Bob will send an `m.key.verification.start` event
with the following properties in its contents:

- `m.relates_to`: an object with the properties:
  - `rel_type`: `m.key.verification`
  - `event_id`: the event ID of the key verification request that is being
    accepted
- `method`: the key verification method that is being used

Clients should ignore `m.key.verification.start` events that correspond to
verification requests that it did not send.

Clients may use this event as a place in the room's timeline do display
progress of the key verification process and to interact with the user as
necessary.

#### Rejecting a key verification

To reject a key verification, Bob will send an `m.key.verification.cancel`
event with the following properties in its contents:

- `m.relates_to`: an object with the properties:
  - `rel_type`: `m.key.verification`
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

#### Other events

Key verification methods may define their own event types, or extensions to the
above event types.  All events sent as part of a key verification process
should have an `m.relates_to` property as defined for
`m.key.verification.accept` or `m.key.verification.cancel` events.

Clients should ignore events with an `m.relates_to` that have a `rel_type` of
`m.key.verification` that refer to a verification where it is not the requester
nor the accepter.

### SAS  verification

The messages used in SAS verification are the same as those currently defined,
except that instead of the `transaction_id` property, an `m.relates_to`
property, as defined above, is used instead.

## Potential issues

If a user wants to verify their own device, this will require the creation of a
Direct Messaging room with themselves.

Direct Messaging rooms could have end-to-end encryption enabled, and some
clients can be configured to only send decryption keys to verified devices.
Key verification messages should be granted an exception to this (so that
decryption keys are sent to all of the target user's devices), or should be
sent unencrypted, so that unverified devices will be able to be verified.

Users might have multiple Direct Messaging rooms with other users.  In this
case, clients will need to prompt the user to select the room in which they
want to perform the verification.

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
