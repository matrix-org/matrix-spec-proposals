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
  this can result in missed messages. [^3]

There are also some other related bugs:

* Matrix users will append emoji or other unique text in their display names to
  avoid unintentional pings.
* Bridges [must use display names](https://github.com/matrix-org/matrix-spec/issues/353#issuecomment-1055809364)
  as a trick to get pings to work.
* If a user changes their display name in a room, they might not be mentioned
  unless the historical display name is used while processing push rules.
  (TODO I think there's an issue about this?)

## Background

Mentions are powered by two of the default push rules that search an event's
`content.body` property for the current user's display name
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
of their Matrix ID, it is proposed to use a property specific to mentions,[^4] and
augment the push rules to search for the current user's Matrix ID.

### New event property

A new `m.mentions` property is added to the event content; it is an object with two
optional properties:

* `user_ids`: an array of strings consisting of Matrix IDs to mention.
* `room`: a boolean, true indicates an "@room" mention. Any other value or the
  property missing is interpreted as not an "@room" mention.  

It is valid to include both the `user_ids` and `room` properties.

It is recommended that homeservers reject locally created events with an invalid
`m.mentions` property with an error with a status code of `400` and an errcode of
`M_INVALID_PARAM`.

Clients should add a Matrix ID to the `user_ids` array whenever composing a message which
includes an intentional [user mention](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
(often called a "pill"). Clients should set the `room` value to `true` when making a
room-wide announcement. Clients may also set these values at other times when it is
obvious the user intends to explicitly mention a user.

The `m.mentions` property is part of the cleartext event body and should **not** be
encrypted into the ciphertext for encrypted events. This exposes slightly more
metadata to homeservers, but allows mentions to work properly. It allows the
server to properly handle push notifications (which is a requirement for a usable
chat application) and could result in bandwidth and battery savings (see the
[future extensions](#muted-except-for-mentions-push-rules) section). Additionally,
it may be useful for the homeserver to filter or prioritize rooms based on whether
the user has been mentioned in them, e.g. for an extension to
[MSC3575 (sliding sync)](https://github.com/matrix-org/matrix-spec-proposals/pull/3575).

### New push rules

Two new default push rule are proposed:

The proposed `.m.rule.is_user_mention` override push rule would appear directly
before the `.m.rule.contains_display_name` push rule:

```json
{
    "rule_id": ".m.rule.is_user_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "exact_event_property_contains",
            "key": "content.m\\.mentions.user_ids",
            "value": "[the user's Matrix ID]"
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
            "kind": "exact_event_match",
            "key": "content.m\\.mentions.room",
            "value": true
        },
        {
            "kind": "sender_notification_permission",
            "key": "room"
        }
    ],
    "actions": [
        "notify",
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
        "m.mentions": {
            "user_ids": ["@alice:example.org"],
            "room": true
        }
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
push rules are to be removed.

To avoid unintentional mentions these rules are modified to only apply when the
`m.mentions` property is missing; clients should provide the `m.mentions` property on
every message to avoid the unintentional mentions discussed above.

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

After acceptance, it is likely for there to be disagreement about which push rules are
implemented: legacy clients and homeservers may not yet have deprecated the
`.m.rule.contains_display_name`, `.m.rule.contains_user_name`, and `.m.rule.roomnotif`
push rules, while up-to-date clients and homeservers will support the
`.m.rule.is_user_mention` and `.m.rule.is_room_mention` push rules. It is expected
that both sets of push rules will need to be supported for a period of time, but
at worst case should simply result in the current behavior (documented in the preamble).

## Potential issues

### Abuse potential

This proposal makes it trivial to "hide" mentions since it does not require the
mentioned Matrix IDs to be part of the displayed text. This is only a limitation
for current clients: mentions could be exposed in the user interface directly.
For example, a de-emphasized "notified" list could be shown on messages, similar
to CCing users on an e-mail.

Although not including mentions in the displayed text could be used as an abuse
vector, it does not enable additional malicious behavior than what is possible
today. From discussions and research while writing this MSC there are moderation
benefits to using a separate property for mentions:

* The number of mentions is trivially limited by moderation tooling, e.g. it may
  be appropriate for a community room to only allow 10 mentions. Events not abiding
  by this could be rejected automatically (or users could be banned automatically).
* Various forms of "mention bombing" are no longer possible.
* It is simpler to collect metrics on how mentions are being used (it is no longer
  necessary to process the textual `body` for every user's display name and local
  part).

Overall this proposal seems to be neutral or positive in the ability to combat
malicious behavior.

## Future extensions

### Combating abuse

Some ideas for combating abuse came from our discussion and research which are
worth sharing. These ideas are not part of this MSC, but also do not depend on it.

It was recommended that clients could expose *why* an event has caused a notification
and give users inline tools to combat abuse. For example, a client might show a tooltip:

> The sender of the message (`@alice:example.org`) mentioned you in this event.
>
> Block `@alice:example.org` from sending you messages? `[Yes]` `[No]`

Additionally, tooling to for moderators to quickly find messages which mention
many users would be useful. 

A future MSC might wish to explore features for trusted contacts or soft-ignores
to give users more control over who can generate notifications.

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

### Extensible events

The `m.mentions` property can be considered a "mixin" as part of extensible events
([MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)) with no needed
changes.

### Role mentions

It is possible to add additional properties to the `m.mentions` object, e.g. a foreseeable
usecase would be a `roles` property which could include values such as `admins` or
`mods`. Defining this in detail is left to a future MSC.

## Alternatives

### Prior proposals

There are a few prior proposals which tackle subsets of the above problem:

* [MSC1796](https://github.com/matrix-org/matrix-spec-proposals/pull/1796):
  extremely similar to the proposal in this MSC, but limited to encrypted events.
* [MSC2463](https://github.com/matrix-org/matrix-spec-proposals/pull/2463):
  excludes searching inside a Matrix ID for localparts / display names of other
  users.
* [MSC3517](https://github.com/matrix-org/matrix-spec-proposals/pull/3517):
  searches for Matrix IDs (instead of display name / localpart) and only searches
  specific event types & properties.
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

The last two proposals use a similar idea of attempting to find "pills" in the
`formatted_body`, this has some downsides though:

* It doesn't allow for hidden mentions, which can be useful in some situations.
* It does not work for event types other than `m.room.message`.

It also adds significant implementation complexity since the HTML messages must
now be parsed for notifications. This is expensive and introduces potential
security issues.

### Room version for backwards compatibility

Alternative backwards compatibility suggestions included using a new room version,
similar to [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932)
for extensible events. This does not seem like a good fit since room versions are
not usually interested in non-state events. It would additionally require a stable
room version before use, which would unnecessarily delay usage.

### Encrypting the `m.mentions` property

Encrypting the `m.mentions` property would solve some unintentional mentions, but
leaving it unencrypted allows for solving a wider range of issues.

Allowing an encrypted `m.mentions` property on a per-message basis could allow users
to choose, but would result in inconsistencies and complications:

* What happens if the cleartext `m.mentions` property does not match the plaintext
  `m.mentions` property?
* Do push rules get processed on both the cleartext and plaintext message?

It may be argued that clients need to decrypt all messages anyway to handle
user-specific keywords. This is a costly process in terms of bandwidth, CPU, and
battery since the client must either receive every message via push notifications
or backpaginate every room fully, in case of a gappy sync.

It is asserted that the use-cases for custom keywords and mentions are sufficiently
different that having different solutions, and different urgencies to receiving
those notifications, is reasonable. In particular, custom keywords is more of a
power-user feature while user mentions working properly (and promptly) is a table-stakes
feature for a messaging application.

## Security considerations

Including the mentioned users in cleartext is a small metadata leak, but we consider that the tradeoff
of mentions working properly and the savings in bandwidth and battery makes it worthwhile.

The additional metadata leaked is minor since the homeserver already knows the
room members, how often users are sending messages, when users are receiving messages
(via read receipts, read markers, and sync), etc. Exposing explicit mentions does not
significantly increase metadata leakage.

## Unstable prefix

During development the following mapping will be used:

| What                | Stable            | Unstable                             |
|---------------------|-------------------|--------------------------------------|
| Event property      | `m.mentions`      | `org.matrix.msc3952.mentions`        |
| Push rule ID        | `.m.rule.*`       | `.org.matrix.msc3952.*`              |

If a client sees this rule available it can choose to apply the custom logic discussed
in the [backwards compatibility](#backwards-compatibility) section.

If a client sees the *stable* identifiers available, they should apply the new
logic and start creating events with the `m.mentions` property.

## Dependencies

This depends on two MSCs which, at the time of writing, have not yet been accepted
into the specification:

* [MSC3758](https://github.com/matrix-org/matrix-spec-proposals/pull/3758): Add `exact_event_match` push rule condition kind
* [MSC3873](https://github.com/matrix-org/matrix-spec-proposals/pull/3873): event_match dotted keys
* [MSC3966](https://github.com/matrix-org/matrix-spec-proposals/pull/3966): `exact_event_property_contains` push rule condition

[^1]: This MSC does not attempt to solve this problem, but [MSC2781](https://github.com/matrix-org/matrix-spec-proposals/pull/2781)
proposes removing reply fallbacks which would solve it. Although as noted in
[MSC3676](https://github.com/matrix-org/matrix-spec-proposals/pull/3676) this
may require landing [MSC3664](https://github.com/matrix-org/matrix-doc/pull/3664)
in order to receive notifications of replies.

[^2]: Note that this MSC does not attempt to solve the problem of edits generating
spurious notifications.

[^3]: It is [defined as](https://spec.matrix.org/v1.5/client-server-api/#mroommessage-msgtypes)
the the "plain text version of the HTML [`formatted_body`] should be provided in the `body`",
but there is no particular algorithm to convert from HTML to plain text *except*
when converting mentions, where the
[plain text version uses the link anchor, not the link](https://spec.matrix.org/v1.5/client-server-api/#client-behaviour-26).

[^4]: As proposed in [issue 353](https://github.com/matrix-org/matrix-spec/issues/353).

[^5]: A new push condition is necessary since none of the current push conditions
(e.g. `event_match`) can process arrays.
