# MSC3952: Intentional Mentions

Mentioning other users on Matrix is difficult -- it is not possible to know if
[mentioning a user by display name or Matrix ID](https://github.com/matrix-org/matrix-spec/issues/353)
will count as a mention, but is also too easy to mistakenly mention a user.

(Note that throughout this proposal "mention" is considered equivalent to a "ping"
or highlight notification.)

Some situations that result in unintentional mentions include:

* Replying to a message will re-issue pings from the initial message due to
  [fallback replies](https://spec.matrix.org/v1.5/client-server-api/#fallbacks-for-rich-replies). [^1]
* Each time a message is edited the new version will be re-evaluated for mentions. [^2]
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
even be interpreted as a mention (see [issue 353](https://github.com/matrix-org/matrix-spec/issues/353)).
This results in some unexpected behavior and bugs:

* Matrix users use "leetspeak" when sending messages to avoid mentions (e.g.
  referring to M4tthew instead of Matthew).
* It is impossible to ping one out of multiple people with the same localpart
  (or display name).
* Since the relation between `body` and `formatted_body` is ill-defined and
  ["pills" are converted to display names](https://github.com/matrix-org/matrix-spec/issues/714),
  this can result in missed messages. [^B]

There is also some other related bugs:

* Matrix users will append emoji or other unique text in their display names to
  avoid unintentional pings.
* Bridges [must use display names](https://github.com/matrix-org/matrix-spec/issues/353#issuecomment-1055809364)
  as a trick to get pings to work.
* If a user changes their display name in a room, they might not be mentioned
  unless the historical display name is used while processing push rules.
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
of their Matrix ID, it is proposed to use a field specific to mentions,[^3] and
augment the push rules to search for the current user's Matrix ID.

### New event field

A new `mentions` field is added to the event content, it is an array of strings
consistent of Matrix IDs or the special value: `"@room"`.

To limit the potential for abuse, only the first 10 items in the array should be
considered. It is recommended that homeservers reject locally created events with
more than 10 mentions with an error with a status code of `400` and an errcode of
`M_INVALID_PARAM`. It is valid to include specific users in addition to the
`"@room"` value.

Clients should add a Matrix ID to this array whenever composing a message which
includes an intentional [user mention](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
(often called a "pill"). Clients should add the `"@room"` value when making a
room-wide announcement. Clients may also add them at other times when it is
obvious the user intends to explicitly mention a user.

If a user generates a message with more than 10 mentions, the client may wish to
show a warning message to the user; it may silently limit the number sent in the
message to 10 or force the user to remove some mentions.

The `mentions` field is part of the cleartext event body and should **not** be
encrypted into the ciphertext for encrypted events. This expoes slightly more
metadata to homeservers, but allows mentions to work properly via push notifications
(which is a requirement for a usable chat application) and should result in bandwidth
and battery savings.

### New push rules

Two new push rule conditions and corresponding default push rule are proposed:

The `is_user_mention` push condition is defined as[^4]:

> This matches messages where the `content.mentions` is an array containing the
> owner’s Matrix ID in the first 10 entries. This condition has no parameters.
> If the `mentions` key is absent or not an array then the rule does not match;
> any array entries which are not strings are ignored, but count against the limit.

The `is_room_mention` push condition is defined as[^4]:

> This matches messages where the `content.mentions` is an array containing the
> string `"@room"` in the first 10 entries. This condition has no parameters.
> If the `mentions` key is absent or not an array then the rule does not match;
> any array entries which are not strings are ignored, but count against the limit.

The proposed `.m.rule.is_user_mention` override push rule would appear directly
before the `.m.rule.contains_display_name` push rule:

```json
{
    "rule_id": ".m.rule.is_user_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "is_user_mention"
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

The proposed `.m.rule.is_room_mention` override push rule would appear directly
before the `.m.rule.roomnotif` push rule:

```json
{
    "rule_id": ".m.rule.is_room_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "is_room_mention"
        },
        {
            "kind": "sender_notification_permission",
            "key": "room"
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

An example event matching both `.m.rule.is_user_mention` (for `@alice:example.org`)
and `.m.rule.is_room_mention` is provided below:

```json
{
    "content": {
        "body": "This is an example mention @alice:example.org",
        "format": "org.matrix.custom.html",
        "formatted_body": "<b>This is an example mention</b> <a href='https://matrix.to/#/@alice:example.org'>Alice</a>",
        "msgtype": "m.text",
        "mentions": ["@alice:example.org", "@room"]
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

The [`.m.rule.contains_display_name`](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules),
[`.m.rule.contains_user_name`](https://spec.matrix.org/v1.5/client-server-api/#default-content-rules),
and [`.m.rule.roomnotif`](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules)
push rules are to be removed. To avoid unintentional mentions these rules are
modified to only apply when the `mentions` field is missing. As this is for
backwards-compatibility it is not implemented using a generic mechanism, but
behavior specific to these push rules.

If users wish to continue to be notified of messages containing their display name
it is recommended that clients create a specific keyword rule for this, e.g. a
`content` rule of the form:

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
  "pattern": "alice",
  "rule_id": "alice",
  "enabled": true
}
```

After acceptance, it is likely for some disagreement about which push rules are
implemented: legacy clients and homeservers may not yet have deprecated the
`.m.rule.contains_display_name`, `.m.rule.contains_user_name`, and `.m.rule.roomnotif`
push rules, while up-to-date clients and homeservers will support the
`.m.rule.is_user_mention` and `.m.rule.is_room_mention` push rules. It is expected
that both sets of push rules will need to be supported for a period of time, but
at worst case should simply result in the current behavior (documented in the preamble).

## Potential issues

### Abuse potential

This proposal makes it trivial to "hide" mentions since it does not require the
mentioned Matrix IDs to be part of the displayed text. Depending on the use this
can be a feature (similar to CCing a user on an e-mail) or an abuse vector. Overall,
this MSC does not enable additional malicious behavior than what is possible today.

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

It could also be worth exposing user interface showing all of the mentions in a
message, especially if those users are not included in the message body. One way
to do this could be a deemphasized "CC" list. Additionally, it would be useful for
moderators to quickly find messages which mention many users.

A future MSC might wish to explore features for trusted contacts or soft-ignores
to give users more control over who can generate notifications.

Overall the proposal does not seem to increase the potential for malicious behavior.

## Future extensions

### Configurable mentions limits

It maybe desirable for room administrators to configure the number of allowed
mentions in a message, e.g. a conference may want to mention 50 people at once
or it may be appropriate for a kudos room to mention the 15 people on your team.
Since it is easy enough to work around the limit of 10 mentions in socially
appropriate situations (by sending multiple messages) it does not seem worth
the technical complexity of allowing this number to be configurable.

### Muted except for mentions push rules

By leaving the mentions array unencrypted it allows for a "muted-except-for-mentions"
push rule. This is particularly useful for large (encrypted) rooms where you would
like to receive push notifications for mentions *only*. It is imperative for
the homeserver to be able to send a push in this case since some mobile platforms,
e.g. iOS, do not sync regularly in the background.

### Pillifying `@room`

Some clients attempt to create a "pill" out of `@room` mentions, but this is not
a requirement of the Matrix specification. The current [user and rooms mentions](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
section could be expanded for this situation.

## Alternatives

### Prior proposals

There's a few prior proposals which tackle subsets of the above problem:

* [MSC1796](https://github.com/matrix-org/matrix-spec-proposals/pull/1796):
  extremely similar to the proposal in this MSC, but limited to encrypted events.
* [MSC2463](https://github.com/matrix-org/matrix-spec-proposals/pull/2463):
  excludes searching inside a Matrix ID for localparts / display names of other
  users.
* [MSC3517](https://github.com/matrix-org/matrix-spec-proposals/pull/3517):
  searches for Matrix IDs (instead of display name / localpart) and only searches
  specific event types & fields.
* [Custom push rules](https://o.librepush.net/aux/matrix_reitools/pill_mention_rules.html)
  to search for matrix.to links instead of display name / localpart.

  <details>

  The above generates a new push rule to replace `.m.rule.contains_display_name`
  and `.m.rule.contains_user_name`:

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

  </details>

### Room version for backwards compatibility

Alternative backwards compatibility suggestions included using a new room version,
similar to [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932)
for extensible events. This does not seem like a good fit since room versions are
not usually interested in non-state events. It would additionally require a stable
room version before use, which would unnecessarily delay usage.

### Encrypting the `mentions` array

Encrypting the `mentions` array would solve some unintentional mentions, but
will not help with???.

Allowing an encrypted `mentions` array on a per-message basis could allow users
to choose, but would result in inconsistencies and complications:

* What happens if the cleartext `mentions` field does not match the plaintext
  `mentions` field?
* Do push rules get processed on both the cleartext and plaintext message?

It may be argued that clients need to decrypt all messages anyway to handle
user-specific keywords, the process for doing this is costly (either receiving
every message via push notifications or backpaginating every room fully, in case
of a gappy sync) in terms of bandwidth, CPU, and battery.

It is asserted that the use-cases for custom keywords and mentions are sufficiently
different that having different solutions, and different urgencies to receiving
those notifications, is reasonable. In particular, custom keywords is more of a
power-user feature while user mentions working properly (and promptly) is a table-stakes
feature for a messaging application.

## Security considerations

Including the mentioned users in cleartext is a small metadata leak, but the tradeoff
of mentions working properly and the savings in bandwidth and battery makes it worthwhile.

The additional metadata leaked is minor since the homeserver already knows the
room members, how often users are sending messages, when users are receiving messages
(via read receipts, read markers, and sync), etc. Exposing explicit mentions does not
significantly increase metadata leakage.

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

[^2]: Note that this MSC does not attempt to solve the problem of issues generating
spurious notifications.

[^B]: The `body` is [defined as](https://spec.matrix.org/v1.5/client-server-api/#mroommessage-msgtypes):

> When [the `format` field is set to `org.matrix.custom.html`], a formatted_body
> with the HTML must be provided. The plain text version of the HTML should be
> provided in the `body`.

But there is no particular algorithm to convert from HTML to plain text *except*
when converting mentions, where the
[plain text version uses the text, not the link](https://spec.matrix.org/v1.5/client-server-api/#client-behaviour-26).

[^3]: As proposed in [issue 353](https://github.com/matrix-org/matrix-spec/issues/353).

[^4]: A new push condition is necessary since none of the current push conditions
(e.g. `event_match`) can process arrays.
