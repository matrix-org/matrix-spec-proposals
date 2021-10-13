# MSC3122: Deprecate starting key verifications without requesting first

Currently, the [Key verification
framework](https://matrix.org/docs/spec/client_server/r0.6.1#key-verification-framework)
allows a device to begin a verification via to-device messages by sending an
`m.key.verification.start` event without first sending or receiving an
`m.key.verification.request` message.  (The last sentence of the 5th paragraph
of the Key verification framework in the unstable spec, as of the time of
writing.)  However, doing so does not provide a good user experience, and
allowing this adds unnecessary complexity to implementations.

We propose to deprecate allowing this behaviour.

Note that verifications in DMs do not allow this behaviour.  Currently, Element
Web is the only client known to do this.

## Proposal

The ability to begin a key verification by sending an
`m.key.verification.start` event as a to-device event without a prior
`m.key.verification.request` is deprecated.  New clients should not begin
verifications in this way, but will still need to accept verifications begun in
this way, until it is removed from the spec.

## Potential issues

None.

## Alternatives

We could do nothing and leave it in the spec.  But we should clean up cruft when
possible.

## Security considerations

None.

## Unstable prefix

No unstable prefix is required since we are simply deprecating behaviour.
