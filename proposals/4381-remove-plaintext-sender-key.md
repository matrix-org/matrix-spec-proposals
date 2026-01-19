# MSC4381: Remove plaintext sender key
[MSC3700] deprecated the plaintext `sender_key` and `device_id` fields in events
encrypted with the `m.megolm.v1.aes-sha2` algorithm. For backwards compatibility
reasons, sending the fields is still recommended. The deprecation was merged
over 3 years ago and released as a part of Matrix v1.3.

[MSC3700]: https://github.com/matrix-org/matrix-spec-proposals/pull/3700

## Proposal
This proposal removes the `sender_key` and `device_id` fields in events
encrypted with the `m.megolm.v1.aes-sha2` algorithm. Clients SHOULD NOT include
the fields in new messages anymore.

## Potential issues
Clients that haven't been updated in years may still rely on the deprecated
fields. However, there is a good chance that such clients will also be affected
by the upcoming exclusion of unverified devices.

As mentioned in [MSC3700], this will make debugging encryption issues harder.

## Alternatives
Deprecated fields are meant to be removed eventually, so the only real
alternatives are un-deprecating the fields or switching away from Megolm
entirely.

## Security considerations
There are only benefits in terms of security, as removing the fields will
realize the privacy and security benefits mentioned in [MSC3700].
