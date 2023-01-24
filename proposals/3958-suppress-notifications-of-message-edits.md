# MSC3958: Suppress notifications of message edits

[Event replacement](https://spec.matrix.org/v1.5/client-server-api/#event-replacements)
(more commonly known as message edits) signals that a message is intended to
be replaced with new content.

This works well for fixing typos or correcting information, but tends to cause
spurious notifications if the event mentions a user. This contributes to notification
fatigue as the additional notifications contain no new information.


## Proposal

A new default push rule is added to suppress notifications [due to edits](https://spec.matrix.org/v1.5/client-server-api/#event-replacements).

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

This rule should be placed as the [first override rule](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules).

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

## Potential issues

Some users may be depending on notifications of edits. If a user would like to
revert to the old behavior they can disable the `.m.rule.suppress_edits` push rule.

If the message edits were allowed by other senders than it would be useful to
know that your own message was edited, but this
[is not currently allowed](https://spec.matrix.org/v1.5/client-server-api/#validity-of-replacement-events).

## Alternatives

None explored.

## Security considerations

None forseen.

## Unstable prefix

The unstable prefix of `.com.beeper.suppress_edits` should be used in place of
`.m.rule.suppress_edits`.

## Dependencies

N/A
