# [MSC2334](https://github.com/matrix-org/matrix-doc/pull/2334) - Change default room version to v5

This MSC proposes changing the recommended default room version from v4 to v5.
This implements steps 5 and 6 of the plan from 
[MSC2002](https://github.com/matrix-org/matrix-doc/issues/2002).

Room version 5 enforces the `valid_until_ts` timestamp on signing keys as
proposed in [MSC2076](https://github.com/matrix-org/matrix-doc/issues/2076).

## Proposal

When [MSC2077](https://github.com/matrix-org/matrix-doc/issues/2077) proposed
room version 5, the default version continued to be v4 to allow old servers to
continue to chat in newly created rooms. Server-Server API r0.1.2 (which
contains the details on room version 5) and Synapse 1.0.0 (with support for room
version 5) were both released more than 4 months ago which has given people
plenty of time to update. Room version 5 should be the default room version so
that newly created rooms enforce key-validity periods.

## Potential issues

Servers which do not support room version 5 will not be able to participate in
newly created rooms on other servers. Hopefully this will encourage them to
update their server.

## Security considerations

Room version 5 fixes known security vulnerabilities but that doesn't do much
good if newly created rooms aren't using room version 5 by default.