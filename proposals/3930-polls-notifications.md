# MSC3930: Polls push rules/notifications

[MSC3381](https://github.com/matrix-org/matrix-spec-proposals/pull/3381) describes how chat polls can work,
though deliberately leaves out details on how push rules or notifications could work for such a feature.
This proposal aims to address that specific feature gap.

Readers should review MSC3381 to better understand how polls are intended to operate in a room.

Push rules are currently defined [here](https://spec.matrix.org/v1.7/client-server-api/#push-rules) in
specification.

## Proposal

Polls should behave similar to message events. To achieve this effect, we define the following underride
push rules which mimic their `m.room.message` partners.

Note that [order matters](https://github.com/matrix-org/matrix-spec/issues/1406) for push rules - these
underride rules are to be inserted immediately after the `.m.rule.encrypted` underride push rule, in the
order presented by this MSC.

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

Additionally, a new override rule is defined to suppress poll responses by default, inserted immediately
after the `.m.rule.room.server_acl` override rule.

```json
{
  "rule_id": ".m.rule.poll_response",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "event_match", "key": "type", "pattern": "m.poll.response"}
  ],
  "actions": []
}
```

*Note*: Lack of `actions` means "don't do anything with matching events", or "don't notify".

Typically these rules would be kept in sync with the `m.room.message` rules they are based upon,
however there is no requirement to do so. A client's approach might be to only keep them in sync
while setting the values, rather than monitoring for changes to push rules.

Clients might find [MSC3934](https://github.com/matrix-org/matrix-spec-proposals/pull/3934) of value
for keeping the rules in sync, though this MSC does not require MSC3934.

For the purposes of [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932), the
push rules defined in this proposal are *not* affected by the room version limitations. This is due
to polls not inherently being room version-specific, unlike other extensible event structures. For
clarity, this means the push rules described here are treated the same as `.m.rule.master` (for
example) - they always apply, regardless of room version.

## Potential issues

The push rules for this feature are complex and not ideal. The author believes that it solves a short
term need while other MSCs work on improving the notifications system. Most importantly, the author
believes future MSCs which aim to fix notifications for extensible events in general will be a more
preferred approach over this MSC's (hopefully) short-term solution.

## General considerations

While the order within the MSC is deliberate for the new rules, the positioning relative to other rules
already in the spec is fairly arbitary. The new rules are placed at the end of each list (underride and
override) for simplicty, but could realistically go anywhere in the list.

## Security considerations

None applicable - no new considerations need to be made with this proposal.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3930.*` as a prefix
in place of `m.*` for the push rule IDs. As of writing, polls are only implemented using the legacy
`org.matrix.msc3381.poll.*` prefix rather than the newer `v2` prefix - implementations of this MSC
should be aware of which version of MSC3381 they plan to support.
