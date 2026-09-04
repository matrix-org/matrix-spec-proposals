# MSC4075: MatrixRTC invites and notifications

[MSC4143] introduces MatrixRTC as an extensible framework for real-time communication in Matrix.
MatrixRTC sessions are formed around `m.rtc.slot` state events to which users join by sending
`m.rtc.member` room events.

This proposal introduces a scheme for notifying users about MatrixRTC sessions. The goal explicitly
is to construct a minimal solution that achieves feature parity with notifications in [legacy VoIP]
and doesn't design out future improvements. This is achieved by mediating notifications via dedicated
room events that prompt recipients to join a MatrixRTC session. Invites can be accepted by joining
the session with an appropriate `m.rtc.member` event, declined by sending a dedicated decline event
or ignored entirely. Under this model, notifications are agnostic of the particular MatrixRTC
application, yet form a solid foundation for future extension.

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[legacy VoIP]: https://spec.matrix.org/v1.19/client-server-api/#voice-over-ip

## Proposal

Two new room events `m.rtc.invite` and `m.rtc.decline` are introduced. These events can be sent by
clients to prompt other users to join a MatrixRTC session and to reject a received invitation, respectively.

The schema of `m.rtc.invite` is as follows:

- `slot_id` (required, string): The `state_key` of the `m.rtc.slot` event for which the invite is
  handed out.
- `sender_ts` (required, integer): The timestamp (in milliseconds since the epoch) when the sending
  client created the event.
- `lifetime` (required, integer): The time in milliseconds that the invite is valid for. MUST be
  non-negative and SHOULD NOT be larger than 2 minutes. The RECOMMENDED value is 90 seconds.
- `m.mentions`: (optional, object): A [mentions] object to optionally direct the invite at a set
  of users in the room. If omitted or empty, the event is not targeted at specific users and may
  be acted upon by any room member.
- `sticky_key` (required, string): The event's sticky key as per [MSC4354]. MUST be equal to `slot_id`.
  This ensures that receivers only maintain one active invite per slot and sender.

```json5
{
  "type":"m.rtc.invite",
  "event_id": "$1",
  "content": {
    "slot_id": "m.call#room", // = m.rtc.slot state_key
    "sender_ts": 1784493900000, // July 19, 2026 at 8:45pm UTC
    "lifetime": 90000, // 90s
    "m.mentions": { "user_ids": ["@alice:example.org"] }, // Optional
    "sticky_key": "m.call#room", // = slot_id
  },
  ...
}
```

The schema of `m.rtc.decline` is as follows:

- `m.relates_to` (required, object): An `m.reference` relation to the `m.rtc.invite` event which is
  being declined.
- `sticky_key` (required, string): The events sticky key as per [MSC4354]. MUST be equal to the
  event ID of the event that is being declined.

```json5
{
  "type": "m.rtc.decline",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$1"
    },
    "sticky_key": "$1"
  }
}
```

Clients MUST send both `m.rtc.invite` and `m.rtc.decline` as sticky events as per [MSC4354] for the
associated delivery guarantee. The sticky duration for `m.rtc.invite` events SHOULD NOT be smaller
than the invite's `lifetime`. The sticky duration for `m.rtc.decline`, in turn, SHOULD NOT be smaller
than the declined invite's sticky duration. Additionally, clients MUST implement the ephemeral map
algorithm as per [MSC4354] to construct a state-like store of both invite and decline events.

[mentions]: https://spec.matrix.org/v1.19/client-server-api/#user-and-room-mentions
[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354

### Sending invites

Both `m.rtc.invite` and `m.rtc.decline` MUST be sent encrypted when the room is encrypted.

A sending client SHOULD only consider an extended invite valid as long as all of the following
conditions apply:

- An `m.rtc.slot` event with `state_key = slot_id` and `status = "open"` exists in the room
  where the invite was sent.
- The invite's `lifetime`, as measured from `sender_ts` and capped at 2 minutes, has not elapsed.
- There are targeted room members who have neither accepted the invite (by sending a corresponding
  `m.rtc.member` event) nor declined it (by sending an `m.rtc.decline` event).

To prevent duplicate invitations, senders SHOULD NOT emit invites when another valid invite exists
for the same slot and the same set of targeted users.

An existing invite MAY be withdrawn by sending another `m.rtc.invite` event with the same `sticky_key`
and an otherwise empty content and the same or a larger sticky duration. Alternatively, the event
MAY also be redacted which will remove it from the ephemeral map of sticky events.

How exactly sending clients present extended invitations in their UI is left as an implementation
detail. For instance, a sending client could use a ringing UI in [direct chats] while it is waiting
for the invite to be acted on and stop ringing when the invite is accepted or declined (see the next
section).

### Receiving invites

In line with the expected behaviour of sending clients that was outlined in the previous section,
a receiving client SHOULD only consider an invite valid as long as all of the following conditions
apply:

- The invite is the current invite entry in the ephemeral sticky events map for the sender
  and slot and not a withdrawal (that is, an invite event whose `content` is empty except
  for `sticky_key`).
- The client's current [push rules] produce an action of `notify` for the event.
- An `m.rtc.slot` event with `state_key = slot_id` and `status = "open"` exists in the room
  where the invite was received.
- The `lifetime`, as measured from `sender_ts` and capped to 2 minutes, has not elapsed. If
  `sender_ts` is more than 20 seconds ahead of `origin_server_ts`, the `lifetime` SHOULD be
  measured from `origin_server_ts` instead. This limits the impact of a malicious user faking
  `sender_ts` to trigger long-lived notifications.
- `m.mentions` is either empty, missing or contains the client's user ID (either directly or
  through a room mention).
- The user is not already joined to the same slot via a corresponding `m.rtc.member` event.

If the invite is valid, the receiving client has three options:

1. It can accept the invite by joining the slot with an appropriate `m.rtc.member` event as
   per [MSC4143]. Once the event is observed by other devices of the user, it invalidates the
   invite.
1. It can decline the invite by sending an `m.rtc.decline` event. Again, once the event is
   observed by other devices of the user, it invalidates the invite.
1. It can ignore the event by doing nothing. The invite will remain valid until either
   the user accepts or declines the invite on another device or its `lifetime` has elapsed.

If multiple valid invites for the same slot exist, clients SHOULD only consider the one whose
`lifetime` will expire last.

Again, how exactly receiving clients render invites in their UI is left as an implementation
detail. A reasonable choice could, for instance, be to use a ringing UI in [direct chats] and
a banner notification in group chats.

Clients may also tweak their notification UI based on the referenced `m.rtc.slot` event and the
`m.rtc.member` events currently joined to that slot. As an example, a client could choose to only
ring for invites to slots hosting an `m.call` application. Similarly, the client could evaluate
the `intent` property from [MSC4196] to display invites to audio calls differently than invites to
video calls.

[push rules]: https://spec.matrix.org/v1.19/client-server-api/#push-rules
[direct chats]: https://spec.matrix.org/v1.19/client-server-api/#direct-messaging
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196

### Push rules

In order to allow clients to manage their notification settings for MatrixRTC invites, three new default
push rules are introduced.

`.m.rule.rtc.invite_for_me` matches `m.rtc.invite` events which contain the user's Matrix ID in
the list of `user_ids` under `m.mentions`.

```json5
{
  "rule_id": ".m.rule.rtc.invite_for_me",
  "default": true,
  "enabled": true,
  "conditions": [{
    "kind": "event_match",
    "key": "type",
    "pattern": "m.rtc.invite"
  }, {
    "kind": "event_property_contains",
    "key": "content.m\\.mentions.user_ids",
    "value": "[the user's Matrix ID]"
  }],
  "actions": ["notify", {
    "set_tweak": "sound",
    "value": "ring"
  }]
}
```

`.m.rule.rtc.invite_for_room` matches `m.rtc.invite` events with the `room` property of `m.mentions`
set to `true` (provided that the sender has the proper power level to trigger `@room` notifications).

```json5
{
  "rule_id": ".m.rule.rtc.invite_for_room",
  "default": true,
  "enabled": true,
  "conditions": [{
    "kind": "event_match",
    "key": "type",
    "pattern": "m.rtc.invite"
  }, {
    "kind": "event_property_is",
    "key": "content.m\\.mentions.room",
    "value": true
  }, {
    "kind": "sender_notification_permission",
    "key": "room"
  }],
  "actions": ["notify", {
    "set_tweak": "sound",
    "value": "ring"
  }]
}
```

Finally, `.m.rule.rtc.invite` matches any `m.rtc.invite` event.

```json5
{
  "rule_id": ".m.rule.rtc.invite",
  "default": true,
  "enabled": true,
  "conditions": [{
    "key": "type",
    "kind": "event_match",
    "pattern": "m.rtc.invite"
  }],
  "actions": ["notify", {
    "set_tweak": "sound",
    "value": "ring"
  }]
}
```

The rules are inserted into the existing default rule set as follows:

- `.m.rule.rtc.invite_for_me` is inserted as an [`override`] rule before `.m.rule.is_user_mention`.
- `.m.rule.rtc.invite_for_room` is inserted as an [`override`] rule before `.m.rule.is_room_mention`.
- `.m.rule.rtc.invite` is inserted as an [`underride`] rule before `.m.rule.call`.

The rules and their placement are designed to fit in with the common push rule configurations for setting
rooms to muted or mentions-only.

Muting is usually implemented via a user-defined `override` rule with empty `actions`. This overrides all
three rules and silences any notifcation for `m.rtc.invite` events.

Mentions-only rooms are commonly implemented via a `room`-kind rule with empty `actions`. The override
rules `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` are processed before such a rule.
As a result, `m.rtc.invite` events that include the user in `m.mentions` still cause notifications.
The `.m.rule.rtc.invite` underride rule, however, is processed after the `room`-kind rule. Consequently,
`m.rtc.invite` events with empty or no `m.mentions` don't cause notifications. This behaviour is
analogous to normal messages with `m.mentions`.

Furthermore, the placement of `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` before
`.m.rule.is_user_mention` and `.m.rule.is_room_mention` means that invites that target the user via
`m.mentions` can be muted by setting empty `actions` on these rules.

Finally, in rooms that are neither set to muted nor mentions-only, `m.rtc.invite` events with `m.mentions`
notify if the user is validly targeted via the event's `m.mentions` (via one of the two override rules)
and also if the event has no or empty `m.mentions` (via the underride rule).

| Push rule configuration | Invite with room mention | Invite with user mention | Invite without mention |
| ----------------------- | ------------------------ | ------------------------ | ---------------------- |
| Default | ✅ Notifies | ✅ Notifies | ✅ Notifies |
| Mentions-only | ✅ Notifies | ✅ Notifies | ❌ Silent |
| Muted | ❌ Silent | ❌ Silent | ❌ Silent |

Note that in encrypted rooms, the server cannot apply any of the above rules because `m.rtc.invite`
events will be encrypted. In this case, clients need to reapply push rules after decrypting themselves.
This is already the case for other events and push rules.

[`override`]: https://spec.matrix.org/v1.19/client-server-api/#default-override-rules
[`underride`]: https://spec.matrix.org/v1.19/client-server-api/#default-underride-rules

## Potential issues

### Lack of application-specific notifications

This proposal deliberately only covers generic session invites and notifications. Some MatrixRTC
applications might have a need for application specific notification mechanisms though. For instance,
a calling application might want to provide hints for the ringing behaviour in the invite. This
could easily be added on top of this proposal by allowing application specific metadata in a dedicated
`application` object inside of `m.rtc.invite` events. Doing so is left as a task for a future proposal
which can use this MSC as a foundation.

### Lack of feedback

As mentioned above, a ringing UX can be a reasonable choice in certain situations. This proposal
doesn't provide sending clients with a way to know whether their invite is actually ringing
the recipient, however. This could be desirable in order to create an experience akin to classical
phone calls. A future proposal may address this gap, for instance, by introducing ringing
acknowledgements communicated via to-device messages or by designing a more general event delivery
receipt mechanism.

### Lack of push notifications in encrypted mentions-only rooms

In encrypted rooms, the server can see neither the actual type of events nor their `m.mentions`. As a
result, invite events will erroneously be caught by the `room`-kind push rule that is needed to implement
mentions-only rooms which means they don't cause push notifications on mobile clients. As a result,
`m.rtc.invite` notifications can be significantly delayed on mobile clients. This problem is not unique
to MatrixRTC invites and [MSC4028] is an ongoing attempt at solving it generally.

[MSC4028]: https://github.com/matrix-org/matrix-spec-proposals/pull/4028

## Alternatives

### Inferring notifications from membership events

Instead of using dedicated `m.rtc.invite` and `m.rtc.decline` events, invites and declines could also
be inferred from `m.rtc.member` events. Adding the required metadata to these events would likely
overload them though. In comparison, the standalone events introduced in this proposal are more
explicit and form a better foundation for future extensions.

## Security considerations

### Inviting without a valid `m.rtc.member` event

Under this proposal, the sender of `m.rtc.invite` events does not need to be joined to the slot
themselves in order to make the invite valid. This may seem like a potential abuse vector. However,
room members who are able to send `m.rtc.invite` events will commonly also be able to send
`m.rtc.member` events. Thus requiring a member event to send invites doesn't provide additional
protection. The actual access control for sending invites is the power level for sending
`m.rtc.invite` events which room administrators can raise as needed. When power levels allow
sending invitations, users can still mitigate abusive invites by configuring push rules accordingly.

Besides this, requiring the sender to have an `m.rtc.member` event also complicates invite processing.
Particularly on mobile, it would mean that after receiving a push notification, the client would
have to fetch a state event and two different room events, including the information required to
decrypt them, in order to validate the invite. This significantly increases the chance to run into
time limits applied to notification processing by mobile operating systems. While it's possible
to mitigate this by processing invites optimistically while they're being validated in the
background, this introduces further abuse risks.

Lastly, being able to invite users into a MatrixRTC session without being joined oneself, also
acts as a feature and enables integrations such as meeting bots to issue invites without having
to support MatrixRTC themselves.

### Inflating `sender_ts` and/or `lifetime`

A malicious client could send invites with a fake `sender_ts` that lies in the future and/or a
large `lifetime` in an attempt to cause receiving clients to notify or ring their users for extended
periods of time. This is mitigated by the recommendations given earlier, in particular the maximum
allowed difference of 20 seconds between `sender_ts` and `origin_server_ts` and the maximum allowed
`lifetime` of 2 minutes.

### Room-level invites

Using room mentions on `m.rtc.invite` events will notify all users in a room. This has the same
potential for abuse as room mentions on normal messages and can be mitigated by increasing the
power level required to send room notifications.

### Repeated invites

Senders can issue a new invite after a previous invite was declined. This can be abusive. Users can
mitigate this by adapting their push rules, [ignoring] the sender or leaving the room.

[ignoring]: https://spec.matrix.org/v1.18/client-server-api/#ignoring-users

## Appendix: Comparison to [legacy VoIP]

| Feature | Legacy VoIP | MatrixRTC |
| ------- | ----------- | --------- |
| Session invites | ✅ via [`m.call.invite`] events | ✅ via `m.rtc.invite` events |
| Directing invites at specific users | ✅ via `invitee` on [`m.call.invite`] | ✅ via `m.mentions` on `m.rtc.invite` |
| Expiring invites | ⚠️ via `lifetime` on [`m.call.invite`] evaluated against [`age`] which is known to be broken in various homeservers | ✅ via `lifetime` on `m.rtc.invite` evaluated against either `sender_ts` or `origin_server_ts` |
| Inviting without starting a call | ❌ Not possible | ✅ Explicitly allowed if an open slot exists |
| Withdrawing invites | ✅ via [`m.call.hangup`] events | ✅ via empty `m.rtc.invite` events |
| Declining invites | ✅ via [`m.call.hangup`] events | ✅ via `m.rtc.decline` events |
| Notifications in default rooms | ✅ via `.m.rule.call` push rule | ✅ via `.m.rule.rtc.invite_for_me`, `.m.rule.rtc.invite_for_room` or `.m.rule.rtc.invite` push rules |
| Notifications in mentions-only rooms | ❌ Not possible | ✅ via `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` push rules |
| Events required to validate session invites | ✅ 1 ([`m.call.invite`]) | ⚠️ 2 (`m.rtc.slot` and `m.rtc.invite`; since `m.rtc.slot` is a state event both can be fetched in the same `/sync`, however) |

[`m.call.invite`]: https://spec.matrix.org/v1.19/client-server-api/#mcallinvite
[`age`]: https://spec.matrix.org/v1.19/client-server-api/#call-event-liveness
[`m.call.hangup`]: https://spec.matrix.org/v1.19/client-server-api/#mcallhangup

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.invite` | Event type | `org.matrix.msc4075.rtc.invite` |
| `m.rtc.decline` | Event type | `org.matrix.msc4075.rtc.decline` |
| `.m.rule.rtc.invite_for_me` | Push rule ID | `.org.matrix.msc4075.rule.rtc.invite_for_me` |
| `.m.rule.rtc.invite_for_room` | Push rule ID | `.org.matrix.msc4075.rule.rtc.invite_for_room` |
| `.m.rule.rtc.invite` | Push rule ID | `.org.matrix.msc4075.rule.rtc.invite` |

## Dependencies

This proposal depends on [MSC4143] and [MSC4354].
