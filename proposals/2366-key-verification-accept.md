# Key verification flow additions: `m.key.verification.ready` and `m.key.verification.done`

The current key verification framework is asymmetrical in that the user who
requests the verification is unable to select the key verification method.
This makes it harder for more experienced users who wish to guide less
experienced users through the verification process, especially if they are not
verifying in-person, but are using a trusted but remote channel of verification
(such as telephone or video conference).

As an example, let us say that Alice is an experienced Matrix user and is
introducing Bob to the wonders of federated communications.  Alice wants to
verify keys with Bob, so she clicks on the "Verify" button in her client on
Bob's profile (which sends a `m.key.verification.request` message to Bob).
Bob's device receives the verification request and prompts Bob to accept the
verification request.  At this point, under the current framework, Bob is
responsible for choosing the verification method to use.  However, with this
proposal, Bob would be able to just accept the verification request without
choosing a method, and allow Alice to choose the verification method.

In addition, the current key verification framework does not have a method for
clients to signal to the other side that a key verification was successful.
Some clients may wish to wait until the other side has either confirmed a
successful verification or indicated an error before displaying the result of
the verification, in order to give the two users a consistent view of the
verification as a whole.

## Proposal

Two new event types are added to the key verification framework.  The new event
types are already described in [MSC2241 (Key verification in
DMs)](https://github.com/matrix-org/matrix-doc/pull/2241).  This proposal adds
them to verifications in to-device messages.

The first event type is `m.key.verification.ready`, which must be sent by the
target of the `m.key.verification.request` message, upon receipt of the
`m.key.verification.request` event.  It has the fields:

- `from_device`: the ID of the device that sent the `m.key.verification.ready`
  message
- `methods`: an array of verification methods that the device supports

It also has the usual `transaction_id` or `m.relates_to` fields for key
verification events, depending on whether it is sent as a to-device event
or an in-room event.

After the `m.key.verification.ready` event is sent, either party can send an
`m.key.verification.start` event to begin the verification.  If both parties
send an `m.key.verification.start` event, and they both specify the same
verification method, then the event sent by the user whose user ID is the
lexicographically smallest is used, and the other `m.key.verification.start` event is ignored.
In the case of a single user verifying two of their devices, the device ID is
compared instead.  If both parties send an `m.key.verification.start` event,
but they specify different verification methods, the verification should be
cancelled with a `code` of `m.unexpected_message`.

With to-device messages, previously the sender of the
`m.key.verification.request` message would send an `m.key.verification.cancel`
message to the recipient's other devices when it received an
`m.key.verification.start` event. With this new event, the sender of the
`m.key.verification.request` message should send an `m.key.verification.cancel`
message when it receives an `m.key.verification.ready` or
`m.key.verification.start` message, whichever comes first.

The `m.key.verification.ready` event is required for verifications in both DMs
and in to-device messages to accept verifications requested using an
`m.key.verification.request` event.

The second event type is `m.key.verification.done`, which has no fields other
than the usual `transaction_id` or `m.relates_to` field.  This indicates that
the device has successfully completed its side of the verification.

## Potential issues

Clients that follow the Client-Server 0.6.0 spec may not expect an
`m.key.verification.ready` message in response to `m.key.verification.request`.
However to our knowledge, no clients implement `m.key.verification.request` in
this way yet.
