# MSC4127: Removal of query string auth

See [MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126) for details on query
string authentication and the prerequisite deprecation.

## Proposal

Query string authentication becomes *removed* from the [Client-Server API](https://spec.matrix.org/v1.10/client-server-api/#using-access-tokens)
and [Identity Service API](https://spec.matrix.org/v1.10/identity-service-api/#authentication).

The prior deprecation required by the [deprecation policy](https://spec.matrix.org/v1.10/#deprecation-policy)
is described by [MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126).

As a process note, it was considered to bundle the deprecation and removal into MSC4126 instead of
having two separate MSCs, breaking the deprecation policy slightly, though this introduces consequences
which are, in the author's opinion, undesirable. Specifically, the spec release changelog for the
deprecation would say "as per MSC4126" and imply the MSC being moved to the [merged](https://spec.matrix.org/proposals/#process)
state, however the second half of the MSC (the feature removal) would not have landed yet. This would
leave the MSC stuck in an awkward `spec-pr-missing` state because half of it had not been written up
or landed yet. To maintain a clearer changelog, ease process considerations, and give clients another
opportunity to object to the removal, the two MSC approach required by the deprecation policy is best.

## Potential issues

See [MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126).

## Alternatives

See [MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126).

More of a process note, during drafting of this proposal the author considered combining the deprecation
and removal into a single MSC, against the advice of the deprecation policy. The aim was to reduce
process burden and more quickly get the security risk removed from the specification, though merging
both operations into a single MSC potentially makes the spec release changelog unclear and leaves the
MSC in an awkward released-but-not-merged state. To avoid figuring out how to navigate the process
states, increasing the process burden rather than decreasing it, the deprecation policy's two MSC
requirement has been followed here. However, there are still other process efficiencies which can
take place - see the "Dependencies" section of this MSC for details.

## Security considerations

See [MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126).

## Unstable prefix

This proposal cannot feasibly have an unstable prefix. Clients are already discouraged from using
query string authentication and should switch to `Authorization` as soon as possible, regardless of
this MSC.

See [MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126) for related details.

## Dependencies

[MSC4126](https://github.com/matrix-org/matrix-spec-proposals/pull/4126) must be *released* in the
specification before this proposal can be merged, though this MSC *may* progress through Final Comment
Period concurrent to MSC4126 if desirable.
