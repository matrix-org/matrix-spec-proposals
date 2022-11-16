# MSC3930: Polls push rules/notifications

[MSC3381](https://github.com/matrix-org/matrix-spec-proposals/pull/3381) describes how chat polls can work,
though deliberately leaves out details on how push rules or notifications could work for such a feature.
This proposal aims to address that specific feature gap.

Readers should review MSC3381 to better understand how polls are intended to operate in a room.

## Proposal

In order to have polls behave similar to message events, the following underride push rules are defined.
Note that the push rules are mirrored from those available to `m.room.message` events.

```json
{
  "rule_id": ".m.rule.poll_start_one_to_one",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "room_member_count", "is": "2"},
    {"kind": "event_match", "key": "type", "pattern": "m.poll.start"}
  ],
  "actions": [
    "notify",
    {"set_tweak": "sound", "value": "default"}
  ]
}
```

```json
{
  "rule_id": ".m.rule.poll_start",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "event_match", "key": "type", "pattern": "m.poll.start"}
  ],
  "actions": [
    "notify"
  ]
}
```

```json
{
  "rule_id": ".m.rule.poll_end_one_to_one",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "room_member_count", "is": "2"},
    {"kind": "event_match", "key": "type", "pattern": "m.poll.end"}
  ],
  "actions": [
    "notify",
    {"set_tweak": "sound", "value": "default"}
  ]
}
```

```json
{
  "rule_id": ".m.rule.poll_end",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "event_match", "key": "type", "pattern": "m.poll.end"}
  ],
  "actions": [
    "notify"
  ]
}
```

Servers should keep these rules in sync with the `m.room.message` rules they are based upon. For
example, if the `m.room.message` rule gets muted in a room then the associated rules for polls would
also get muted. Similarly, if either of the two poll rules were to be muted in a room then the other
poll rule and the `m.room.message` rule would be muted as well.

Clients are expected to not require any specific change in order to support these rules. Their user
experience typically already considers an entry for "messages in the room", which is what a typical
user would expect to control notifications caused by polls.

The server-side syncing of the rules additionally means that clients won't have to manually add support
for the new rules. Servers as part of implementation will update and incorporate the rules on behalf
of the users and simply send them down `/sync` per normal - clients which parse the push rules manually
shouldn't have to do anything as the rule will execute normally.

## Potential issues

The push rules for this feature are complex and not ideal. The author believes that it solves a short
term need while other MSCs work on improving the notifications system. Most importantly, the author
believes future MSCs which aim to fix notifications for extensible events in general will be a more
preferred approach over this MSC's (hopefully) short-term solution.

## Security considerations

None applicable - no new considerations need to be made with this proposal.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3930.*` as a prefix
in place of `m.*`.
