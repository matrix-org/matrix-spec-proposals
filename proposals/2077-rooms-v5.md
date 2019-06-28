# MSC2077 - Room version 5

This MSC proposes creating room version 5, which will enforce the signing key
`valid_until_ts` timestamps proposed in
[MSC2076](https://github.com/matrix-org/matrix-doc/issues/2076).

## Proposal

The new room version is called `5`. The only difference between v5 and v4 is
that v5 rooms enforce the `valid_until_ts` timestamp on signing keys as
proposed in [MSC2076](https://github.com/matrix-org/matrix-doc/issues/2076).

It is not yet proposed to change the default room version to v5. Version 5 will
be considered a "stable" version.

## Notes

See also [MSC2002](./2002-rooms-v4.md), which proposed room v4 but also
mentioned that a v5 was anticipated and gave some context for this change.
