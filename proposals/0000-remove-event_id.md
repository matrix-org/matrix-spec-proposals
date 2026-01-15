# MSC0000: Remove `event_id` from redacted events

The top-level `event_id` key has no use ever since room
version 3, and there is also no defined behaviour in spec
on how to handle the key if it is present on a v3+ event.
This has led to some implementations outright rejecting
these events, even though they are perfectly valid.

## Proposal

Remove the `event_id` key from redacted events.

## Potential issues

None?

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

The room version for this proposal is `com.nhjkl.msc0000.opt1`,
and it is based on room version 12.

## Dependencies

None.
