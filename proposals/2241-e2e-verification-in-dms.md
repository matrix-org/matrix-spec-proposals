# Key verification in DMs

Currently, key verification is done using `to_device` messages.  However, since
`to_device` messages are not part of a timeline, there is no user-visible record
of the key verification.

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
  to verify keys
- `msgtype`: `m.key.verification.request`
- `methods`: the verification methods supported by Alice's client

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
  event](https://matrix.org/docs/spec/client_server/r0.5.0#m-key-verification-cancel)

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

## Tradeoffs


## Potential issues


## Security considerations


## Conclusion
