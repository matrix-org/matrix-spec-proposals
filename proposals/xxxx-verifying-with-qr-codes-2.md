# MSCxxxx: Verifying with QR codes v2

[MSC1544](https://github.com/matrix-org/matrix-doc/pull/1544) defines a way of
verifying using QR codes.  However, some [concerns were
raised](https://github.com/matrix-org/matrix-doc/pull/1544#discussion_r429104321)
with the mechanism proposed, preferring that clients do not display the QR code
until a user has selected to use QR code verification and an
`m.key.verification.start` event has been sent.

This proposal introduces a new set of verification messages that supports this
mode of operation.  By modifying the flow of events, clients may now chose to
automatically display QR codes or not, depending on their own needs or
preferences.

## Proposal

Two new verification method identifiers are introduced: `m.qr_code.show.v2` and
`m.qr_code.scan.v2`.  Clients advertise support for `m.qr_code.show.v2` if they
are able to display a QR code, and clients advertise support for
`m.qr_code.scan.v2` if they are able to scan a QR code.  The QR code format is
the same as the one defined in MSC1544.

If both clients support both `v1` and `v2` versions of QR code verification,
they must use the `v2` method.  In other words, they should behave as if the
`v1` methods were not available.  The `m.qr_code.show.v1` and
`m.qr_code.scan.v1` methods are deprecated.

When Alice and Bob verify, if Alice's client supports showing QR codes and
Bob's client supports scanning QR codes, then Alice's client MAY immediately
show the QR code after the
`m.key.verification.request`/`m.key.verification.ready` handshake, in addition
to allowing her to select a different available verification method.  Bob's
client will allow him to select one of the available verification methods,
including scanning a QR code, but not including showing a QR code, even if his
client can show a QR code and Alice's client can scan a QR code.

If Bob selects verification by scanning a QR code, then his client will send an
`m.key.verification.start` event with `method` set to `m.qr_code.scan.v2`.
When Alice's client receives this event, then it will show the QR code if it
has not already done so.

> Rationale: Clients should not enable the device's camera without interaction
> from the user as doing so could make users feel uneasy and dis-trust the
> client.  Thus Bob's client must wait for Bob to select verifying by scanning
> a QR code, and so we make it the scanner's responsibility to send the
> `m.key.verification.start` event.  If we allow Alice's client to select
> verifying by showing a QR code and then send an `m.key.verification.start`
> event with `method` set to `m.qr_code.show.v2`, Bob's client would still need
> to interact with his device to start the scanning process, and having both
> users interact with their devices is more complicated than having just one
> user interact with their device.

After Bob scans Alice's QR code and verifies that it contains his correct key,
his client will indicate that the code has been successfully scanned and will
send an `m.key.verification.reciprocate` event with the `secret` field set to
the shared secret from the QR code.  Alice's client will check that the
`m.key.verification.reciprocate` event contains the shared secret and, if so,
hides the QR code and displays a message asking Alice to confirm that Bob has
scanned the QR code.  (If the shared secret does not match, it displays an
error message and cancels the verification.)  When Alice confirms that Bob has
scanned the QR code, Alice's client sends an `m.key.verification.done` message.
Bob's client may send an `m.key.verification.done` message any time after it
sends the `m.key.verification.reciprocate` message.

## Potential issues

This increases the complexity of the verification code by adding new methods.
However, if clients are implemented it a way such that verification methods are
extensible, the impact of this additional complexity should be minimal.

## Alternatives

This is an alternative to MSC1543, but allows greater flexibility in the
client's choice of UX.

There are other ways of verifying keys; see, for example, the
Tradeoffs/Alternatives section of MSC1543.

## Security considerations

This is just a rearrangement of some messages and does not introduce any new
security issues.

## Unstable prefix

TODO
