# MSC4324: Fixing MSC4289's power level for tombstones

This MSC modifies [MSC4289 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4289-privilege-creators.md).

*Spec process note*: After an MSC is accepted, some changes may require a further
MSC at the discretion of the Spec Core Team (SCT). This can be done up until a
proposal becomes merged, at which point the regular MSC process applies. When an
MSC modifies another accepted-but-not-merged MSC, that MSC gets its own dedicated
file and changes the target MSC directly in the same changeset.

When MSC4289 was first written, it assigned `m.room.tombstone` events a fixed
power level of `150`, which was not necessarily compatible with how implementations
specify the initial power levels (the spec doesn't define precisely what the
initial values should be). The MSC was then changed to reference `state_default`
as an anchor, requiring `m.room.tombstone` to be initially set to "above `state_default`"
while still citing the historical `150` value. Unfortunately, in some implementations,
`state_default` typically defaults to power level `50` instead of the intended
`100` desired by MSC4289.

This proposal changes the anchor from `state_default` to a calculation which results
in a power level of `100` in most implementations.

## Proposal

When creating rooms using room version 12, instead of setting the power level to
send `m.room.tombstone` events higher than `state_default`, servers MUST set the
level required to send `m.room.tombstone` events higher than all other power levels
in the initial `m.room.power_levels` event. This MAY still be overridden by clients
using `power_level_content_override`, per MSC4289.

For most server implementations, the highest power level they populate will be
`100`, so MSC4289's recommendation to use `150` for `m.room.tombstone` events
still applies to those implementations.

## Potential issues

As clients can and do use `power_level_content_override`, the default power level
may not be entirely useful. However, the spec should also be correct and use a
sane default.

It's also not particularly helpful that the initial power level scale is not
defined in the spec. Relative values are defined ("room creator is given permission
to send state events"), but not actual numbers. This may be a catalyst for higher
usage of `power_level_content_override`, so clients can expect consistency.

## Alternatives

Some alternatives exist, all of which amount to a "pick one" decision:

* We could use the level required to send `m.room.power_levels` as the anchor
  instead of `state_default`, which is typically power level `100`. This has
  the disadvantage where a server implementation which sets this to sub-100
  no longer captures the intent of MSC4289.

* We could use a fixed value, as MSC4289 originally intended, though this has
  the same disadvantage as above: a server which sets other power levels may
  inadvertently grant upgrade permissions to the wrong user group.

Alternatives also exist with a larger scope than this MSC can reasonably tackle,
such as introducing Role- (or Attribute-) Based Access Control (RBAC/ABAC),
specifying the initial power level scale, or generally rethinking power levels.

## Security considerations

This ensures the intent of MSC4289 is captured in the spec regarding the PL150
tier.

## Unstable prefix

N/A - this MSC is a behavioural change that can't be namespaced.

## Dependencies

None.
