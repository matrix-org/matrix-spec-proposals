# MSC4075: MatrixRTC invites and notifications

[MSC4143] introduces MatrixRTC as an extensible framework for real-time communication in Matrix.
MatrixRTC sessions are formed around `m.rtc.slot` state events to which users join by sending
`m.rtc.member` room events.

This proposal introduces a scheme for notifying users about MatrixRTC sessions. The goal explicitly
is to construct a minimal solution that achieves feature parity with notifications in [legacy VoIP]
and doesn't design out future improvements. This is achieved by mediating notifications via dedicated
room events that invite recipients to join a MatrixRTC session. Invites can be accepted by joining
the session with an appropriate `m.rtc.member` event, declined by sending a dedicated decline event
or ignored entirely. Invites also delimit calls: a call starts with an invite and ends when it is
declined, cancelled, expires unanswered or, once answered, is hung up, and each of these endings is
signalled distinctly. The invite's event ID serves as the call ID, and when invites to the same slot
cross, a deterministic tie-break settles which call they belong to. Under this model, notifications
are agnostic of the particular MatrixRTC application, yet form a solid foundation for future extension.

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[legacy VoIP]: https://spec.matrix.org/v1.19/client-server-api/#voice-over-ip

## Proposal

Two new [sticky][MSC4354] room events, `m.rtc.invite` and `m.rtc.decline`, are introduced. These
events can be sent by clients to prompt other users to join a MatrixRTC session and to reject a
received invitation, respectively.

The schema of `m.rtc.invite` is as follows:

- `slot_id` (required, string): The `state_key` of the `m.rtc.slot` event for which the invite is
  handed out.
- `sender_ts` (required, integer): The timestamp (in milliseconds since the Unix epoch) when the sending
  client created the event.
- `lifetime` (required, integer): The time in milliseconds that the invite is active for. MUST be
  non-negative and SHOULD NOT be larger than 2 minutes. The RECOMMENDED value is 90 seconds.
- `m.mentions`: (required, object): A [mentions] object to direct the invite at either a set
  of users in the room or the entire room. One of the two options MUST be used. An `m.mentions`
  object with both `room` missing or set to false and `user_ids` missing or empty makes the
  `m.rtc.invite` event invalid.
- `sticky_key` (required, string): The event's sticky key as per [the addendum of MSC4354]. MUST be
  equal to `slot_id`. This ensures that receivers only maintain one active invite per slot and sender.
- `call_id` (optional, string): The ID of the call that this invite invites into (see [calls]). MUST
  be absent on an invite that starts a call.
- `withdraw_reason` (optional, object): Only valid on a withdrawal (see [sending invites]). Why the
  invite was withdrawn. Mirrors `leave_reason` on `m.rtc.member` in [MSC4143].
  - `code` (required, string): `cancelled` if the inviter gave up on the call, or `glare` if the
    invite lost a tie-break (see [crossing invites]). Receivers MUST treat a withdrawal without
    `withdraw_reason`, and any `code` they do not recognise, as `cancelled`.
  - `reason` (optional, string): Human-readable detail for diagnostics. Clients MAY display it but
    MUST NOT interpret it.

```json5
{
  "type":"m.rtc.invite",
  "event_id": "$1",
  "content": {
    "slot_id": "m.call#room", // = m.rtc.slot state_key
    "sender_ts": 1784493900000, // July 19, 2026 at 8:45pm UTC
    "lifetime": 90000, // 90s
    "m.mentions": { "user_ids": ["@alice:example.org"] },
    "sticky_key": "m.call#room", // = slot_id
  },
  ...
}
```

The schema of `m.rtc.decline` is as follows:

- `m.relates_to` (required, object): An [`m.reference` relation] to the `m.rtc.invite` event which is
  being declined.
- `sticky_key` (required, string): The event's sticky key as per [MSC4354]. MUST be equal to the
  event ID of the `m.rtc.invite` event that is being declined.
- `decline_reason` (optional, object): Why the invite was declined. Mirrors `leave_reason` on
  `m.rtc.member` in [MSC4143], which covers why a member left after joining, whereas this covers why
  a user never joined.
  - `code` (required, string): `declined` if the user chose not to answer, or `busy` if the user is
    already in another call and does not want to be disturbed. Further proposals MAY define more
    codes. Receivers MUST treat a decline without `decline_reason`, and any `code` they do not
    recognise, as `declined`.
  - `reason` (optional, string): Human-readable detail for diagnostics. Clients MAY display it but
    MUST NOT interpret it.

```json5
{
  "type": "m.rtc.decline",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$1"
    },
    "sticky_key": "$1",
    "decline_reason": { "code": "busy" }
  }
}
```

`busy` is an explicit choice, as `user_busy` is in [legacy VoIP]: a client SHOULD NOT decline new
invites with `busy` merely because its user is in another call, unless the user has asked it to.

Clients MUST send both `m.rtc.invite` and `m.rtc.decline` as sticky events as per [MSC4354] for the
associated delivery guarantee. The sticky durations of `m.rtc.invite` events, `m.rtc.member` events
which accept an invite, or `m.rtc.decline` events which decline an invite SHOULD NOT be smaller than
the invite's `lifetime`. Additionally, clients MUST implement the ephemeral map algorithm as per
[MSC4354] to construct a state-like store of `m.rtc.invite` and `m.rtc.decline` events.

Additionally, both `m.rtc.invite` and `m.rtc.decline` MUST be sent encrypted when the room is encrypted.

[mentions]: https://spec.matrix.org/v1.19/client-server-api/#user-and-room-mentions
[the addendum of MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/blob/kegan/persist-edu/proposals/4354-sticky-events.md#implementing-an-ephemeral-map
[`m.reference` relation]: https://spec.matrix.org/v1.19/client-server-api/#reference-relations
[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354
[sending invites]: #sending-invites
[calls]: #calls
[invite activeness]: #invite-activeness
[crossing invites]: #crossing-invites

### Invite activeness

For a particular user, an invite event is in exactly one of two states at any time: active or inactive.
Active invites are "live" and MAY be acted upon by either senders or receivers whereas inactive invites
SHOULD be ignored. Note that the view onto the state of an invite can differ between senders and receivers
depending on what users the invite was targeted at and which of these users have already acted upon the
invite.

In order to define the rules for when an invite is considered active, we first need to formalise the
requirements for being targeted by an invite and having acted on it.

A user receiving an `m.rtc.invite` event is targeted by the invite if and only if all of the following
conditions apply:

- The `sender` is not the same user as the recipient.
- `m.mentions` either contains the receiving user in `user_ids` or has `room` set to `true` (and the sender
  has sufficient power level to trigger a `room` notification at the time the invite is received[^mentions-pl]).

If a user was targeted by an invite it may act on it by either accepting or declining the invite. Furthermore,
if the user accepts the invite, they can later leave the session again which must not reactivate the invite.
Therefore, a user that was targeted by an invite has _not_ yet acted on the invite if and only if all of
the following requirements are met:

- There is no `m.rtc.member` event sent by the user in the ephemeral sticky events map that has a membership
  of `join` for the slot.
- If there is an `m.rtc.member` event sent by the user in the ephemeral sticky events map that has a
  membership of `leave` for the slot, its `origin_server_ts` is less than the `origin_server_ts` of the
  invite event.
- There is no `m.rtc.decline` event sent by the user in the ephemeral sticky events map that references the
  invite event.

Given these definitions, the following requirements MUST hold for clients to consider an invite active:

- An `m.rtc.slot` event with `state_key = slot_id` and `status = "open"` exists in the state of the
  room where the invite was sent.
- The `lifetime` of the invite, as measured from `sender_ts`, has not elapsed. If `sender_ts` is later
  than `origin_server_ts`, the `lifetime` SHOULD be measured from `origin_server_ts` instead. This
  limits the impact of a malicious user faking `sender_ts` to trigger long-lived notifications.
  Regardless of the basis for measuring, the remaining lifetime MUST be capped at 2 minutes.
- The invite is the current invite entry in the ephemeral sticky events map for the sender
  and slot, and is not a withdrawal (that is, an invite event whose `content` is empty except
  for `sticky_key` and, optionally, `withdraw_reason`).
- The invite has not lost a tie-break against another invite (see [crossing invites]).
- If the client is the receiver of the invite:
  - The client's current user is targeted by the invite but has not yet acted on it (as per the definitions
    above).
- If the client is the sender of the invite:
  - There are targeted room members who have not yet acted on the invite (as per the definitions above).

If any of these conditions is not met, clients MUST consider the invite inactive.

### Sending invites

To prevent duplicate invitations, senders SHOULD NOT emit invites when another active invite exists
for the same slot and the same set of targeted users. Additionally, clients MAY emit invites automatically
when joining a slot but SHOULD only do so when no other user is currently joined to the slot.

An existing invite MAY be withdrawn by sending another `m.rtc.invite` event with the same `sticky_key`,
an otherwise empty content (apart from an optional `withdraw_reason`) and the same or a larger sticky
duration. Alternatively, the event MAY also be redacted which will remove it from the ephemeral map of
sticky events. A redacted invite counts as withdrawn with `cancelled`.

To prevent stale invitations, clients SHOULD withdraw previously sent invitations, with `cancelled`,
when the slot is closed or when the inviter themselves leaves the slot with no other members currently
joined to the slot.

How exactly sending clients present issued invitations in their UI is left as an implementation
detail. For instance, a sending client could use a ringing UI in [direct chats] while it is waiting
for the invite to be acted on and stop ringing when the invite is accepted, declined (see the next
section) or expires.

### Receiving invites

The conditions for invite activeness outlined above, in effect, mean that when an active invite comes
in, the receiving client has three options:

1. It can accept the invite by joining the slot with an appropriate `m.rtc.member` event as
   per [MSC4143]. The invite is inactivated due to the presence of a sticky join event.
1. It can decline the invite by sending an `m.rtc.decline` event. Again, the invite is inactivated
   due to the presence of a sticky decline event.
1. It can ignore the event by doing nothing. The invite will remain active until either
   the user accepts or declines the invite on another device or its `lifetime` has elapsed.

If several invites to a given slot are active at the same time, they either invite into the same
call or cross each other. Receivers SHOULD present only one of them, as described under [calls] and
[crossing invites].

Again, how exactly receiving clients render invites in their UI is left as an implementation
detail. A reasonable choice could, for instance, be to use a ringing UI in [direct chats] and
a banner notification in group chats.

Clients may also tweak their notification UI based on the referenced `m.rtc.slot` event and the
`m.rtc.member` events currently joined to that slot. As an example, a client could choose to only
ring for invites to slots hosting an `m.call` application. Similarly, the client could evaluate
the `intent` property from [MSC4196] to display invites to audio calls differently than invites to
video calls.

[direct chats]: https://spec.matrix.org/v1.19/client-server-api/#direct-messaging
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196

### Calls

[MSC4143] defines a session as the span of time during which a changing set of members is
continuously joined to a slot, and deliberately defines no identifier for it. Sessions say who was
connected, but not why: they don't record that somebody rang somebody else, whether they answered,
or how it ended. This proposal calls that a call.

A call starts with an invite and ends when it is declined, cancelled or expires unanswered, or, once
answered, when it is hung up. Calls and sessions are separate concepts over the same memberships. A
call may begin before anyone has joined the slot and end without anyone ever joining it, in which
case it has no session at all. A session may contain several calls, as when a further user is rung
into a running call, or none, as when members simply join a slot without inviting anybody.

A call is identified by its call ID, which is the event ID of the invite that started it. Senders
set `call_id` on every invite into a call they know to be running, such as when ringing a further
user into it, so normally exactly one invite without `call_id` exists per call. Several exist only
when invites cross, as described under [crossing invites]. Concretely, the call ID is the event ID
that sorts first, when compared as Unicode code points, among the invites without `call_id` sent
for the call. Sessions in which nobody is invited have no call and so no call ID, as in [MSC4143].

Members and their media are attributed to a call by timing: a member belongs to the calls that are
running while it is joined. No new property on `m.rtc.member` is needed. Declines, withdrawals and
any future events that reference an invite are attributed to a call through the invite they reference.

None of this affects media. Transports connect the members of a slot as per [MSC4143] regardless of
which invite, if any, brought them there. Calls are a labelling over memberships that already exist,
for use by call history, call data records, bridges and future signalling that needs to refer to a
particular call.

### Ending a call

A call is answered as soon as a targeted user has acted on its invite by being joined to the slot
(see [invite activeness]), including a user who was already joined when the invite was sent. For each
targeted user, the outcome of the invite is exactly one of the following, with events signalling
each outcome distinctly:

| Outcome | Signalled by |
| ------- | ------------ |
| Answered | A joining `m.rtc.member` event from the targeted user. If a device other than the current one sent it, the call was answered elsewhere. |
| Declined | `m.rtc.decline` with `decline_reason.code` `declined`, or no `decline_reason` |
| Busy | `m.rtc.decline` with `decline_reason.code` `busy` |
| Cancelled | A withdrawal of the invite with `withdraw_reason.code` `cancelled`, or no `withdraw_reason`, or a redaction |
| Merged by glare | A withdrawal of the invite with `withdraw_reason.code` `glare` (see [crossing invites]) |
| Not answered | Nothing: the invite's `lifetime` elapsed |
| Slot closed | The `m.rtc.slot` event no longer has `status` `open` |

A call that has not been answered ends when its invite is inactive for every targeted user. A call
that has been answered ends with the session it was answered in, that is, when no member is joined
to the slot any more. Each member's departure is signalled by its leaving `m.rtc.member` event with
the `leave_reason` of [MSC4143]: `leave` for hanging up, `delayed_leave` for a lost connection and
`slot_closed` for the slot closing.

Whether an outcome is local or remote follows from the sender of the event that signalled it. If
it is the client's own user, on this device or another, the outcome is local. Otherwise it is
remote. A client can therefore tell, for instance, its user hanging up from the other party hanging
up, the other party declining from its own user declining on another device, and the caller
cancelling from the invite expiring.

A call with exactly one targeted user is a two-party call, the common case in direct chats. When
the other party leaves such a call, the remaining client SHOULD treat the call as ended and leave the
slot itself, with `leave_reason` `leave`, unless its user chooses to stay. This gives two-party
calls the same behaviour as in [legacy VoIP], where either party hanging up ends the call.

### Crossing invites

Two users may call each other, or several users may invite the room, in the same slot at about the
same time, each before having seen the others' invites. This is glare. Each sender believes it is
starting a call and so sends an invite without `call_id`. As [MSC4143] notes, membership is
conflict-free, so glare cannot break media: every sender can join the slot and their transports
connect as usual. What needs resolving is purely at the signalling layer: which invite identifies
the call, and which invite receivers act on.

By the rule under [calls], all such invites belong to one call and the one whose event ID sorts first
identifies it. That invite wins, the others lose, and the following applies:

- The sender of a losing invite SHOULD withdraw it with `withdraw_reason.code` `glare`. If it is
  targeted by the winning invite, it SHOULD accept the winning invite on behalf of its user, by
  joining the slot unless already joined. Its user has evidently chosen to be in this call.
- Receivers MUST consider losing invites inactive and SHOULD present only the winning invite, whether
  or not the withdrawal has arrived yet.
- An invite whose `call_id` names a losing invite invites into the winner's call.
- Members already joined to the slot stay joined. Nothing is torn down or renegotiated, and media
  that is already flowing is not interrupted.

As every client applies the same comparison to the same event IDs, they agree on the outcome without
further signalling. The withdrawal exists for receivers that have only seen the losing invite so far.
This is the same resolution that [legacy VoIP glare] uses, with the invite's event ID in place of
`call_id`, except that no call is hung up.

[legacy VoIP glare]: https://spec.matrix.org/v1.19/client-server-api/#glare

### Exemplary invite flows

To visualise how event stickiness, the rules for invite activeness and actions taken on invites
play together, a few examples are provided below. Note that, as mentioned before, the sticky
duration of both invite events and events which react to invites SHOULD exceed the invite's
`lifetime`. Additionally, the sticky duration of a leaving `m.rtc.member` event MUST be large
enough to replace the corresponding joining member event in the sticky map as per [MSC4354].
As a result, joins, leaves and declines always exceed the invite's `lifetime` which ensures
that inactivated invites cannot be reactivated.

All examples below use the following legend:

```
[===]: Event is the current one in the sticky map
[xxx]: Event is not the current one anymore
[###]: Invite is considered active
```

#### Example 1: User accepts invite, then leaves again

```
m.rtc.invite          [==========|==========|==========]
m.rtc.member (join)   |          [==========|xxxxxxxxxxxxxxxxxxxxx]
m.rtc.member (leave)  |          |          [================================]
                      |          |          |
Invite active         [##########]          |
                      |          |          |
                      Invite     Invite     Invitee
                      sent       accepted   leaves
```

#### Example 2: User declines invite

```
m.rtc.invite          [==========|=====================]
m.rtc.decline.        |          [================================]
                      |          |
Invite active         [##########]
                      |          |
                      Invite     Invite
                      sent       declined
```

#### Example 3: User is already joined before being invited

```
m.rtc.invite                     [==========|=====================]
m.rtc.member (join)   [==========|==========|xxxxxxxxxx]
m.rtc.member (leave)  |          |          [================================]
                      |          |          |
Invite active         |          |          |
                      |          |          |
                      Slot       Invite     Invitee
                      joined     sent       leaves
```

#### Example 4: Alice and Bob call each other at the same time

Both join the slot and invite the other before seeing the other's invite. Bob's invite `$b` sorts
before Alice's `$a`, so `$b` is the call ID and Alice withdraws `$a` with `withdraw_reason.code`
`glare`. Both were joined before being invited, so neither invite rings anyone, the call counts as
answered at once, and their media connected as soon as both had joined.

```
m.rtc.member (Alice: join)   [==========|==========|==========|==========]
m.rtc.member (Bob: join)     |          [==========|==========|==========]
m.rtc.invite ($a, Alice)     |          |          [xxxxxxxxxx|xxxxxxxxxx]
m.rtc.invite ($b, Bob)       |          |          [==========|==========]
m.rtc.invite ($a withdrawn)  |          |          |          [==========]
                             |          |          |          |
Session                      [=======================================
Call $b                      |          |          [===========================
                             |          |          |          |
                             Alice      Bob        Invites    Alice
                             joins      joins      cross      withdraws
```

### Push rules

In order to allow clients to manage their notification settings for MatrixRTC invites, two new default
[push rules] are introduced.

`.m.rule.rtc.invite_for_me` matches `m.rtc.invite` events which contain the user's Matrix ID in
the list of `user_ids` under `m.mentions`.

```json5
{
  "rule_id": ".m.rule.rtc.invite_for_me",
  "default": true,
  "enabled": true,
  "conditions": [{
    "kind": "event_property_is",
    "key": "type",
    "value": "m.rtc.invite"
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
set to `true` (provided that the sender has the proper power level to trigger room notifications at
the time the invite is received[^mentions-pl]).

```json5
{
  "rule_id": ".m.rule.rtc.invite_for_room",
  "default": true,
  "enabled": true,
  "conditions": [{
    "kind": "event_property_is",
    "key": "type",
    "value": "m.rtc.invite"
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

The rules are inserted into the existing default rule set as follows:

- `.m.rule.rtc.invite_for_me` is inserted as an [`override`] rule before `.m.rule.is_user_mention`.
- `.m.rule.rtc.invite_for_room` is inserted as an [`override`] rule before `.m.rule.is_room_mention`.

The rules and their placement are designed to fit in with the common push rule configurations for setting
rooms to muted or mentions-only.

Muting of specific rooms is usually implemented in current clients via a user-defined `override` rule with
a `condition` on `room_id` and empty `actions`. This overrides both rules and silences any notification
for `m.rtc.invite` events.

Mentions-only rooms are commonly implemented via a room-specific rule with empty `actions`. The `override`
rules `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` are processed before such a rule.
As a result, `m.rtc.invite` events that include the user in `m.mentions` still cause notifications.
In turn, `m.rtc.invite` events that *don't* include the user in `m.mentions` are caught by the room-specific
rule and don't cause notifications. This behaviour is analogous to normal messages with `m.mentions`.

Finally, in rooms that are neither set to muted nor mentions-only, `m.rtc.invite` events with `m.mentions`
notify only if the user is included in the mentions.

| Push rule configuration | Invite with room mention | Invite with user mention | Invite without mention |
| ----------------------- | ------------------------ | ------------------------ | ---------------------- |
| Default | ✅ Notifies | ✅ Notifies | ❌ Silent |
| Mentions-only | ✅ Notifies | ✅ Notifies | ❌ Silent |
| Muted | ❌ Silent | ❌ Silent | ❌ Silent |

Furthermore, the two separate rules for MatrixRTC invites and their placement before the existing rules
for mentions means that the notification settings for MatrixRTC invites can be configured separately
from the settings for other mentions. The table below lists a few examples for configuring notifications
in a mentions-only room.

| Notify for | Push rule configuration |
| ---------- | ----------------------- |
| All mentions including MatrixRTC invites | default as above |
| All mentions except for MatrixRTC invites | set `actions` to `[]` on `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` |
| MatrixRTC invites but not other mentions | set `actions` to `[]` on `.m.rule.is_user_mention` and `.m.rule.is_room_mention` |

Note that in encrypted rooms, the server cannot apply any of the above rules because `m.rtc.invite`
events will be encrypted. In this case, clients need to reapply push rules after decrypting themselves.
This is already the case for other events and push rules.

[push rules]: https://spec.matrix.org/v1.19/client-server-api/#push-rules
[`override`]: https://spec.matrix.org/v1.19/client-server-api/#default-override-rules
[`underride`]: https://spec.matrix.org/v1.19/client-server-api/#default-underride-rules

## Potential issues

### Lack of application-specific notifications

This proposal deliberately only covers generic session invites and notifications. Some MatrixRTC
applications might have a need for application specific notification mechanisms though.

For instance, when issuing invites to the `m.call` application from [MSC4196], it could be helpful
to provide a hint for the intent of the call (audio or video). This would spare the invitee from
having to look up the `intent` properties of the current `m.rtc.member` events. Additionally, it
would also make it possible to convey the intent when no joined members exist yet.

Extensions like this could be added on top of this proposal, for instance, by allowing application
specific metadata in a dedicated `application` object inside of `m.rtc.invite` events. Doing so is
left as a task for a future proposal which can use this MSC as a foundation.

### Lack of feedback

As mentioned above, a ringing UX can be a reasonable choice in certain situations in order to create
an experience akin to classical phone calls. However, this proposal doesn't provide sending clients
with a way to know if their invite has reached the recipient or what their current status is (ringing,
busy, etc.). The window inbetween inviting and declining has deliberately been descoped from this
proposal and various solutions may be plugged into the system by a future MSC. As an example, lightweight
ringing acknowledgements could be communicated back via to-device messages. Alternatively, richer invite
progress updates could be mediated via sticky room messages. Lastly, a general event delivery receipt
mechanism could also be sufficient to cover some use cases.

### Sessions without calls have no identifier

Call IDs only exist for calls, which need an invite. Ad-hoc sessions, where members join a slot
without inviting anybody, remain without an identifier as in [MSC4143]. Applications that need
identifiers for these can define their own.

### Call boundaries depend on observed order

Whether a call is running when a sender invites depends on the order in which it has seen membership
and invite events, which can briefly differ between clients as discussed under accurate session
reconstruction in [MSC4143]. A sender that has not yet seen a call start will omit `call_id`, and its
invite then competes under the tie-break, which can give the call a different ID than clients that
saw the earlier invite first assumed. The outcome is still the same for everybody once all events
have been seen, and only invites without `call_id` ever compete.

Likewise, whether an answered call has ended depends on the client having seen every member leave.
A member whose leave is delayed until its delayed leave event fires, as per [MSC4143], keeps the call
running until then.

### Device-specific invites

This proposal uses `m.mentions` to target invite recipients. Mentions can currently be directed at either
the whole room or a set of users in the room. They don't support targeting specific devices, however.
This would be helpful in some cases, for instance, when a user has delegated part of their calling to a
designated bridge device standing in for their desk phone. A caller might only want to ring that device
rather than all of the user's devices. This feature is unlocked by adding support for device mentions
which a future proposal, such as [MSC4296], may explore.

[MSC4296]: https://github.com/matrix-org/matrix-spec-proposals/pull/4296

### Lack of push notifications in encrypted mentions-only rooms

In encrypted rooms, the server can see neither the actual type of events nor their `m.mentions`. As a
result, invite events will erroneously be caught by the `room`-kind push rule that is needed to implement
mentions-only rooms. This means invites don't trigger push notifications on mobile clients. This problem
is not unique to MatrixRTC invites and [MSC4028] is an ongoing attempt at solving it generally.

A possible mediation could be to send `m.rtc.invite` events unencrypted. The only currently available
MatrixRTC transport is [MSC4195] which already exposes user participation in slots to the homeserver
via SFU token requests. Not encrypting the invite event would, therefore, not increase the leakage
when using this transport. This might not be true for future MatrixRTC transports, however.

[MSC4028]: https://github.com/matrix-org/matrix-spec-proposals/pull/4028
[MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195

### Invalidation of existing call notification settings

Users might already have specific notification settings for calls via the existing `.m.rule.call`
push rule. These will not automatically apply to MatrixRTC invites which could lead to confusion.
Servers may consider migrating push rules for their existing users.

### Stale notifications on other clients of the same user

The push rules introduced in this proposal only cover `m.rtc.invite` events but don't provide a signal
to other clients of the same user when an invite is accepted or declined. As a result, those clients
may continue notifying or ringing the user erroneously until they have synced the respective
`m.rtc.member` or `m.rtc.decline` event.

The same limitation also exists in [legacy VoIP] where the `.m.rule.call` push rule only covers
`m.call.invite` events.

This problem cannot currently be solved with push rules because the spec [excludes] a user's own
events when generating notifications:

> Homeservers MUST NOT notify the Push Gateway for events that the user has sent themselves.

Resolving this existing issue is deemed out of scope here and may be tackled by a future proposal.

[excludes]: https://spec.matrix.org/latest/client-server-api/#push-rules

## Alternatives

### Inferring notifications from membership events

Instead of using dedicated `m.rtc.invite` and `m.rtc.decline` events, invites and declines could also
be inferred from `m.rtc.member` events. Adding the required metadata to these events would likely
overload them though. In comparison, the standalone events introduced in this proposal are more
explicit and form a better foundation for future extensions.

### Using a dedicated `invitees` property

Rather than re-using the `m.mentions` mechanism, `m.rtc.invite` events could have a dedicated
`invitees` property for specifying the targets of the invite. This would avoid overloading
the semantics of `m.mentions`. Additionally, a power level flag could be introduced that
allows to configure the threshold for MatrixRTC room invites separately from the threshold
for room mentions on other messages. It's unclear what use cases would require this, however.
Additionally, an `invitees` property would largely duplicate what `m.mentions` already supports.

### Treating sticky duration as lifetime

The lifetime of `m.rtc.invite` events could also be inferred from their sticky duration which
would eliminate the need for an explicit `lifetime` property. As mentioned earlier, clients
evaluate an invite's effective lifetime based on `sender_ts`, falling back to `origin_server_ts`
only on larger deviations. However, servers measure the sticky duration exclusively from
`origin_server_ts` because they have no access to `sender_ts` in encrypted events. As a result,
if the `lifetime` property were replaced with the event's sticky duration, clients could not
reliably evaluate the lifetime against `sender_ts` anymore. This is because when the stickiness
ends, the invite may not even be delivered to clients anymore. This would make it impossible to
account for clock-drift between inviting clients and servers.

### Identifying sessions rather than calls

[MSC4143] suggests that the event ID of an invite could serve as a session identifier. A session and
a call differ, however: a call can ring and fail without anyone joining, and one session can carry
several calls, or none. Reusing "session" for both would make it ambiguous which of the two an
identifier refers to, so this proposal identifies calls and leaves sessions as [MSC4143] defines them.

### Sender-chosen call identifiers

Invites could carry a `call_id` chosen freely by the sender, as `call_id` is in [legacy VoIP].
Deriving the identifier from the starting invite's event ID instead cannot collide or be forged, and
leaves nothing for the sender to choose.

### Inferring the call of an invite from timing alone

Instead of `call_id`, an invite could be taken to invite into whatever call is running when it is
sent. Clients can disagree on whether a call was running when an invite arrived, which would make the
call ID depend on the order in which each client saw events. `call_id` makes the sender's intent
explicit, and the tie-break covers the only case where several invites legitimately claim to start
the same call.

### A dedicated hangup event

[Legacy VoIP] ends calls with `m.call.hangup`, which covers rejecting, cancelling and hanging up
alike. In MatrixRTC, hanging up is already expressed by leaving the slot, with a `leave_reason`, and
a separate event would duplicate it and could contradict it. Declining and cancelling happen before
the user has joined, so they need events of their own, and their reasons follow the shape of
`leave_reason` so that all three read alike.

### Tie-breaking on timestamps or senders

Crossing invites could be resolved by `origin_server_ts` or by comparing sender Matrix IDs. Timestamps
are set by different homeservers and can be faked, and a comparison of Matrix IDs would always favour
the same user. Event IDs are random, known to every client, and settle a tie without bias.

## Security considerations

### Inviting without a valid `m.rtc.member` event

Under this proposal, the sender of `m.rtc.invite` events does not need to be joined to the slot
themselves in order to make the invite valid. This may seem like a potential abuse vector. However,
room members who are able to send `m.rtc.invite` events will usually also be able to send
`m.rtc.member` events unless the room power levels have specifically been configured otherwise.
Thus requiring a member event to send invites doesn't provide additional protection. The actual
access control for sending invites is the power level for sending `m.rtc.invite` events which
room administrators can raise as needed. When power levels allow sending invitations, users can
still mitigate abusive invites by configuring push rules accordingly.

Besides this, requiring the sender to have an `m.rtc.member` event also complicates invite processing.
Particularly on mobile, it would mean that after receiving a push notification, the client would
have to fetch an additional related room event, including the information required for decryption,
in order to validate the invite. This increases the chance to run into time limits applied to
notification processing by mobile operating systems. While it's possible to mitigate this by
processing invites optimistically while they're being validated in the background, this introduces
further abuse risks.

Lastly, being able to invite users into a MatrixRTC session without being joined oneself, also
acts as a feature and enables integrations such as meeting bots to issue invites without having
to support MatrixRTC themselves.

### Inflating `sender_ts` and/or `lifetime`

A malicious client could send invites with a fake `sender_ts` that lies in the future and/or a
large `lifetime` in an attempt to cause receiving clients to notify or ring their users for extended
periods of time. This is mitigated by the recommendations given earlier, in particular measuring the
lifetime from `sender_ts` only if is before `origin_server_ts` and the maximum allowed `lifetime` of
2 minutes.

Similarly, a malicious server could fake `origin_server_ts` to be in the future to cause long-lived
notifications. Again, the client-side 2 minute cap for the remaining lifetime acts as a mitigation.

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
| Directing invites at specific users | ✅ via [`m.call.invite`] and `invitee` | ✅ via `m.rtc.invite` and `m.mentions` |
| Directing invites at the room | ❌ Not possible | ✅ via `m.rtc.invite` and `m.mentions` |
| Expiring invites | ⚠️ via `lifetime` on [`m.call.invite`] evaluated against [`age`] which is known to be broken in various homeservers | ✅ via `lifetime` on `m.rtc.invite` evaluated against either `sender_ts` or `origin_server_ts` |
| Inviting without starting a call | ❌ Not possible | ✅ Explicitly allowed if an open slot exists |
| Withdrawing invites | ✅ via [`m.call.hangup`] events | ✅ via empty or redacted `m.rtc.invite` events |
| Declining invites | ✅ via [`m.call.hangup`] events | ✅ via `m.rtc.decline` events |
| Call identifiers | ✅ `call_id` | ✅ event ID of the call's first `m.rtc.invite` |
| Why a call ended | ⚠️ `reason` on [`m.call.hangup`], one event for every ending | ✅ `decline_reason`, `withdraw_reason` and `leave_reason`, each on the event that ends it |
| Glare | ✅ lexicographic comparison of `call_id`; the losing call is hung up | ✅ comparison of invite event IDs; media is unaffected |
| Notifications in default rooms | ✅ via `.m.rule.call` push rule | ✅ via `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` push rules |
| Notifications in mentions-only rooms | ❌ Not possible | ✅ via `.m.rule.rtc.invite_for_me` and `.m.rule.rtc.invite_for_room` push rules |
| Events required to validate session invites | ✅ 1 ([`m.call.invite`]) | ⚠️ 2 (`m.rtc.slot` and `m.rtc.invite`; since `m.rtc.slot` is a state event both can be fetched in the same `/sync`, however) |

[`m.call.invite`]: https://spec.matrix.org/v1.19/client-server-api/#mcallinvite
[`age`]: https://spec.matrix.org/v1.19/client-server-api/#call-event-liveness
[`m.call.hangup`]: https://spec.matrix.org/v1.19/client-server-api/#mcallhangup

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.invite` | Event type | `org.matrix.msc4075.rtc.notification` |
| `m.rtc.decline` | Event type | `org.matrix.msc4310.rtc.decline` |
| `call_id` | Property of `m.rtc.invite` | `org.matrix.msc4075.call_id` |
| `withdraw_reason` | Property of `m.rtc.invite` | `org.matrix.msc4075.withdraw_reason` |
| `decline_reason` | Property of `m.rtc.decline` | `org.matrix.msc4075.decline_reason` |
| `.m.rule.rtc.invite_for_me` | Push rule ID | `.org.matrix.msc4075.rule.rtc.invite_for_me` |
| `.m.rule.rtc.invite_for_room` | Push rule ID | `.org.matrix.msc4075.rule.rtc.invite_for_room` |

Note that the unstable identifier for invite events uses `rtc.notification` rather than `rtc.invite` due
to an earlier iteration of this proposal having been implemented first. Moreover, decline events were
originally specified in [MSC4310] and, therefore, use that MSC number in their unstable identifier.

[MSC4310]: https://github.com/matrix-org/matrix-spec-proposals/pull/4310

## Dependencies

This proposal depends on [MSC4143] and [MSC4354].

## Appendix

### Implementation differences in the reference implementation

The reference implementation of this proposal is documented in a [file-level comment] and touches
[matrix-js-sdk], [element-web] and [synapse]. For practical reasons, some changes of the proposal
text that resulted from iterating or from review comments have not been carried over into the
implementation. As of writing, the full list of such implementation differences is as follows:

- `org.matrix.msc4075.rtc.notification` events contain a property `notification_type` that has been
  removed from the proposal. Instead, receiving clients have control about how to present the invite.
- `org.matrix.msc4075.rtc.notification` events contain a property `m.call.intent` that has been removed
  from the proposal. Instead, receiving clients can look up the intent from membership events.
- `org.matrix.msc4075.rtc.notification` events contain an `m.reference` relation to the sending user's
  RTC member event that has been removed from the proposal. Instead, receiving clients can look up
  membership events via the slot.
- The value of `sender_ts` is allowed to be up to 20 seconds later than `origin_server_ts`.

[^mentions-pl]: Note that this matches how `room` mentions are already handled in practice today even
                though the spec doesn't make it explicit yet (see https://github.com/matrix-org/matrix-spec/issues/2443).

[file-level comment]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075/changes#r4026443865
[matrix-js-sdk]: https://github.com/matrix-org/matrix-js-sdk/
[element-web]: https://github.com/element-hq/element-web
[synapse]: https://github.com/element-hq/synapse
