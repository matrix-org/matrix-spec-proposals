# Key verification mechanisms

Key verification is an essential part of ensuring that end-to-end encrypted
messages are secure.  Matrix may support multiple verification methods that
require sending events; in fact, two such methods (such as [MSC
1267](https://github.com/matrix-org/matrix-doc/issues/1267) and [MSC
1543](https://github.com/matrix-org/matrix-doc/issues/1543)) have already been
proposed.

This proposal tries to present a common framework for verification methods to
use, and presents a way to request key verification.

## Proposal

Each key verification method is identified by a name.  Verification method
names defined in the Matrix spec will begin with `m.`, and verification method
names that are not defined in the Matrix spec must be namespaced following the
Java package naming convention.

If Alice wants to verify keys with Bob, Alice's device may send `to_device`
events to Bob's devices with the `type` set to `m.key.verification.request`, as
described below.  The `m.key.verification.request` messages should all have the
same `transaction_id`, and are considered to be a single request.  Thus, for
example, if Bob rejects the request on one device, then the entire request
should be considered as rejected across all of his devices.  Similarly, if Bob
accepts the request on one device, that device is now in charge of completing
the key verification, and Bob's other devices no longer need to be involved.

The `m.key.verification.request` event lists the verification methods that
Alice's device supports, and upon receipt of this message, Bob's client should
prompt him to verify keys with Alice using one of the applicable methods.  In
order to avoid displaying stale key verification prompts, if Bob does not
interact with the prompt, it should be automatically hidden 10 minutes after
the message is sent (according to the `timestamp` field), or 2 minutes after
the client receives the message, whichever comes first.  The prompt should also
be hidden if an appropriate `m.key.verification.cancel` message is received.

If Bob chooses to reject the key verification request, Bob's client should send
a `m.key.verification.cancel` message to Alice's device.  This indicates to
Alice that Bob does not wish to verify keys with her.  In this case, Alice's
device should send an `m.key.verification.cancel` message to all of Bob's
devices to notify them that the request has been rejected.

If one of Bob's clients does not understand any of the methods offered, it
should display a message to Bob saying so.  However, it should not send a
`m.key.verification.cancel` message to Alice's device unless Bob chooses to
reject the verification request, as Bob may have another device that is capable
of verifying using one of the given methods.

To initiate a key verification process, Bob's device sends a `to_device` event
to one of Alice's devices with the `type` set to `m.key.verification.start`.
This may either be done in response to an `m.key.verification.request` message,
or can be done independently.  If it is done in response to an
`m.key.verification.request` message, it should use the same `transaction_id`
as the `m.key.verification.request` message.  If Alice's device receives an
`m.key.verification.start` message in response to an
`m.key.verification.request` message, it should send an
`m.key.verification.cancel` message to Bob's other devices that it had
originally sent an `m.key.verification.request` to, in order to cancel the key
verification request.

Verification methods can define other events required to complete the
verification.  Event types for verification methods defined in the Matrix spec
should be in the `m.key.verification` namespace.  Event types that are not
defined in the Matrix spec must be namespaced following the Java package naming
convention.

Alice's or Bob's devices can cancel a key verification process or a key
verification request by sending a `to_device` event with `type` set to
`m.key.verification.cancel`.

### Event Definitions

#### `m.key.verification.request`

Requests a key verification.

Properties:

- `from_device` (string): Required. The device ID of the device requesting
  verification.
- `transaction_id` (string): Required. An identifier for the verification
  request. Must be unique with respect to the pair of devices.
- `methods` ([string]): Required. The verification methods supported by the
  sender.
- `timestamp` (integer): Required. The time when the request was made.  If the
  timestamp is in the future (by more than 5 minutes, to allow for clock skew),
  or more than 10 minutes in the past, then the message must be ignored.

#### `m.key.verification.start`

Begins a key verification process.

Properties:

- `method` (string): Required. The verification method to use.
- `from_device` (string): Required. The device ID of the device starting the
  verification process.
- `transaction_id` (string): Required. An identifier for the verification
  process.  If this message is sent in response to an
  `m.key.verification.request` event, then it must use the same
  `transaction_id` as the one given in the `m.key.verification.request`.
- `next_method` (string): Optional. If the selected verification method only
  verifies one user's key, then this property can be used to indicate the
  method to use to verify the other user's key, which will be started
  immediately after after the current key verification is complete.

Key verification methods can define additional properties to be included.

#### `m.key.verification.cancel`

Cancels a key verification process or a key verification request.  Upon
receiving an `m.key.verification.cancel` message, the receiving device must
cancel the verification or the request.  If it is a verification process that
is cancelled, or a verification request initiated by the recipient of the
cancellation message, the device should inform the user of the reason.

Properties:

- `transaction_id` (string): the identifier for the request or key verification
  to cancel.
- `code` (string): machine-readable reason for cancelling.  Possible reasons
  are:
  - `m.user`: the user cancelled the verification.
  - `m.timeout`: the verification process has timed out.  Different verification
    methods may define their own timeouts.
  - `m.unknown_transaction`: the device does not know about the given transaction
    ID.
  - `m.unknown_method`: the device does not know how to handle the given method.
    This can be sent in response to an `m.key.verification.start` message, or
    can be sent in response to other verification method-specific messages.
  - `m.unexpected_message`: the device received an unexpected message.  For
    example, a message for a verification method may have been received when it
    was not expected.
  - `m.key_mismatch`: the key was not verified.
  - `m.user_mismatch`: the expected user did not match the user verified.
  - `m.invalid_message`: an invalid message was received.
  - `m.accepted`: when an `m.key.verification.request` is accepted by one
    device, an `m.key.verification.cancel` message with `code` set to
    `m.accepted` is sent to the other devices
- `reason` (string): human-readable reason for cancelling.  This should only be
  used if the receiving client does not understand the code given in the `code`
  property.

Verification methods may define their own additional cancellation codes.
Cancellation codes defined in the Matrix spec will begin with `m.`; other
cancellation codes must be namespaced following the Java package naming
convention.

## Tradeoffs

Rather than broadcasting verification requests to Bob's devices, Alice could
simply send an `m.key.verification.start` request to a single device.  However,
this would require Alice to choose the right device to send to, which may be
hard for Alice to do if, for example, Bob has many devices, or if his devices
have similar names.

## Security considerations

An attacker could try to spam a user with verification requests.  Clients
should take care that such requests do not interfere with a user's use of the
client.

## Conclusion

This proposal presents common event definitions for use by key verification
methods and defines a way for users to request key verification.
