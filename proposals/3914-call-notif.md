# MSC3914: Matrix native group call push rule

[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) defines
how group calls can happen over Matrix. It adds a an `m.call` state event with
an `m.intent` field which, if it has a value of `m.ring` or `m.prompt`, should
cause a notification should be shown to the user. This MSC defines a new push
rule for this scenario.

## Proposal

A new push-rule condition is added with the name `call_started`. For this
condition to be met the following conditions have to be met:

- `m.intent` must either be `m.ring` or `m.prompt`
- `m.terminated` must _not_ be in the content
- the `prev_content` is either missing or includes `m.terminated`

This is a new push condition since the current push-rule system is not flexible
enough for this to be built out of existing rules.

A new [default underride
rule](https://spec.matrix.org/v1.2/client-server-api/#default-underride-rules) is
to be added:

```json
{
    "rule_id": ".m.rule.room.call",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.call"
        },
        {
            "kind": "call_started"
        }
    ],
    "actions": [
        "notify", 
        {"set_tweak": "sound", "value": "default"}
    ]
}
```

This new push rule is inserted immediately after `.m.rule.call`.

## Potential issues

Once we have state event E2EE all notifications will have to be handled
client-side as the server won't see the content of events.

## Alternatives

This could be implemented entirely client-side without any push rule though this
presents an issue for mobile devices which can't sync all the time and therefore
need to receive push notifications.

## Unstable prefix

During development, `.org.matrix.msc3914.rule.room.call` and
`org.matrix.msc3914.call_started` is to be used instead of `.m.rule.room.call`
and `call_started` respectively.
