# MSC3964: Notifications for room tags

Users expect that a [room's tag](https://spec.matrix.org/v1.5/client-server-api/#room-tagging)
has an impact on its notification settings. [^1]

The "low priority" setting for rooms is often used in cases where a user
doesn't want to leave a room, but also doesn't care about the room. Similarly,
the "favorites" tag is used to mark rooms which a user *really* cares about.

It is a source of confusion that users continue receiving notifications of all
messages in rooms which are set to "low priority". And it is desirable to control
the notification configuration for all rooms of the same tag at once. This would
enable the following features:

* Mark all low-priority rooms as mentions & keywords. [^2]
* Set all favorites to notify for all message.
* Set all "work" rooms as "mute" (assuming the user has a custom "work" tag).

An additional benefit of being able to control notifications per room tag is that
the total number of push rules per user can be reduced. Instead of having a push
rule per low-priority room, a single rule would suffice. This is useful to limit
the processing effort of push rules as well as reducing the overall size of
`/sync` responses.

## Proposal

### A new push rule condition for room tags

A new [push rule condition](https://spec.matrix.org/v1.5/client-server-api/#conditions-1)
is proposed. The `room_tag` push condition has a single parameter: `pattern`
which is a glob-style pattern to match against the room tags of the room. If any
single room tag matches the pattern then the room condition matches. (Globbing is
performed in the same way as the `event_match` condition.)

If the `pattern` property is not provided then the condition matches against
untagged rooms.

For example, given a room with tags:

```json
{
  "content": {
    "tags": {
      "m.favourite": {
        "order": 0.1
      },
      "u.work": {
        "order": 0.9
      }
    }
  },
  "type": "m.tag"
}
```

This would match a push rule like:

```json
{
  "actions": [
    "notify",
    {
      "set_tweak": "sound",
      "value": "default"
    },
    {
      "set_tweak": "highlight"
    }
  ],
  "conditions": [
    {
      "kind": "room_tag",
      "pattern": "m.favourite"
    }
  ],
  "rule_id": "favourites",
  "enabled": true
}
```

### A new default push rule for low-priority rooms

By default, low-priority rooms would be set "Mentions & Keywords" by default;
this would be done by adding a new `underride` rule:

```json
{
  "rule_id": ".m.rule.suppress_lowpriority",
  "default": true,
  "enabled": true,
  "conditions": [
    {
      "kind": "room_tag",
      "pattern": "m.lowpriority"
    }
  ],
  "actions": []
}
```

## Potential issues

None foreseen.

## Alternatives

### Per-space notifications

Per-space notification configuration has been touted as an alternative. The author
sees these are complementary features.

### Tag matching

The `room_tag` condition only has to match a single tag in order to match, it
might make sense to consider the tag ordering, but it is not clear what impact
that would have on the proposal (since push rules are already ordered).

## Security considerations

N/A

## Unstable prefix

`org.matrix.msc3964.room_tag` should be used instead of `room_tag` for the push
rule condition.

`.org.matrix.msc3964.suppress_lowpriority` push rule ID should replace the new
`.m.rule.suppress_lowpriority` default push rule.

## Dependencies

None.

[^1]: https://github.com/vector-im/element-web/issues/16836
[^2]: https://github.com/vector-im/element-web/issues/915, https://github.com/vector-im/element-meta/discussions/873
