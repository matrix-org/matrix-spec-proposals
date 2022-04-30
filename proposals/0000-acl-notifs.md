# MSC0000: Add a default push rule to ignore `m.room.server_acl` events

`m.room.server_acl` events allow for expressing which servers can participate in
a room. Often during spam attacks, these events are sent quite frequently, which
causes the users to be overwhelmed by notifications. (See
<https://github.com/vector-im/element-web/issues/20788>) As this is very
unideal, this MSC proposes a new push rule to avoid this.

## Proposal

A new default override rule is to be added that ignores `m.room.server_acl`
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

## Unstable prefix

During development, `org.matrix.msc0000.rule.room.server_acl` is to be used
instead of `.m.rule.room.server_acl`.
