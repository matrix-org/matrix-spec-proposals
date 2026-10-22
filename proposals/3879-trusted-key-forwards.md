# MSC3879: Trusted key forwards

When a device does not have a megolm session, it can [request the session from
another device](https://spec.matrix.org/unstable/client-server-api/#key-requests).
However, when receiving sessions in this way, the device currently does not
know whether the session should be trusted.  As a result, some clients indicate
that the events encrypted with this session cannot be trusted, which causes
confusion for users.

We propose adding a flag to the `m.forwarded_room_key` event to indicate
whether the forwarding device believes the session should be trusted.  If the
recipient then trusts the forwarder, it can use that flag to decide whether or
not to trust the session.

## Proposal

A new property, `trusted`, is added to the `m.forwarded_room_key` event.  The
property is set to `true` if the forwarder believes the session should be
trusted.  If the property is set to `false` or is absent, this indicates that
the session cannot be trusted.

The recipient should trust the session if and only if all of the following is true:

- the `m.forwarded_room_key` event marks the key as trusted,
- the recipient and forwarding devices belong to the same user, and
- the forwarder has been verified (e.g. by verifying the device directly, or
  via cross-signing).

Note that this depends on the forwarder being able to determine whether it
trusts the session.  The forwarder can mark the session as trusted if any of
the following is true:

- it created the session;
- it received the session from the session creator via an `m.room_key` message;
- it was received via an `m.forwarded_room_key` from a trusted device belonging
  to the same user, and it was marked as trusted; or
- it was received from a key backup that can be trusted (such as [Symmetric key
  backup](https://github.com/matrix-org/matrix-spec-proposals/pull/3270)), and
  was marked as trusted in the backup.

## Potential issues

TODO:

## Alternatives

The `forwarding_curve25519_key_chain` property of the `m.forwarded_room_key`
event was intended to help determine whether the key could be trusted.
However, this appears to be insufficient as:

- this does not indicate whether the key was ever obtained from key backup, and
- does not handle the fact that devices listed in the forwarding key chain may
  no longer exist.

Rather than trying to divine whether a key should be trusted based on this
information, the method proposed here seems to be simpler and more robust.

## Security considerations

The security of this proposal depends on the forwarder being able to determine
whether it trusts a session.  If the forwarder incorrectly marks a session as
trusted when it should not in fact be trusted, the recipient, as well as any
other devices that obtain the session from the recipient (whether directly, or
indirectly), will incorrectly trust messages.

## Unstable prefix

Until this proposal is accepted, clients should use
`org.matrix.msc3879.trusted` as the property name.

## Dependencies

This MSC does not build on any other MSCs.  However, the "trusted" concept is
also present in [MSC3270: Symmetric megolm
backup](https://github.com/matrix-org/matrix-spec-proposals/pull/3270).
