# MSC2077 - Rooms V5

This MSC proposes creating a new room version named v5, which will enforce the
signing key `valid_until_ts` timestamps proposed in
[MSC2076](https://github.com/matrix-org/matrix-doc/issues/2076).

## Proposal

The new room version is called "5". The only difference between v5 and v4 is
that v5 rooms enforce the `valid_until_ts` timestamp on signing keys as
proposed in [MSC2076](https://github.com/matrix-org/matrix-doc/issues/2076).

It is not yet proposed that servers change the default room version used when
creating new rooms, and it is not yet proposed that servers recommend upgrading
existing rooms to v5.

## Notes

See also [MSC2002](./2002-rooms-v4.md), which proposed room v4 but also
mentioned that a v5 was anticipated and gave some context for this change.
