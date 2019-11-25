# Key verification flow addition: `m.key.verification.accept`

The current key verification framework is asymmetrical in that the user who
requests the verification is unable to select the key verification method.
This makes it harder for more experienced users who wish to guide less
experienced users through the verification process, especially if they are not
verifying in-person, but are using a trusted but remote channel of verification
(such as telephone or video conference).

## Proposal

A new event type is added to the key verification framework:
`m.key.verification.accept`, which may be sent by the target of the
`m.key.verification.request` message, upon receipt of the
`m.key.verification.request` event.  It has the fields:

- `from_device`: the ID of the device that sent the `m.key.verification.accept`
  message
- `methods`: an array of verification methods that the device supports

It also has the usual `transaction_id` or `m.relates_to` fields for key
verification events, depending on whether it is sent as a to-device event
or an in-room event.

After the `m.key.verification.accept` event is sent, either party can send an
`m.key.verification.start` event to begin the verification.  If both parties
send an `m.key.verification.start` event, and they both specify the same
verification method, then the event sent by the user whose ID is the smallest
is used, and the event sent by the user whose ID is the largest is ignored.  In
the case of a single user verifying two of their devices, the device ID is
compared instead.  If both parties send an `m.key.verification.start` event,
but they specify different verification methods, the verification should be
cancelled with a `code` of `m.unexpected_message`.

The `m.key.verification.accept` event is optional; the recipient of the
`m.key.verification.request` event may respond directly with a
`m.key.verification.start` event instead.  This is for compatibility with the
current version of the spec.

## Potential issues

There are now three possible ways that a key verification can be performed:

1. A device begins a verification by sending an `m.key.verification.start`
   event.  This is only possible for to-device verification.
2. A device sends an `m.key.verification.request` event and the recipient
   replies with an `m.key.verification.start` event.
3. A device sends an `m.key.verification.request` event and the recipient
   replies with an `m.key.verification.accept` event, and which point, either
   device can send an `m.key.verification.start` event to begin the
   verification.

This increases the complexity of implementations.
