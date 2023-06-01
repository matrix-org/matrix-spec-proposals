# MSC3958: Suppress notifications from message edits

[Event replacement](https://spec.matrix.org/v1.7/client-server-api/#event-replacements)
(more commonly known as message edits) signals that a message is intended to
be replaced with new content.

This works well for fixing typos or other minor correction, but can cause
spurious notifications if the event mentions a user's display name / localpart or
if it includes `@room` (which is particularly bad in large rooms as every user
is re-notified). This contributes to notification fatigue as the additional
notifications contain no new information.

Additionally for users which have a room set to "all messages" then every event
edit results in a new notification.

## Proposal

A new default push rule is added to suppress notifications due to [edits](https://spec.matrix.org/v1.7/client-server-api/#event-replacements).

```json
{
    "rule_id": ".m.rule.suppress_edits",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_property_is",
            "key": "content.m\\.relates_to.rel_type",
            "value": "m.replace"
        }
    ],
    "actions": []
}
```

This rule should be placed after the [`.m.rule.room.server_acl` rule](https://spec.matrix.org/v1.7/client-server-api/#default-override-rules)
as the last override rule.

It would match events such as those given in [event replacements](https://spec.matrix.org/v1.7/client-server-api/#event-replacements)
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

With the [updated mentions behavior in Matrix 1.7](https://spec.matrix.org/v1.7/client-server-api/#user-and-room-mentions),
this would allow the [`.m.rule.is_user_mention`](https://spec.matrix.org/v1.7/client-server-api/#_m_rule_is_user_mention)
and the [`.m.rule.is_room_mention`](https://spec.matrix.org/v1.7/client-server-api/#_m_rule_is_room_mention)
rules to continue matching, even for edited events, while suppressing notifications
from other edits.

Some users may be depending on notifications of edits. If a user would like to
revert to the old behavior they can disable the `.m.rule.suppress_edits` push rule.

## Potential issues

### Edits of invites and tombstones

The [`.m.rule.invite_for_me` and `.m.rule.tombstone`](https://spec.matrix.org/v1.7/client-server-api/#default-override-rules)
rules may still cause spurious notifications if events which match those rules
are edited. Both of those are state events and
[not subject to valid edits](https://spec.matrix.org/v1.7/client-server-api/#validity-of-replacement-events).

### Keeping notifications up-to-date

Mobile clients currently depend on the push notifications of edited events to update the
text of on-screen notifications. The proposed push rule would result in mobile clients no
longer receiving these edits; but showing slightly outdated text on a notification screen. That
is only a minor impact and it would be better to separate when (& why) we send pushes vs.
when we generate notifications.

### Suppression of notifications to a new keyword

If an event is edited and the new event (but not the original event) matches a keyword
then the notification would erroneously be suppressed.

## Alternatives

An alternative solution would be to add a push rule with no actions and a condition to
check whether a notification was generated for the original message.

This would be placed as an override rule before the `.m.rule.contains_display_name`
and the `.m.rule.roomnotif` [push rules](https://spec.matrix.org/v1.7/client-server-api/#push-rules).

This would suppress duplicate notifications, while still allow for new notifications due
to new mentions or keywords changing.

## Security considerations

None forseen.

## Future extensions

If message edits by other senders were allowed than it would be useful to
know when your own message was edited, but this
[is not currently allowed](https://spec.matrix.org/v1.7/client-server-api/#validity-of-replacement-events).
A future MSC to define this behavior should take into account notifying
users in this situation.

## Unstable prefix

The unstable prefix of `.org.matrix.msc3958.suppress_edits` should be used in place of
`.m.rule.suppress_edits`.

A previous version of this MSC used `.com.beeper.suppress_edits` with a different condition
(which should match the same events), but different rule placement.

## Dependencies

N/A
