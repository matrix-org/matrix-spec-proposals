# MSC3786: Add a default push rule to ignore `m.room.server_acl` events

`m.room.server_acl` events allow for expressing which servers can participate in
a room. Room server ACLs aren't something the user should have to worry about,
so these events should not trigger notifications; however right now they *do*
trigger notifications, if the user has the room rule set to `notify` (`All
messages` in Element). 

Additionally, these events are often sent quite frequently during spam attacks, 
which causes the users to be overwhelmed by
notifications. (See <https://github.com/vector-im/element-web/issues/20788>.)

Due to these problems, this MSC proposes a new push rule to ignore these events.
The new push rule is analogous to `.m.rule.member_event` (see https://spec.matrix.org/v1.2/client-server-api/#default-override-rules), or `.m.rule.reaction`
(from [MSC2153](https://github.com/matrix-org/matrix-spec-proposals/pull/2153)
or [MSC2677](https://github.com/matrix-org/matrix-spec-proposals/pull/2677)).

## Proposal

A new [default override
rule](https://spec.matrix.org/v1.2/client-server-api/#default-override-rules) is
to be added that ignores `m.room.server_acl` events:

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
