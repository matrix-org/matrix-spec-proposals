# MSC3786: Add a default push rule to ignore `m.room.server_acl` events

`m.room.server_acl` events allow for expressing which servers can participate in
a room. Often during spam attacks, these events are sent quite frequently, which
causes the users to be overwhelmed by notifications, if they have the room rule
set to `notify` (`All messages` in Element). (See
<https://github.com/vector-im/element-web/issues/20788>) As this is very
unideal, this MSC proposes a new push rule to avoid this. It is analogues
to [MSC2153](https://github.com/matrix-org/matrix-spec-proposals/pull/2153).

## Proposal

A new [default override rule](https://spec.matrix.org/v1.2/client-server-api/#default-override-rules) is to be added that ignores `m.room.server_acl`
events:

```json
{
    "rule_id": ".m.rule.room.server_acl",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.room.server_acl"
        }
    ],
    "actions": [
        "dont_notify"
    ]
}
```

This new push rule is inserted immediately after `.m.rule.tombstone`.

## Unstable prefix

During development, `.org.matrix.msc3786.rule.room.server_acl` is to be used
instead of `.m.rule.room.server_acl`.
