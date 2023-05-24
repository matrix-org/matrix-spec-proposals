# MSC3904: Room version 10 as a default

Enough time has passed to allow the public federation to upgrade their servers to support room
version 10, though with some caveats (see "potential issues"). This proposal aims to make v10 the
default room version.

## Proposal

The specification adopts v10 as the suggested default room version, making no changes to the stability
of any room versions. As of writing, v9 is currently the suggested room version.

Room version 10 is currently published here: https://spec.matrix.org/v1.4/rooms/v10/

## Potential issues

Servers will be encouraged to update their config/internal defaults to use v10 instead of v9. This
is considered a good problem to have.

Note that servers are not required to honour the default room version due to it being a suggestion
in the specification, however they might fall behind as other servers set their defaults accordingly.

Some server implementations, like Synapse, support configurable default room versions: servers which
have set this flag will not necessarily be affected by this change.

As of writing (2022-10-09) Synapse and Dendrite both have supported Room version 10 since 2022-08-02
when Synapse in 1.64.0 added its support. Dendrite added its support back in 2022-06-01. This leaves
Conduit as the only major implementation to lack v10 support. 

Conduit status for v10 is not implemented as of (2022-10-09) but has been reported that its getting close
by Conduit developer Timo. Ruma has it implemented and the Catalyst Conduit fork has v10 working 
for about as long as Synapse has had its implementation based on the memory of the Author of this MSC.

For completeness, some links:

**Conduit**:

* Tracking issue: N/A
* Library support: https://github.com/ruma/ruma/pull/1213
* Release: v0.5.0
* Testing: N/A
* Update Progress Source: https://gitlab.com/famedly/conduit/-/merge_requests/444/diffs?commit_id=1e1a144dfa98429ef9f02d16045796b73013830d

## Alternatives

None relevant.

## Security considerations

None relevant.

## Unstable prefix

None relevant - servers can already choose a different default room version legally. This MSC
just formalizes v10 as the default.
