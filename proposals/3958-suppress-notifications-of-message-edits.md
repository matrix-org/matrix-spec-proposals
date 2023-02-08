# MSC3958: Suppress notifications from message edits

[Event replacement](https://spec.matrix.org/v1.5/client-server-api/#event-replacements)
(more commonly known as message edits) signals that a message is intended to
be replaced with new content.

This works well for fixing typos or other minor correction, but can cause
spurious notifications if the event mentions a user's display name / localpart or
if it includes `@room` (which is particularly bad in large rooms as every user
is re-notified). This contributes to notification fatigue as the additional
notifications contain no new information.

## Proposal

A new default push rule is added to suppress notifications due to [edits](https://spec.matrix.org/v1.5/client-server-api/#event-replacements).

```json
{
    "rule_id": ".m.rule.suppress_edits",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "content.m.relates_to.rel_type",
            "pattern": "m.replace"
        }
    ],
    "actions": []
}
```

This rule should be placed before the [`.m.rule.suppress_notices` rule](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules)
as the first non-master, non-user added override rule.

It would match events such as those given in [event replacements](https://spec.matrix.org/v1.5/client-server-api/#event-replacements)
portion of the spec:

```json5
{
    "type": "m.room.message",
    "content": {
        "body": "* Hello! My name is bar",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text"
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id"
        }
    },
    // ... other fields required by events
}
```

Some users may be depending on notifications of edits. If a user would like to
revert to the old behavior they can disable the `.m.rule.suppress_edits` push rule.

## Potential issues

### Editing mentions

With this MSC it would no longer possible to edit a message to change who is going
to be notified. For instance, if you write a message and then edit it to put another
user pill in it, in this case the user would not be notified. Socially it seems more
likely for the sender to send another message instead of editing:

> @alice:example.com see above ^

### Rule Ambiguity

The rule is ambiguous (see [MSC3873](https://github.com/matrix-org/matrix-spec-proposals/pull/3873))
due to the `.` in `m.relates_to` and could also match other, unrelated, events:

```json5
{
    "type": "m.room.message",
    "content": {
        "body": "* Hello! My name is bar",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text"
        },
        "m": {
            "relates_to": {
                "rel_type": "m.replace",
                "event_id": "$some_event_id"
            }
        }
    },
    // ... other fields required by events
}
```

(Note that `relates_to` being embedded inside of the `m`.)

### Keeping notifications up-to-date

Another issues is that mobile clients would no longer receive push notifications for
message edits, which are currently used to update the text of on-screen notifications
to show the updated content. The proposed push rule would mean that mobile clients would
no longer receive this update, but showing slightly outdated text on a notification screen
is only a minor impact and it would be better to separate when (& why) we send pushes vs.
when we generate notifications.

## Alternatives

An alternative solution would be to add a push rule with no actions and a condition to
check whether a notification should have been generated for the user in the original
message.

This should be placed as an override rule before the `.m.rule.contains_display_name`
and the `.m.rule.roomnotif` [push rules](https://spec.matrix.org/v1.5/client-server-api/#push-rules).

This would suppress duplicate notifications, while still allow for new notifications due
to new mentions or keywords changing.

## Security considerations

None forseen.

## Future extensions

If message edits by other senders were allowed than it would be useful to
know when your own message was edited, but this
[is not currently allowed](https://spec.matrix.org/v1.5/client-server-api/#validity-of-replacement-events).
A future MSC to define this behavior should take into account notifying
users in this situation.

## Unstable prefix

The unstable prefix of `.com.beeper.suppress_edits` should be used in place of
`.m.rule.suppress_edits`.

## Dependencies

N/A
