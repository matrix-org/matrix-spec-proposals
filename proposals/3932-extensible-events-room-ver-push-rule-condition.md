# MSC3932: Extensible events room version push rule feature flag

As defined by [MSC3931](https://github.com/matrix-org/matrix-spec-proposals/pull/3931), push rules
can be disabled or enabled based on what the room version itself supports feature-wise. This MSC
introduces a feature flag for [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767),
making it possible to restrict extensible events to an appropriate room version through notifications.

A theory with this approach is that if push rules (and therefore notifications) are denied for extensible
events, they are even less likely to be sent in inappropriate room versions.

## Proposal

For room versions supporting extensible events, they declare support for an `m.extensible_events`
feature flag.

Push rules which don't specify a `room_version_supports` condition are assumed to *not* support
extensible events and are therefore expected to be treated as disabled when a room version *does*
support extensible events. This is to ensure that legacy rules do not trigger in new room versions,
similar to how this MSC aims to only enable certain push rules in applicable room versions.

The above rule does *not* apply to the following push rule IDs:
* `.m.rule.master`
* `.m.rule.roomnotif`
* `.m.rule.contains_user_name`

Note that this MSC intentionally considers the lack of the condition rather than the lack of feature
flag check on the push rule: this is intentional as the timeline for extensible events appears to
show that this "push rules feature flags" system will land at the same time as extensible events,
causing all future MSCs to consider extensible events too.

Any room version which supports MSC1767's described room version is required to list this new feature
flag.

## Potential issues

There is complexity in understanding how to apply the feature flag's condition to existing push rules,
however through implementation effort it will become clearer.

## Alternatives

None discovered.

## Security considerations

No new considerations apply.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3932.*` in place of
`m.*` throughout this proposal.
