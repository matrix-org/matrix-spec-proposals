# MSC3664: Notifications for relations

Relations are very powerful and are becoming a platform to build new features
like replies, edits, reactions, threads, polls and much more on.

On the other hand there is currently no way to control, what you are getting
notified for. Some people want to get notified, when someone replies to their
message. Some want to get notified for reactions to their message. Some people
explicitly do not want that. You might want to be able to mute a thread and you
may want to get notified for poll responeses or not. Some people like getting
notified for edits, others prefer to not get notified, when someone fixes typos
20 times in a row for a long message they sent a week ago.

We should extend push rules so that a server can provide sane defaults and users
can adjust them to their own wishes.

## Proposal

### New push rule condition: `related_event_match`

Notifications for relation based features need to distinguish, what type of
relation was used and potentially match on the content of the related-to event.

To do that we introduce a new type of condition: `related_event_match`. This is
largely similar to the existing `event_match`, but operates on the related-to
event. Such a condition could look like this:

```json5
{
  "kind": "related_event_match",
  "rel_type": "m.in_reply_to",
  "key": "sender",
  "pattern": "@me:my.server"
}
```

This condition can be used to notify me whenever someone sends a reply to my
messages.

- `rel_type` is the relation type. For the sake of compatibility replies
    should be matched as if they were sent in the relation format from
    [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) with a
    `rel_type` of `m.in_reply_to`. If the event has any relation of this type,
    the related event should be matched using `pattern` and `key`.
- `key` (optional): The dot-separated field of the event to match, e.g. `content.body`
    or `sender`. If it is not present, the condition should match all events,
    that have a relation of type `rel_type`.
- `pattern` (optional): The glob-style pattern to match against. Patterns with
    no special glob characters should be treated as having asterisks prepended
    and appended when testing the condition. If this is not present, it should
    match everything if the specific key is present.

`key` and `pattern` are optional to allow you to enable or suppress all
notifications for a specific event type. For example one could suppress
notifications for all events in
[threads](https://github.com/matrix-org/matrix-doc/pull/3440) and all
[edits](https://github.com/matrix-org/matrix-doc/pull/2676) with the following
two conditions:

```json5
{
  "kind": "related_event_match",
  "rel_type": "m.replace"
}
```

```json5
{
  "kind": "related_event_match",
  "rel_type": "m.thread"
}
```

Without a `key` the push rule can be evaluated without fetching the related to
event.

### A push rule for replies

To enable notifications for replies without relying on the reply fallback, but
with similar semantics we also define a new default push rule. The proposed
push rule differs slightly from the old behaviour, because it only notifies you
for replies to your events, but it does not notify you for replies to events,
which contained your display name or matrix ID. The rule should look like this:

```json5
{
    "rule_id": ".m.rule.reply",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "related_event_match"
            "rel_type": "m.in_reply_to",
            "key": "sender",
            "pattern": "[the user's Matrix ID]"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        },
        {
            "set_tweak": "highlight"
        }
    ]
}
```

This should be an underride rule, since it can't be a content rule. It ensures
you get notified for replies to all events you sent. The actions are the same as
for `.m.rule.contains_display_name` and `.m.rule.contains_user_name`.

No other rules are proposed as no other relations are in the specification as of
writing this MSC to decrease dependencies.

## Potential issues

- Most push rules for relations will need a lookup into a second event. This
    causes additional implementation complexity and can potentially be
    expensive. Looking up one event shouldn't be that heavy, but it is overhead,
    that wasn't there before and it needs to be evaluated for every event, so it
    clearly is somewhat performance sensitive.
- If the related to event is not present on the homeserver, evaluating the
    push rule may be delayed or fail completely. For most rules this should not
    be an issue. You can assume the event was not sent by a user on your server
    if the event is not present on your server.

## Alternatives

- One could add an optional `rel_type` key to all existing conditions. This
    would allow you to also easily match by `contains_display_name`,
    `sender_notification_permission` and `room_member_count`. Out of those
    conditions only `contains_display_name` seems to be useful in a related
    event context. Having a potentially expensive key like `rel_type` available
    for all conditions would also increase implementation complexity. As such
    this MSC proposes the minimum amount of conditions to support push rules for
    most relations, although allowing `rel_type` on `contains_display_name` and
    `event_match` could be a good alternative.
- Beeper has a
    [similar feature in their synapse](https://gitlab.com/beeper/synapse/-/commit/44a1728b6b021f97900c89e0c00f7d1a23ce0d43),
    but it does not allow you to filter by relation type and also differs
    otherwise from the usual naming of push rule condition.


## Security considerations

- These pushrules could be used to increase load on the homeserver. Apart from
    that there shouldn't be any potential security issues.

## Unstable prefix

While this proposal is still in progress, implementations should use the
unstable prefix `im.nheko.msc3664` for the `related_event_match` condition. As
a result it should be called `im.nheko.msc3664.related_event_match`.

