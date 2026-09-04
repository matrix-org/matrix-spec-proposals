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
  non-negative and SHOULD not be larger than 2 minutes. The RECOMMENDED value is 90 seconds.
- `m.mentions`: (optional, object): A [mentions] object to optionally direct the invite at a subset
  of users in the room only. If omitted, the event is not targeted at specific users and may be acted
  upon by any room member.

```json5
{
  "type":"m.rtc.invite",
  "event_id": "$1",
  "content": {
    "slot_id": "m.call#room", // = m.rtc.slot state_key
    "sender_ts": 1784493900000, // July 19, 2026 at 8:45pm UTC
    "lifetime": 90000, // 90s
    "m.mentions": { "user_ids": ["@alice:example.org"] } // Optional
  },
  ...
}
```

The schema of `m.rtc.decline` is as follows:

- `m.relates_to` (required, object): An `m.reference` relation to the `m.rtc.invite` event which is
  being declined.

```json5
{
  "type": "m.rtc.decline",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$1"
    },
  }
}
```

[mentions]: https://spec.matrix.org/v1.19/client-server-api/#user-and-room-mentions

### Receiving invites

A receiving client SHOULD only consider an invite valid as long as all of the following conditions
apply:

- The client's current [push rules] produce an action of `notify` for the event.
- An `m.rtc.slot` event with `state_key = slot_id` and `status = "open"` exists in the room
  where the invite was received.
- The `lifetime`, as measured from `sender_ts` and capped to 2 minutes, has not elapsed. If
  `sender_ts` is more than 20 seconds ahead of `origin_server_ts`, the `lifetime` SHOULD be
  measured from `origin_server_ts` instead. This limits the impact of a malicious user faking
  `sender_ts` to trigger long-lived notifications.
- The client's user ID is included in `m.mentions` (either directly or through a room mention)
  or `m.mentions` is missing.
- The user is not already joined to the same slot via a corresponding `m.rtc.member` event.

If the invite is valid, the receiving client has three options:

1. It can accept the invite by joining the slot with an appropriate `m.rtc.member` event as
   per [MSC4143]. Once the event is observed by other devices of the user, it invalidates the
   invite.
1. It can decline the invite by sending an `m.rtc.decline` event. Again, once the event is
   observed by other devices of the user, it invalidates the invite.
1. It can ignore the event by doing nothing. The invite will remain valid until either
   the user accepts or declines the invite on another device or its `lifetime` has elapsed.

If multiple valid invites for the same slot exist, clients SHOULD only consider the one that
will expire last.

How exactly receiving clients render invites in their UI is left as an implementation detail.
A reasonable choice could, for instance, be to use a ringing UI in [direct chats] and a banner
notification in group chats.

Clients may also tweak their notification UI based on the referenced `m.rtc.slot` event and the
`m.rtc.member` events currently joined to that slot. As an example, a client could choose to only
ring for invites to slots hosting an `m.call` application. Similarly, the client could evaluate
the `intent` property from [MSC4196] to display invites to audio calls differently than invites to
video calls.

[push rules]: https://spec.matrix.org/v1.19/client-server-api/#push-rules
[direct chats]: https://spec.matrix.org/v1.19/client-server-api/#direct-messaging
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196

### Sending invites

Clients MUST send both `m.rtc.invite` and `m.rtc.decline` as sticky events as per [MSC4354] for the
associated delivery guarantee.

In line with the expected behaviour of receiving clients that was outlined in the previous section,
a sending client SHOULD only consider an extended invite valid as long as all of the following
conditions apply:

- An `m.rtc.slot` event with `state_key = slot_id` and `status = "open"` exists in the room
  where the invite was sent.
- The invite's `lifetime` as measured from `sender_ts`, has not elapsed.
- There are targeted room members who have neither accepted the invite (by sending a corresponding
  `m.rtc.member` event) nor declined it (by sending an `m.rtc.decline` event).

To prevent duplicate invitations, senders SHOULD NOT emit invites when another valid invite exists
for the same slot.

Again, how exactly sending clients present extended invitations in their UI is left as an
implementation detail. Similar to the examples previously given for receiving clients, a
sending client could use a ringing UI in [direct chats], for instance.

[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354

### Push rules

In order to allow clients to manage their notification settings for MatrixRTC invites, a new default
[underride] push rule `.m.rule.rtc` is introduced that matches any incoming `m.rtc.invite` event.

```json5
{
  "rule_id": ".m.rule.rtc",
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

`.m.rule.rtc` is inserted directly after the existing `.m.rule.call` rule.

[underride]: https://spec.matrix.org/v1.19/client-server-api/#default-underride-rules

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

## Appendix: Comparison to [legacy VoIP]

| Feature | Legacy VoIP | MatrixRTC |
| ------- | ----------- | --------- |
| Session invites | ✅ via [`m.call.invite`] events | ✅ via `m.rtc.invite` events |
| Directing invites at specific users | ✅ via `invitee` on [`m.call.invite`] | ✅ via `m.mentions` on `m.rtc.invite` |
| Expiring invites | ⚠️ via `lifetime` on [`m.call.invite`] evaluated against [`age`] which is known to be broken in various homeservers | ✅ via `lifetime` on `m.rtc.invite` evaluated against either `sender_ts` or `origin_server_ts` |
| Invite without starting a call | ❌ Not possible | ✅ Explicitly allowed if an open slot exists |
| Declining invites | ✅ via [`m.call.hangup`] events | ✅ via `m.rtc.decline` events |
| Managing notification settings | ✅ via `.m.rule.call` push rule | ✅ via `.m.rule.rtc` push rule |
| Events required to validate session invites | ✅ 1 ([`m.call.invite`]) | ⚠️ 2 (`m.rtc.slot` and `m.rtc.invite`; since `m.rtc.slot` is a state event both can be fetched in the same `/sync`, however ) |

[`m.call.invite`]: https://spec.matrix.org/v1.19/client-server-api/#mcallinvite
[`age`]: https://spec.matrix.org/v1.19/client-server-api/#call-event-liveness
[`m.call.hangup`]: https://spec.matrix.org/v1.19/client-server-api/#mcallhangup

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.invite` | Event type | `org.matrix.msc4075.rtc.invite` |
| `m.rtc.decline` | Event type | `org.matrix.msc4075.rtc.decline` |
| `.m.rule.rtc` | Push rule ID | `.org.matrix.msc4075.rule.rtc` |

## Dependencies

This proposal depends on [MSC4143] and [MSC4354].
