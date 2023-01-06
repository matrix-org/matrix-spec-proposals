# MSC3952: Intentional Mentions

Mentioning other users on Matrix is difficult -- it is not possible to know if
[mentioning a user by display name or Matrix ID](https://github.com/matrix-org/matrix-spec/issues/353)
will count as a mention, but is also too easy to mistakenly mention a user.

(Note that throughout this proposal "mention" is considered equivalent to a "ping"
or highlight notification.)

Some situations that result in unintentional mentions include:

* Replying to a message will re-issue pings from the initial message due to
  [fallback replies](https://spec.matrix.org/v1.5/client-server-api/#fallbacks-for-rich-replies). [^1]
* Each time a message is edited the new version will be re-evaluated for mentions.
* Mentions occurring [in spoiler contents](https://github.com/matrix-org/matrix-spec/issues/16)
  or [code blocks](https://github.com/matrix-org/matrix-spec/issues/15) are
  evaluated.
* If the [localpart of your Matrix ID is a common word](https://github.com/matrix-org/matrix-spec-proposals/issues/3011)
  then the push rule matching usernames (`.m.rule.contains_user_name`) matches
  too often (e.g. Travis CI matching if your Matrix ID is `@travis:example.com`).
* If the [localpart or display name of your Matrix ID matches the hostname](https://github.com/matrix-org/matrix-spec-proposals/issues/2735)
  (e.g. `@example:example.com` receives notifications whenever `@foo:example.com`
  is replied to).

As a sender you do not know if including the user's display name or Matrix ID would
even be interpreting as a mention (see [issue 353](https://github.com/matrix-org/matrix-spec/issues/353)).

This also results in some unexpected behavior and bugs:

* Matrix users use "leetspeak" when sending messages to avoid mentions (e.g.
  referring to M4tthew instead of Matthew).
* Matrix users will append emoji or other unique text in their display names to
  avoid unintentional pings.
* It is impossible to ping one out of multiple people with the same localpart
  (or display name).
* Since the relation between `body` and `formatted_body` is ill-defined and
  ["pills" are converted to display names](https://github.com/matrix-org/matrix-spec/issues/714),
  this can result in missed messages.
* Bridges [must use display names](https://github.com/matrix-org/matrix-spec/issues/353#issuecomment-1055809364)
  as a trick to get pings to work.
* If a user changes their display name in a room than whether or not they are
  mentioned changes unless you use historical display names to process push rules.
  (TODO I think there's an issue about this?)

## Background

Mentions are powered by two of the default push rules that search an event's
`content.body` field for the current user's display name
([`.m.rule.contains_display_name`](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules))
or the localpart of their Matrix ID ([`.m.rule.contains_user_name`](https://spec.matrix.org/v1.5/client-server-api/#default-content-rules)).

There's also a [section about "user and room mentions"](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
which defines that messages which mention the current user in the `formatted_body`
of the message should be colored differently:

> If the current user is mentioned in a message (either by a mention as defined
> in this module or by a push rule), the client should show that mention differently
> from other mentions, such as by using a red background color to signify to the
> user that they were mentioned.

## Proposal

Instead of searching a message's `body` for the user's display name or the localpart
of their Matrix ID, it is proposed to use a field specific to mentions,[^2] and
augment the push rules to search for the current user's Matrix ID.

### New event field

A new `mentions` field is added to the event content, it is an array of strings
consistent of Matrix IDs.

To limit the potential for abuse, only the first 10 items in the array should be
considered. It is recommended that homeservers reject locally created events with
more than 10 mentions with an error with a status code of `400` and an errcode of
`M_INVALID_PARAM`.

Clients should add a Matrix ID to this array whenever composing a message which
includes an intentional [user mention](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
(often called a "pill"). Clients may also add them at other times when it is
obvious the user intends to explicitly mention a user.

The `mentions` field is part of the plaintext event body and should be encrypted
into the ciphertext for encrypted events.

### New push rules

A new push rule condition and a new default push rule will be added:

```json
{
    "rule_id": ".m.rule.user_is_mentioned",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "is_mention"
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

The `is_mention` push condition is defined as[^3]:

> This matches messages where the `content.mentions` is an array containing the
> owner’s Matrix ID in the first 10 entries. This condition has no parameters.
> If the `mentions` key is absent or not an array then the rule does not match;
> any array entries which are not strings are ignored, but count against the limit.

An example matching event is provided below:

```json
{
    "content": {
        "body": "This is an example mention @alice:example.org",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>This is an example mention</b> <a href='https://matrix.to/#/@alice:example.org'>Alice</a>",
        "msgtype": "m.text",
        "mentions": ["@alice:example.org"]
    },
    "event_id": "$143273582443PhrSn:example.org",
    "origin_server_ts": 1432735824653,
    "room_id": "!somewhere:over.the.rainbow",
    "sender": "@example:example.org",
    "type": "m.room.message",
    "unsigned": {
        "age": 1234
    }
}
```

### Backwards compatibility

The the [`.m.rule.contains_display_name`](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules)
and [`.m.rule.contains_user_name`](https://spec.matrix.org/v1.5/client-server-api/#default-content-rules)
push rules are both deprecated. To avoid the unintentional mentions they are both
modified to only apply when the `mentions` field is missing. As this is for
backwards-compatibility it is not implemented using a generic mechanism, but
behavior specific to those push rules with those IDs.

While this is being deployed there will be a mismatch for legacy clients which
implement the deprecated `.m.rule.contains_display_name` and `.m.rule.contains_user_name`
push rules locally while the `.m.rule.user_is_mentioned` push rule is used on
the homeserver; as messages which
[mention the user should also include the user's localpart](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
in the message `body` it is likely that the `.m.rule.contains_user_name`
will also match. It is postulated that this will not cause issues in most cases.

## Potential issues

### Abuse potential

This proposal makes it trivial to "hide" mentions since it does not require the
mentioned Matrix IDs to be part of the displayed text. This is not seen as
worse than what is possible today.

From discussions and research while writing this MSC there are some benefits to
using a separate field for mentions:

* The number of mentions is trivially limited.
* Various forms of "mention bombing" are no longer possible.
* It is simpler to collect data on how many users are being mentioned (without
  having to process the textual `body` for every user's display name and local
  part).

Nonetheless, the conversations did result in some ideas to combat the potential
for abuse, many of which apply regardless of whether this proposal is implemented.

Clients could expose *why* an event has caused a notification and give users inline
tools to combat potential abuse. For example, a client might show a tooltip:

> The sender of the message (`@alice:example.org`) mentioned you in this event.
>
> Block `@alice:example.org` from sending you messages? `[Yes]` `[No]`

It could also be worth exposing user interface for moderators to see messages
which mention many users.

A future MSC might wish to explore features for trusted contacts or soft-ignores
to give users more control over who can generate notifications.

Overall the proposal does not seem to increase the potential for malicious behavior.

## Alternatives

### Prior proposals

There's a few prior proposals which tackle subsets of the above problem:

* [MSC2463](https://github.com/matrix-org/matrix-spec-proposals/pull/2463):
  excludes searching inside a Matrix ID for localparts / display names of other
  users.
* [MSC3517](https://github.com/matrix-org/matrix-spec-proposals/pull/3517):
  searches for Matrix IDs (instead of display name / localpart) and only searches
  specific event types & fields.
* [Custom push rules](https://o.librepush.net/aux/matrix_reitools/pill_mention_rules.html)
  to search for matrix.to links instead of display name / localpart.

  <summary>

  This generates a new push rule to replace `.m.rule.contains_display_name` and
  `.m.rule.contains_user_name`:

  ```json
  {
     "conditions": [
       {
           "kind": "event_match",
           "key": "content.formatted_body",
           "pattern": "*https://matrix.to/#/@alice:example.org*"
       }
     ],
     "actions" : [
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

  </summary>

### Room version for backwards compatibility

Alternative backwards compatibility suggestions included using a new room version,
similar to [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932)
for extensible events. This does not seem like a good fit since room versions are
not usually interested in non-state events. It would additionally require a stable
room version before use, which would unnecessarily delay usage.

## Security considerations

None foreseen.

## Unstable prefix

During development the `.org.matrix.msc3952.is_user_mentioned` push rule will be
used. If a client sees this rule available it should apply the custom logic discussed
in the [backwards compatibility](#backwards-compatibility) section.

## Dependencies

N/A

[^1]: This MSC does not attempt to solve this problem, but [MSC2781](https://github.com/matrix-org/matrix-spec-proposals/pull/2781)
proposes removing reply fallbacks which would solve it. Although as noted in
[MSC3676](https://github.com/matrix-org/matrix-spec-proposals/pull/3676) this
may require landing [MSC3664](https://github.com/matrix-org/matrix-doc/pull/3664)
in order to receive notifications of replies.

[^2]: As proposed in [issue 353](https://github.com/matrix-org/matrix-spec/issues/353).

[^3]: A new push condition is necessary since none of the current push conditions
(e.g. `event_match`) can process arrays.
