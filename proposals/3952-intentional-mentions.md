# MSC3952: Intentional Mentions

Mentioning other users on Matrix is difficult -- it is not possible to know if
[mentioning a user by display name or Matrix ID](https://github.com/matrix-org/matrix-spec/issues/353)
will count as a mention, but is also too easy to mistakenly mention a user.

(Note that throughout this proposal "mention" is considered equivalent to a "ping"
or highlight notification.)

Some situations that result in unintentional mentions include:

* Replying to a message will re-issue pings from the initial message due to
  [fallback replies](https://spec.matrix.org/v1.5/client-server-api/#fallbacks-for-rich-replies).
  * A user without the power level to send `@room` can abuse this by including
    `@room` in a message and getting a user with the appropriate power levels
    to reply to them.
* Each time a message is edited the new version will be re-evaluated for mentions.
* Mentions occurring [in spoiler contents](https://github.com/matrix-org/matrix-spec/issues/16)
  or [code blocks](https://github.com/matrix-org/matrix-spec/issues/15) are
  evaluated.
* If the [localpart of your Matrix ID is a common word](https://github.com/matrix-org/matrix-spec-proposals/issues/3011)
  then the push rule matching usernames (`.m.rule.contains_user_name`) matches
  too often (e.g. Travis CI matching if your Matrix ID is `@travis:example.org`).
* If the [localpart or display name of your Matrix ID matches the hostname](https://github.com/matrix-org/matrix-spec-proposals/issues/2735)
  (e.g. `@example:example.org` receives notifications whenever `@foo:example.org`
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
  this can result in missed messages. [^1]

There are also some other related bugs:

* Matrix users will append emoji or other unique text in their display names to
  avoid unintentional pings.
* Bridging mentions is suboptimal since they [use display names](https://github.com/matrix-org/matrix-spec/issues/353#issuecomment-1055809364)
  as a workaround, e.g.:
  * It breaks the contract that bridges will not mutate the content of messages.
  * For some protocols, bridges need try to figure out if every message contains
    any of the possible nicknames of room members.
* If a user changes their display name in a room,
  [they might not be mentioned unless the historical display name](https://github.com/matrix-org/matrix-spec/issues/353#issuecomment-1055809372)
  is used while processing push rules.

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

The existing push rules for user and room mentions are deprecated and new rules,
which use a property specific for mentions[^2], are added to make mentions simpler
and more reliable for users.

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

Clients add a Matrix ID to the `user_ids` array whenever composing a message which
includes an intentional mention, such as a ["pill"](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions).
Clients set the `room` value to `true` when making a room-wide announcement. Clients
should also set these values at other times when it is obvious the user intends to explicitly
mention a user.[^3]

The `m.mentions` property is part of the plaintext event body and should be encrypted
into the ciphertext for encrypted events.

### New push rules

Two new default push rule are added:

The `.m.rule.is_user_mention` override push rule would appear directly
before the `.m.rule.contains_display_name` push rule:

```json
{
    "rule_id": ".m.rule.is_user_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_property_contains",
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

The `.m.rule.is_room_mention` override push rule would appear directly
before the `.m.rule.roomnotif` push rule:

```json
{
    "rule_id": ".m.rule.is_room_mention",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_property_is",
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

### Client behavior

The overall user experience is not modified, beyond improving explicitness and
reducing unintended mentions.

For example, it is common that a client will show an event with a mention in a
different color (and denote the current user's "pill", as a way of showing the
user *why* they were mentioned). This behavior is unchanged.

There are two variations that clients should take into account when decorating
messages for mentions, however:

* The presence of a user's "pill" in a message no longer implies it is a mention.
* This makes it easier to mention users without including their "pill" in a
  message (see [Abuse Potential](#abuse-potential) for ideas to combat this).

### Backwards compatibility

The [`.m.rule.contains_display_name`](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules),
[`.m.rule.contains_user_name`](https://spec.matrix.org/v1.5/client-server-api/#default-content-rules),
and [`.m.rule.roomnotif`](https://spec.matrix.org/v1.5/client-server-api/#default-override-rules)
push rules are to be deprecated.

To avoid unintentional mentions these rules are modified to only apply when the
`m.mentions` property is missing; clients should provide at least an empty `m.mentions` property on
every message to avoid the unintentional mentions discussed in the introduction.

A future room version may wish to disable the legacy push rules: clients would
no longer be required to include the `m.mentions` property on every event. It
maybe convenient to do this when extensible events are adopted (see
[MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932)).

After acceptance, it is likely for there to be disagreement about which push rules are
implemented: legacy clients and homeservers may not yet have deprecated the
`.m.rule.contains_display_name`, `.m.rule.contains_user_name`, and `.m.rule.roomnotif`
push rules, while up-to-date clients and homeservers will support the
`.m.rule.is_user_mention` and `.m.rule.is_room_mention` push rules. It is expected
that both sets of push rules will need to be supported for a period of time, but
at worst case should simply result in the current behavior (documented in the preamble).

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

### Impact on replies

Users are notified of replies via the `.m.rule.contains_display_name` or the
`.m.rule.contains_user_name` push rule matching the
[rich reply fallback](https://spec.matrix.org/v1.6/client-server-api/#fallbacks-for-rich-replies).
Unfortunately these push rules will be disabled for events  which contain the
`m.mentions` property, i.e. all newly created events (see
[above](#backwards-compatibility)). It is proposed that clients should include
the sender of the event being replied to as well as any users (except themself)
mentioned in that event in the new event's `m.mentions` property. The `room`
property should not be copied over.

For example, if there is an event:

```json5
{
  "sender": "@dan:example.org",
  "event_id": "$initial_event",
  "content": {
    "body": "Alice: Have you heard from Bob?",
    "m.mentions": {
      "user_ids": ["@alice:example.org", "@bob:example.org"]
    }
  },
  // other fields as required by events
}
```

And a reply from Alice:

```json5
{
  "content": {
    "body": "> <@dan:example.org> Alice: Have you heard from Bob?\n\nNo, but I saw him with Charlie earlier.",
    "m.mentions": {
      "user_ids": [
        // Include the sender of $initial_event.
        "@dan:example.org",
        // The users mentioned, minus yourself.
        "@bob:example.org",
        // New mentions, as normal.
        "@charlie:example.org"
      ]
    },
    "m.relates_to": {
      "m.in_reply_to": {
          "event_id": "$initial_event"
      }
    }
  },
  // other fields as required by events
}
```

This signals that it is the *intention* of the sender to mention all of those people,
clients may wish to allow users to modify the list of people to include, e.g. to
"quote reply" as opposed to replying directly.

If a user wishes to be notified of *all replies* to their messages, other solutions
should be investigated, such as [MSC3664](https://github.com/matrix-org/matrix-spec-proposals/pull/3664).
This would give more equal power to both senders and receivers of events.

### Impact on edits

Similarly to [replies](#impact-on-replies), users are notified of message edits
via the `.m.rule.contains_display_name` or the `.m.rule.contains_user_name` push
rule matching the [fallback content](https://spec.matrix.org/v1.6/client-server-api/#event-replacements).
Generally this is undesirable and users do not need to be notified for the same
message multiple times (e.g. if a user is fixing a typo).

Edited events end up with two `m.mentions` properties:

* One at the top-level of the `content`, this should contain any users to mention
 *for this edit*.
* One inside the `m.new_content` property, which should contain the full list of
  mentioned users in any version of the event.

It is recommended that clients use an empty top-level `m.mentions` property when
editing an event, *unless* the edit is significant or if additional users are
mentioned.

For example, if there is an event:

```json5
{
  "sender": "@dan:example.org",
  "event_id": "$initial_event",
  "content": {
    "body": "Helo Alice!",
    "m.mentions": {
      "user_ids": ["@alice:example.org"]
    }
  },
  // other fields as required by events
}
```

And an edit after realizing that Bob is also in the room:

```json5
{
  "content": {
    "body": "* Hello Alice & Bob!",
    "m.mentions": {
      "user_ids": [
        // Include only the newly mentioned user.
        "@bob:example.org"
      ]
    },
    "m.new_content": {
      "body": "Hello Alice & Bob!",
      "m.mentions": {
        "user_ids": [
          // Include all mentioned users.
          "@alice:example.org",
          "@bob:example.org"
        ]
      },
    },
    "m.relates_to": {
      "rel_type": "m.replace",
      "event_id": "$initial_event"
    }
  },
  // other fields as required by events
}
```

Mentions can also be removed as part of an edit, in this case top-level `m.mentions`
property would not include the removed user IDs (you cannot cancel the notification from
the previous event) or any previously notified users, and the removed user would also be
removed from the `m.new_content` proprerty's copy  of `m.mentions`.

This should limit duplicate, unnecessary notifications for users. If a user wishes
to receive notifications for edits of events they were mentioned in then they
could setup a push rule for the `content.m\\.new_content.m\\.mentions` property
or potentially leverage [MSC3664](https://github.com/matrix-org/matrix-spec-proposals/pull/3664).

### Impact on bridging

For protocols with a similar mechanism for listing mentioned users this should
strengthen the bridging contract as it enables bridges to stop mutating the
content of messages. The bridge should be able to map from the remote user ID
to the bridged user ID and include that in the `m.mentions` property of the
Matrix event & the proper field in the bridged protocol[^4].

For bridged protocols that do not have this mechanism than the bridge will only
be able to stop mutating content on messages bridged *into* Matrix. Messages
bridged out of Matrix will still need to embed the mention into the text
content.[^5]

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
worth sharing. These ideas are not a requirement for implementing this MSC, and
generally do not depend on it. (They could be implemented today with enough effort.)

It was recommended that clients could expose *why* an event has caused a notification
and give users inline tools to combat abuse. For example, a client might show a tooltip:

> The sender of the message (`@alice:example.org`) mentioned you in this event.
>
> Block `@alice:example.org` from sending you messages? `[Yes]` `[No]`

Additionally, if a user sending a message is about to mention many people it can
be useful to confirm whether they wish to do that (or prompt them to do an `@room`
mention instead).

Moderators may find tooling to quickly find messages which mention many users
useful in combating mention spammers. (Note that this should be made easier by
this MSC.)

A future MSC might wish to explore features for trusted contacts or soft-ignores
to give users more control over who can generate notifications.

### Muted except for mentions push rules

It might be desirable to have a "muted-except-for-mentions" feature for large (encrypted)
rooms. This is particularly useful on iOS where a push notification can be decrypted
via a background process but *cannot* be suppressed. This means it is not possible
for the client to handle this feature and it must be handled on the server, unfortunately
this would not be possible with the current proposal since the `m.mentions`
property is encrypted (and the server cannot act on it).

Solving this problem is left to a future MSC.

### Pillifying `@room`

Some clients attempt to create a "pill" out of `@room` mentions, but this is not
a requirement of the Matrix specification. The current [user and rooms mentions](https://spec.matrix.org/v1.5/client-server-api/#user-and-room-mentions)
section could be expanded for this situation.

### Extensible events

Handling of this property in [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)-style
extensible events is deliberately left for a future MSC to address, if needed.

### Role mentions

It is possible to add additional properties to the `m.mentions` object, e.g. a foreseeable
usecase would be a `roles` property which could include values such as `admins` or
`mods`. Defining this in detail is left to a future MSC.

### Cancelling notifications

It maybe useful for a future MSC to investigate cancelling notifications if a
user's mention is removed while [editing events](#impact-on-edits). This could
be quite difficult as it is unclear if the mentioned user has already received
the notification or not.

## Alternatives

### Prior proposals

There are a few prior proposals which tackle subsets of the above problem:

* [MSC1796](https://github.com/matrix-org/matrix-spec-proposals/pull/1796):
  similar to the proposal in this MSC, but limited to encrypted events (and kept
  in cleartext).
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
room version before use, which would unnecessarily delay usage. Another MSC
can address this concern, such as in the extensible events series, if
desirable to be gated by a room version for a "clean slate" approach.

## Security considerations

None not already described.

## Unstable prefix

During development the following mapping will be used:

| What                | Stable            | Unstable                             |
|---------------------|-------------------|--------------------------------------|
| Event property      | `m.mentions`      | `org.matrix.msc3952.mentions`        |
| Push rule ID        | `.m.rule.*`       | `.org.matrix.msc3952.*`              |

The server will include the `org.matrix.msc3952_intentional_mentions` flag in the
`unstable_features` array of the `/versions` endpoint. If a client sees this flag
it can choose to apply the deprecation logic discussed in the
[backwards compatibility](#backwards-compatibility) section.

## Dependencies

This depends on the following (accepted) MSCs:

* [MSC3758](https://github.com/matrix-org/matrix-spec-proposals/pull/3758): Add `event_property_is` push rule condition kind
* [MSC3873](https://github.com/matrix-org/matrix-spec-proposals/pull/3873): event_match dotted keys
* [MSC3966](https://github.com/matrix-org/matrix-spec-proposals/pull/3966): `event_property_contains` push rule condition

<!-- Footnotes below: -->

[^1]: It is [defined as](https://spec.matrix.org/v1.5/client-server-api/#mroommessage-msgtypes)
the the "plain text version of the HTML [`formatted_body`] should be provided in the `body`",
but there is no particular algorithm to convert from HTML to plain text *except*
when converting mentions, where the
[plain text version uses the link anchor, not the link](https://spec.matrix.org/v1.5/client-server-api/#client-behaviour-26).

[^2]: As proposed in [issue 353](https://github.com/matrix-org/matrix-spec/issues/353).

[^3]: Note that this isn't really a change in behavior, it is just making the behavior
explicit. It is expected that users already considered "pilled" users to be mentions,
and it was more unexpected when non-pilled users *were* mentioned. This MSC fixes the
latter case.

[^4]: Some protocols which provide structured data for mentions include
[Twitter](https://developer.twitter.com/en/docs/twitter-api/data-dictionary/object-model/tweet),
[Mastodon](https://docs.joinmastodon.org/entities/Status/#Mention),
[Discord](https://discord.com/developers/docs/resources/channel#message-object),
and [Microsoft Teams](https://learn.microsoft.com/en-us/graph/api/resources/chatmessagemention?view=graph-rest-1.0).

[^5]: Unfortunately some protocols do *not* provide structured data: the message
itself must be parsed for mentions, e.g. IRC or
[Slack](https://api.slack.com/reference/surfaces/formatting#mentioning-users).
