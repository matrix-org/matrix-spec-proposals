# MSC4053: Extensible Events - Mentions mixin

Matrix 1.7 introduced ["intentional mentions"](https://spec.matrix.org/v1.8/client-server-api/#user-and-room-mentions)
to improve how users are mentioned via Matrix events. This was defined in
[MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952), which
[deprecated the legacy push rules](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3952-intentional-mentions.md#backwards-compatibility),
but left it to a future MSC to disable them:

* [`.m.rule.contains_display_name`](https://spec.matrix.org/v1.8/client-server-api/#default-override-rules)
* [`.m.rule.contains_user_name`](https://spec.matrix.org/v1.8/client-server-api/#default-content-rules)
* [`.m.rule.roomnotif`](https://spec.matrix.org/v1.8/client-server-api/#default-override-rules)

The logical time to remove these legacy mentions push rules is when extensible
events are supported.

## Proposal

It is proposed that a future room version implementing [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932)
shall stop supporting the above legacy mentions rules. This does not require any changes
as [noted in MSC3932](https://github.com/matrix-org/matrix-spec-proposals/blob/travis/msc/extev/rver-cond/proposals/3932-extensible-events-room-ver-push-rule-condition.md#proposal):

> Push rules which don't specify a `room_version_supports` condition are assumed
> to not support extensible events and are therefore expected to be treated as
> disabled when a room version does support extensible events.

[Intentional mentions (i.e. the `m.mentions` property)](https://spec.matrix.org/v1.8/client-server-api/#user-and-room-mentions)
is redefined as an extensible events "mixin" ([see MSC1767](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md#mixins-specifically-allowed)).
No changes to the implementation are needed except for additional push rules (similar
to those defined in [MSC3933](https://github.com/matrix-org/matrix-spec-proposals/pull/3933)) [^1]:

The `.m.rule.mixin.is_user_mention` override push rule would appear directly
before the `.m.rule.is_user_mention` push rule:

```json
{
    "rule_id": ".m.rule.mixin.is_user_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_property_contains",
            "key": "content.m\\.mentions.user_ids",
            "value": "[the user's Matrix ID]"
        },
        {
            "kind": "room_version_supports",
            "feature": "m.extensible_events"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        },
        {
            "set_tweak": "highlight"
        }
    ]
}
```

(Note: `\\.` would become a single logical backslash followed by a dot since the
above is in JSON-representation. See
[the appendicies](https://spec.matrix.org/v1.8/appendices/#dot-separated-property-paths).)

The `.m.rule.mixin.is_room_mention` override push rule would appear directly
before the `.m.rule.is_room_mention` push rule:

```json
{
    "rule_id": ".m.rule.mixin.is_room_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_property_is",
            "key": "content.m\\.mentions.room",
            "value": true
        },
        {
            "kind": "sender_notification_permission",
            "key": "room"
        },
        {
            "kind": "room_version_supports",
            "feature": "m.extensible_events"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight"
        }
    ]
}
```

## Potential issues

This does not really allow for the *removal* of the old push rules (until
implementations drop support for legacy room versions), but it is a step in the
correct direction.

## Alternatives

An additional `feature` could be defined which allows for use both with and without
extensible events.

----

This could potentially be grouped into [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932) or
[MSC3933](https://github.com/matrix-org/matrix-spec-proposals/pull/3933) if desired.

## Security considerations

Additional push rules result in extra processing, but an implementation could
partition push rules by room version.

## Unstable prefix

While this proposal is not considered stable, implementations should use
`org.matrix.msc4053.*` in place  of `m.*`. Also note that the `kind` and feature
flags may need to use unstable identifiers until
[MSC3931](https://github.com/matrix-org/matrix-spec-proposals/pull/3931) and
[MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932)
are merged.

## Dependencies

This MSC builds on the following MSCs which at the time of writing have not yet
been accepted into the spec:

* [MSC3931](https://github.com/matrix-org/matrix-spec-proposals/pull/3931): Push rule condition for room version features
* [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932): Extensible events room version push rule feature flag

It also depends on the following MSCs which at the time of writing have been
accepted into the spec, but not yet released:

* [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767): Extensible event types & fallback in Matrix (v2)

It also depends on the following MSCs which at the time of writing have been accepted
into the spec and released:

* [MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952): Intentional Mentions

The following MSCs are related and may help understanding of this MSC, but not
dependencies:

* [MSC3933](https://github.com/matrix-org/matrix-spec-proposals/pull/3933): Core push rules for Extensible Events
* [MSC3955](https://github.com/matrix-org/matrix-spec-proposals/pull/3955): Extensible Events - Automated event mixin (notices)

<!-- Footnotes below -->

[^1]: Note the proposed push rules are identical to
[the push rules from MSC3952](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3952-intentional-mentions.md#new-push-rules),
except the rule ID is updated and they include a `room_version_supports` condition.
