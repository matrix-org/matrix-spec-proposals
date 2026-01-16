# MSC4403: Forbid `event_id` on PDUs received over federation

The top-level `event_id` key has no use ever since room
version 3, and there is also no defined behaviour in spec
on how to handle the key if it is present on a v3+ PDU.
This has led to some implementations outright rejecting
these PDUs, even though they are perfectly valid.

## Proposal

Forbid `event_id` from appearing on the top-level of PDUs
received over federation. This also removes it from the
protected keys list in the redaction algorithm.

This will require a new room version.

## Potential issues

None?

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

The room version for this proposal is `com.nhjkl.msc4403.opt2`,
and it is based on room version 12.

## Dependencies

None.
