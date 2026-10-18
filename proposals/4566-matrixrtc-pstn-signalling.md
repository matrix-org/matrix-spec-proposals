# MSC4566: MatrixRTC call progress and PSTN signalling

[MSC4075] lets a user invite others into a MatrixRTC session and lets them accept, decline or ignore
the invite, and identifies the resulting session by the event ID of the invite. That is enough for
calls between Matrix clients. It is not enough for calls that leave Matrix: a bridge that dials a
phone on the PSTN or a SIP network on behalf of a Matrix user learns a lot more from the far side
than "answered" or "not answered", and the caller expects to hear it. A phone call tells the caller
that the far end is ringing, lets them hear a ringback tone or an announcement from the network
before anybody answers, and tells them afterwards whether the line was busy, nobody picked up, or
the number could not be reached.

Consider Alice, on a Matrix client, calling Bob, who is reachable through a bridge that puppets his
phone number as a Matrix user. Alice's client sends an `m.rtc.invite`. The bridge dials Bob's phone.
Under [MSC4075] alone, Alice's client rings until the invite's `lifetime` elapses or the bridge joins
the slot, and if Bob's line is busy the bridge can only decline, which Alice's client shows as
"declined". With this proposal, the bridge reports `ringing` once the phone network says the phone is
alerting, joins the slot to play the network's ringback tone or announcement to Alice, reports
`answer` when Bob picks up, and declines with `busy` if the line was engaged.

This proposal adds what is needed for this on top of [MSC4075]: an explicit answer, per-device
reports of ringing and failure, and reasons on declines and withdrawn invites. It is purely
additive. Clients that only implement [MSC4075] keep working, and a native Matrix client only needs
the parts that concern an inviter, plus sending `ringing` and `answer` if it chooses to.

[MSC4075]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075

## Proposal

This proposal uses the terms of [MSC4075] and [MSC4143]. A session starts with an `m.rtc.invite`,
is identified by that invite's event ID (its session ID), and ends when it is declined, cancelled,
expires unanswered or when every member who joined it has left. Where this proposal says "call", it
means such a session as seen from a telephone network. Three additions are made:

- A new [sticky][MSC4354] room event, `m.rtc.invite_progress`, reports the progress of an invite on
  one of the recipient's devices: that it is ringing, that it has been answered, or that it has
  failed. The explicit `answer` state is what separates early media from answering.
- `m.rtc.decline` gains an optional `decline_reason` saying why the invite was declined.
- A withdrawn `m.rtc.invite` gains an optional `withdraw_reason` saying why it was withdrawn.

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354

### Reason codes

Declines, withdrawals and failed progress all carry the same kind of reason object:

- `code` (required, string): One of the [call outcome codes] below.
- `reason` (optional, string): A human-readable explanation, for logs and diagnostics rather than
  for display. A bridge would typically put the SIP status line here.
- `sip_status` (optional, integer): The SIP status code that led to this outcome, when the event is
  sent on behalf of a SIP or PSTN endpoint. Informational only.
- `q850_cause` (optional, integer): The [Q.850] cause value that led to this outcome, when the event
  is sent on behalf of a PSTN endpoint. Informational only.

[Q.850]: https://www.itu.int/rec/T-REC-Q.850
[call outcome codes]: #call-outcome-codes

#### Call outcome codes

The SIP and Q.850 values listed are typical, after [RFC 3398]. They show what a bridge would map to
each code and are not exhaustive.

| Code | Used in | Meaning | Q.850 cause | SIP |
| ---- | ------- | ------- | ----------- | --- |
| `declined` | decline | The user chose not to answer. | 21 | 603 |
| `busy` | decline, progress | The endpoint cannot take the call now. | 17 | 486, 600 |
| `no_answer` | decline, progress | The endpoint alerted but nobody answered. | 19 | 408 or 480 after alerting |
| `unreachable` | decline, progress | The endpoint could not be reached or alerted. | 1, 3, 18, 20, 27, 34, 38 | 404, 410, 408 or 480 without alerting, 502, 503, 504 |
| `cancelled` | withdrawal | The inviter gave up before anyone answered. | 16 | CANCEL |
| `glare` | withdrawal | The invite lost [MSC4075]'s crossing-invite resolution to another. | — | — |

A native Matrix client does not decline with `busy` merely because its user is in another call;
[MSC4075] lets the user accept a second invite. Future proposals MAY define further codes. Receivers
treat an unknown code as `declined` in a decline, as `cancelled` in a withdrawal and as no report at
all in progress.

[RFC 3398]: https://www.rfc-editor.org/rfc/rfc3398

### Invite progress

The schema of `m.rtc.invite_progress` is as follows:

- `m.relates_to` (required, object): An [`m.reference` relation] to the `m.rtc.invite` event whose
  progress is being reported, as [MSC4075] requires of every event that acts on an invite.
- `member_id` (required, string): The `member.id` that the sending device uses, or will use, for its
  `m.rtc.member` event in the invite's slot, as defined in [MSC4143]. A device that never joins still
  picks one; it only has to be unique among the user's devices, exactly as `member.id` has to be.
- `sticky_key` (required, string): The event's sticky key as per [MSC4354]. MUST be equal to the
  event ID of the `m.rtc.invite` event, followed by `|`, followed by `member_id`. As the ephemeral map
  is keyed by sender, type and sticky key, this gives each of the user's devices its own entry, and a
  later report from a device replaces only that device's earlier one.
- `state` (required, string): The progress of the invite on that device. One of:
  - `ringing`: The device is alerting the user, or the endpoint it stands in for is (a phone behind a
    SIP bridge has returned `180 Ringing`, say).
  - `answer`: The user has explicitly answered the invite on this device, or the endpoint it stands
    in for has. This is the [answer] of the invite.
  - `busy`, `no_answer`, `unreachable`: The device, or the endpoint it stands in for, will not answer
    this invite, for the reasons given by the [call outcome codes]. Unlike a decline, this is per
    device: the user's other devices may still be ringing.
- `reason`, `sip_status`, `q850_cause` (optional): As in [reason codes] above. Only meaningful with
  a failure state.

```json5
{
  "type": "m.rtc.invite_progress",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$1"
    },
    "member_id": "xyzABCDEF0123",
    "sticky_key": "$1|xyzABCDEF0123",
    "state": "ringing",
    "reason": "180 Ringing",
    "sip_status": 180
  }
}
```

Progress only moves forward. `ringing` may be followed by `answer` or by one of the failure states,
and a device SHOULD send each state at most once per invite. Devices SHOULD NOT report progress on
invites that are inactive for their user.

[`m.reference` relation]: https://spec.matrix.org/v1.19/client-server-api/#reference-relations
[reason codes]: #reason-codes
[answer]: #answering-and-early-media

### Decline reasons

`m.rtc.decline` as defined in [MSC4075] gains one optional property:

- `decline_reason` (optional, object): Why the invite was declined, as a [reason codes] object with a
  `code` of `declined`, `busy`, `no_answer` or `unreachable`. Absent means `declined`.

```json5
{
  "type": "m.rtc.decline",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$1"
    },
    "sticky_key": "$1",
    "decline_reason": {
      "code": "busy",
      "reason": "486 Busy Here",
      "sip_status": 486,
      "q850_cause": 17
    }
  }
}
```

A decline remains a final answer from the user as a whole: it inactivates the invite for that user on
every device, exactly as in [MSC4075]. `decline_reason` only explains why.

### Withdraw reasons

[MSC4075] withdraws an invite by sending another `m.rtc.invite` with the same `sticky_key` and an
otherwise empty content. This proposal lets the withdrawal carry one optional property:

- `withdraw_reason` (optional, object): Why the invite was withdrawn, as a [reason codes] object with
  a `code` of `cancelled` or `glare`. Absent means `cancelled`.

```json5
{
  "type": "m.rtc.invite",
  "content": {
    "sticky_key": "m.call#room",
    "withdraw_reason": {
      "code": "glare"
    }
  }
}
```

Accordingly, [MSC4075]'s definition of a withdrawal is amended to an `m.rtc.invite` event whose
`content` has no properties other than `sticky_key` and `withdraw_reason`. A client that only
implements [MSC4075] sees such an event as an invite without `slot_id` or `m.mentions`, which that
proposal already makes invalid, so it still stops treating the withdrawn invite as active.

### Answering and early media

Under [MSC4075], a targeted user accepts an invite by joining the slot. This proposal keeps that
and adds a way to join without accepting, so that media can flow before the call is answered. The
rule is that a device which intends to send early media says so, by reporting `ringing` for the
invite before it joins:

- A targeted user has **answered** an invite if any of their devices has sent an
  `m.rtc.invite_progress` with `state` `answer` for it, or if the user has an `m.rtc.member` event
  in the ephemeral sticky events map with a membership of `join` for the slot whose `member.id` has
  no `m.rtc.invite_progress` entry for the invite from that user with `state` `ringing`.
- Any other `m.rtc.member` join by a targeted user is an **early member** of the invite: it has
  reported `ringing` and not yet answered. Its media is early media.

Since a device's own events are delivered in the order it sent them, a receiver never sees the join
of an early member before its `ringing` report, and a join from a device that never reported
anything (a client that only implements [MSC4075]) is the answer, as before. The call is answered
at the `origin_server_ts` of the `answer` report if there is one, else of the answering join.

To that end, the definition in [MSC4075] of when a targeted user has _not_ yet acted on an invite is
amended. Its first two requirements become:

- The user has not answered the invite as defined above.
- If there is an `m.rtc.member` event sent by the user in the ephemeral sticky events map that has a
  membership of `leave` for the slot and whose `origin_server_ts` is greater than that of the invite
  event, the user has an `m.rtc.invite_progress` entry for the invite with that `member.id` and
  `state` `ringing`. That is, an early member leaving again does not count as having answered and
  left.

The third requirement, that there is no `m.rtc.decline` from the user referencing the invite, is
unchanged. `m.rtc.invite_progress` events with any state other than `answer` never change whether
an invite is active.

A device that answers SHOULD send `answer` and then join, so that inviters see the answer as soon as
possible. A device that is already an early member sends `answer` and keeps its membership. A device
abandons an early membership by leaving the slot; if it is the user's only endpoint it SHOULD also
decline, as set out under [reporting progress].

[reporting progress]: #reporting-progress

### Stickiness and encryption

Clients MUST send `m.rtc.invite_progress` as sticky events as per [MSC4354] for the associated
delivery guarantee. The sticky duration of an `m.rtc.invite_progress` event SHOULD NOT be smaller
than the `lifetime` of the invite it reports on, and the sticky duration of an `answer` SHOULD NOT be
smaller than that of the device's `m.rtc.member` event, so that the two outlive each other together.
Inviting clients that present progress MUST implement the ephemeral map algorithm as per [MSC4354]
for `m.rtc.invite_progress` events, as [MSC4075] already requires for `m.rtc.invite` and
`m.rtc.decline`.

`m.rtc.invite_progress` MUST be sent encrypted when the room is encrypted, as `m.rtc.invite` and
`m.rtc.decline` are.

No push rules are introduced for `m.rtc.invite_progress`. It is not meant to notify the user.

### Call flow

Putting [MSC4075] and this proposal together, a session identified by invite `X` moves through the
following states. `{X}` means the event references `X`. Members join and leave as per [MSC4143];
the transitions below are the ones that matter to signalling.

```text
                               +------+
                               | IDLE |
                               +------+
                                  |
                                  | m.rtc.invite X + inviter's m.rtc.member join
                                  v
+------------------------------------------ pre-answer -------------------------------------------+
|                                                                                                 |
|   +----------+   m.rtc.invite_progress {X} ringing   +---------+                                |
|   | INVITING |------------------------------------->| RINGING |                                |
|   +----------+       (from any callee device)       +---------+                                |
|        |                                                 |                                     |
|        |                                                 | callee's m.rtc.member join          |
|        |                                                 | (early member: it reported ringing) |
|        |                                                 v                                     |
|        |                                          +-------------+                              |
|        |                                          | EARLY_MEDIA |                              |
|        |                                          +-------------+                              |
|        |                                                 |                                     |
+--------|-------------------------------------------------|-------------------------------------+
         |                                                 |
         | callee's m.rtc.member join                      | m.rtc.invite_progress {X} answer
         | (no ringing report: answers)                    |
         |                                                 |
         |   from any pre-answer state:                    |
         |     m.rtc.invite withdrawn, cancelled   -> ENDED (cancelled)                           
         |     m.rtc.invite withdrawn, glare       -> ENDED (glare)
         |     m.rtc.decline {X}                   -> ENDED (declined / busy / no_answer / unreachable)
         |     invite lifetime elapses             -> ENDED (no_answer)
         |     inviter's m.rtc.member leaves       -> ENDED (cancelled)
         v                                                 v
   +----------+    every member of the session has left    +-------+
   | ANSWERED |------------------------------------------->| ENDED |
   +----------+                 (hangup)                   +-------+
```

- `RINGING` and `EARLY_MEDIA` are per device; the session is in the furthest state any targeted
  device has reached. A failure report (`busy`, `no_answer`, `unreachable`) from one device returns
  that device to `INVITING` without ending the session, since the user's other devices may still
  answer. The session ends with that outcome only through a decline, or when the lifetime elapses.
- In a group, several targeted users may answer; the session is `ANSWERED` from the first.
- The loser of crossing invites withdraws with `glare` and, if it had joined, sends
  `m.rtc.invite_progress` `answer` on the winning invite, since its media is already up.
- In a two-party call, the remaining member leaves once the other has, so "every member has left"
  happens promptly. What ends a session once answered is defined by [MSC4075].

### Reporting progress

This section matters most for devices that stand in for an endpoint which cannot speak Matrix itself,
such as a bridge that dials a phone on the PSTN or a SIP network for a targeted user. Such a device
learns how the call is going from the far side and relays it into the room. Plain Matrix clients only
need the rules for inviting clients, plus `ringing` and `answer` if they choose to send them.

The protocol keeps two things apart, as SIP does between provisional and final responses:

- **Per-device progress** is carried by `m.rtc.invite_progress`. Except for `answer`, it is optional,
  best effort, and never changes whether an invite is active.
- **The user's final outcome** is an answer, a decline (`m.rtc.decline`, optionally with a
  `decline_reason`) or nothing, in which case the invite expires.

Devices that alert for an invite MAY report `ringing`, so that the inviter can tell a delivered invite
from one that reached nothing. Devices that stand in for an endpoint SHOULD report each state as they
learn of it.

A device standing in for an endpoint that is the user's only way to be reached (for example, a bridge
puppeting a phone number as a Matrix user) SHOULD conclude a failed call with an `m.rtc.decline`
carrying the matching `decline_reason`, rather than only an `m.rtc.invite_progress` failure. This
gives the inviter a final answer straight away. A device which is one of several for its user cannot
know that the others have failed too, so it reports the failure as progress and leaves the final
outcome to the user's other devices or to the invite's `lifetime`.

#### Early media

A device standing in for an endpoint follows the established rules for early media ([RFC 3960]):

- When the far side signals alerting without media (SIP `180 Ringing` without SDP, ISUP ACM or CPG
  without in-band information), the device reports `ringing` and does not join the slot. The
  inviter's client plays its own ringback tone.
- When the far side sends early media (SIP `183 Session Progress` or `180` with SDP, or in-band
  information in ISUP or Q.931), the device reports `ringing` if it has not already and then joins
  the slot, publishing that media. It may be a ringback tone, an announcement or anything else, and
  the device cannot reliably tell which.
- When the far side answers (SIP `200 OK`, ISUP ANM or CON, Q.931 CONNECT), the device reports
  `answer`, and joins the slot if it has not already. This inactivates the invite exactly as any
  other answer does.
- When the call fails, the device reports the failure or declines as described above, and leaves
  the slot if it had joined.

The media direction before an answer is backwards only, as in the PSTN. An early member MUST NOT
present other members' media to the user or endpoint it stands in for until it has answered. A bridge
MUST NOT forward the caller's audio to the far side before the answer.

Inviting clients:

- MAY play a local ringback tone while an invite is active for a targeted user, and SHOULD do so once
  any device of a targeted user has reported `ringing`.
- MUST stop any local ringback tone and play the early member's media instead while a targeted user
  has an early member in the slot. This avoids the two being heard at once, and lets a caller hear
  an announcement such as "the number you have called is not available".
- SHOULD summarise progress per targeted user across all of that user's devices, rather than showing
  the latest report alone. For example, the user is "ringing" if any device's current report is
  `ringing`, and "busy" only if every device that reported has failed with `busy`.
- MAY withdraw the invite once every targeted user has declined, or once every device that reported on
  it has failed and none is ringing, as it would after a decline.
- MAY use progress to say "ringing" rather than "calling" once a recipient is actually alerting, and
  a `decline_reason` to say "busy" rather than "declined".
- SHOULD start any call timer from the answer rather than from the first join.

Clients other than the inviter SHOULD present early members as connecting rather than present, and
SHOULD NOT play their media. In a group call, a bridge dialling out on someone's behalf would
otherwise play ringback to everybody.

Receivers MUST ignore `m.rtc.invite_progress` and `m.rtc.decline` events whose sender is not targeted
by the referenced invite (see [security considerations]).

[RFC 3960]: https://www.rfc-editor.org/rfc/rfc3960
[legacy VoIP]: https://spec.matrix.org/v1.19/client-server-api/#voice-over-ip
[security considerations]: #security-considerations

### Exemplary flows

The examples use the legend of [MSC4075]:

```
[===]: Event is the current one in the sticky map
[xxx]: Event is not the current one anymore
[###]: Invite is considered active
```

#### Example 1: A bridge dials a phone, which plays early media and is then answered

The bridge's join follows its `ringing` report, so it is an early member and does not inactivate the
invite; its `answer` does. While the early member is present, the inviter hears its media instead of
a local ringback tone.

```
m.rtc.invite                     [==========|==========|==========|==========]
m.rtc.invite_progress (ringing)  |          [==========|==========|xxxxxxxxxxxxxxxxxxxx]
m.rtc.member (join)              |          |          [==========|=====================]
m.rtc.invite_progress (answer)   |          |          |          [=====================]
                                 |          |          |          |
Invite active                    [################################]
                                 |          |          |          |
                                 Invite     Phone      Early      Phone
                                 sent       rings      media      answers
```

#### Example 2: A bridged phone is busy

The bridge is the user's only endpoint, so it declines with a reason. The inviter's client can show
"busy" at once instead of ringing until the `lifetime` elapses.

```
m.rtc.invite                         [==========|=====================]
m.rtc.decline (decline_reason: busy) |          [================================]
                                     |          |
Invite active                        [##########]
                                     |          |
                                     Invite     Phone
                                     sent       busy
```

#### Example 3: One device is busy, another answers

Each device has its own progress entry. The `busy` report from device B does not end the invite for
the user, so device A can still answer. A never reported `ringing`, so its join alone is the answer.

```
m.rtc.invite                        [==========|==========|==========|==========]
m.rtc.invite_progress (A: ringing)  |          [==========|==========|=====================]
m.rtc.invite_progress (B: busy)     |          |          [==========|=====================]
m.rtc.invite_progress (A: answer)   |          |          |          [=====================]
m.rtc.member (A: join)              |          |          |          [=====================]
                                    |          |          |          |
Invite active                       [################################]
                                    |          |          |          |
                                    Invite     A          B          A
                                    sent       rings      busy       answers
```

#### Example 4: The caller gives up

The inviter withdraws with `cancelled` and leaves the slot. The bridge, which was ringing the phone,
cancels the call on the far side.

```
m.rtc.invite                         [==========|==========|xxxxxxxxxxxxxxxxxxxxx]
m.rtc.invite_progress (ringing)      |          [==========|=====================]
m.rtc.invite (withdrawn: cancelled)  |          |          [=====================]
                                     |          |          |
Invite active                        [#####################]
                                     |          |          |
                                     Invite     Phone      Caller
                                     sent       rings      hangs up
```

## Potential issues

### Feedback is best effort

`m.rtc.invite_progress` and `decline_reason` give sending clients a way to learn whether an invite
reached a recipient and why a call was not answered. However, reports other than `answer` are
optional and only as good as the reporting device's knowledge. A client that rings but never reports
looks the same as one the invite never reached, and a bridge relays whatever the far side told it.
Sending clients MUST therefore not depend on progress reports for correctness, and SHOULD treat an
invite without any reports as they would without this proposal.

### Early media in group calls

An early member is a full member as far as [MSC4143] and its transports are concerned. Clients that
do not implement this proposal will treat it as present and may play its early media to everyone
joined to the slot, and clients that only implement [MSC4075] will take its join as the answer. This
proposal asks clients other than the inviter not to play early media. Restricting early media to the
inviter at the transport level, for instance through SFU subscription permissions, is left to
transport specifications.

### A legacy device answering next to a reporting one

The early-member rule is keyed by `member.id`, so a device that reported `ringing` and a device that
did not are told apart. A single device that reports `ringing` and then joins without ever sending
`answer`, because it stopped implementing this proposal halfway, would be shown as early media until
the invite expires. Devices that report `ringing` MUST therefore also report `answer`.

### Alerting longer than two minutes

The 2-minute cap in [MSC4075] on an invite's remaining lifetime is shorter than the no-answer timers
of some telephone networks. A caller who wants to keep ringing for longer needs to send a fresh invite
before the previous one expires, which starts a new session. A bridge reporting on such a call will
see the invite it is reporting on replaced, and SHOULD carry on reporting against the new one.

### Addressing endpoints outside Matrix

Invites can only target Matrix users who are members of the room. Calling a telephone number or SIP
address requires a bridge to represent it as a Matrix user first. A first-class way of addressing
such endpoints is left to a future proposal, as is targeting a specific device of a user, which
[MSC4075] leaves to proposals such as [MSC4296].

[MSC4296]: https://github.com/matrix-org/matrix-spec-proposals/pull/4296

### Pushes for progress in encrypted direct chats

In encrypted direct chats, the server cannot tell `m.rtc.decline` and `m.rtc.invite_progress` apart
from messages, so `.m.rule.encrypted_room_one_to_one` will push them to the inviter's devices, which
then have to discard them after decrypting. This is already true of `m.rtc.member` events.

### Stale notifications on other devices

[MSC4075] notes that a user's other devices keep ringing until they sync the event that accepted or
declined the invite. Telephone networks cancel the alert on every other branch when one answers,
and users coming from the phone network will expect the same, so this matters more for calls that
interwork with the PSTN than it did for legacy VoIP. It remains out of scope here.

## Alternatives

### An `early` flag on `m.rtc.member`

An earlier draft marked early media with an `early: true` property on the `m.rtc.member` event, and
answered by re-sending the membership without it. That makes "joined but not answered" a property of
a single event, which is robust against ordering, but it signals the answer in a roundabout way: the
answer is the absence of a flag on an update to an unrelated event, and nothing records who
explicitly answered or when. It also required `early` on the leave as well, so that an abandoned
early membership did not count as "answered and left". An explicit `answer` state records the
answer as an event of its own, timestamps the call from it, and leaves `m.rtc.member` untouched.
The ordering question is settled instead by requiring an early member to report `ringing` first.

### A dedicated `m.rtc.answer` event

The answer could be its own event type rather than a state of `m.rtc.invite_progress`. Progress
already is a per-device, per-invite, sticky, referenced event, which is exactly what an answer
needs, and keeping the answer in the same ephemeral map entry as the device's `ringing` means a
device's progress is one value that moves forward rather than two events to reconcile.

### Signalling the answer with a `connected` progress state ranked above membership

An earlier draft let a bridge join the slot as soon as it started dialling and signal the answer with
a `connected` state, and had inviters rank progress reports above membership for any device that had
reported. That depended on ordering: if the join arrived before the first report, the inviter's
client would take it as the answer, start the call timer, and then have to back out. Requiring the
`ringing` report before the join removes the ambiguity.

### Keying progress reports by sender or by device ID

Using the invite's event ID alone as the sticky key for `m.rtc.invite_progress` would give each user
one entry in the ephemeral map. Reports from different devices would replace each other, so a `busy`
from one device could hide `ringing` on another. Keying by device ID instead would tell devices
apart, but [MSC4143] allows a device several memberships and does not put device IDs on `m.rtc.member`
events, so an inviter could not tell which membership a report belongs to. `member.id` is the
identifier the join will carry anyway.

### Treating a device's failure as a decline

A `busy` or `unreachable` result from one device could be taken as the user declining. This would
break calls to users with several devices, just as a single busy branch does not end a forked call in
SIP. The proposal keeps per-device failures in `m.rtc.invite_progress`, and leaves a decline with a
reason to devices that know they are the user's only endpoint.

### Reporting progress via to-device messages

Progress could be sent as to-device messages to the inviter's devices instead of as room events. They
would not appear in the room's timeline at all, which suits their short-lived nature. However, they
would leave no record to diagnose a failed call from, they need an Olm session with every device of
the inviter, and they do not reach devices the inviter adds later. As sticky room events, reports get
the same delivery guarantee as the invite they belong to.

### Putting reasons into [MSC4075]

`decline_reason` and `withdraw_reason` could live in [MSC4075] itself. They are only needed when a
call touches a telephone network, where the far side has told the bridge something worth relaying,
so they belong with the rest of the interworking here and keep [MSC4075] minimal.

## Security considerations

### Forged progress and outcomes

Any room member can send an `m.rtc.invite_progress` or `m.rtc.decline` event that references any
invite. Receivers MUST ignore both unless their sender is targeted by the referenced invite. This
prevents a third party from making a call look busy, unreachable or answered.

`member_id` is asserted by the sender. A user can always misreport the state of their own devices, so
this only matters if one device of a user could impersonate another, which [MSC4143] already
accepts for `member.id` itself.

### Early media

An early member publishes media to the slot before answering, and could receive other members'
media before answering. The rule that an early member does not present other members' media until it
answers keeps media flowing backwards only, as in the PSTN, so that an unanswered phone cannot
overhear the caller. This rule is enforced by the early member's own client or bridge, not by the
protocol. A transport that supports it SHOULD also deny early members subscriptions until they answer.

A targeted user could also join early to play arbitrary audio to the inviter without ever answering.
Inviting clients only play an early member's media while an invite to that member's user is active,
which bounds this to the invite's `lifetime`.

## Appendix: Comparison to [legacy VoIP]

These rows extend the comparison table in [MSC4075].

| Feature | Legacy VoIP | MatrixRTC |
| ------- | ----------- | --------- |
| Explicit answer | ✅ [`m.call.answer`] | ✅ `m.rtc.invite_progress` with `answer` |
| Reason for an unanswered call | ⚠️ `user_busy` and `invite_timeout` on [`m.call.hangup`] | ✅ `busy`, `no_answer` and `unreachable` in `decline_reason`, with SIP and Q.850 values |
| Reason for a cancelled call | ❌ Not possible | ✅ `cancelled` and `glare` in `withdraw_reason` |
| Ringing feedback to the caller | ❌ Not possible | ✅ via `m.rtc.invite_progress` events |
| Early media | ❌ Not possible | ✅ via `m.rtc.member` joins after `ringing` and before `answer` |

[`m.call.answer`]: https://spec.matrix.org/v1.19/client-server-api/#mcallanswer
[`m.call.hangup`]: https://spec.matrix.org/v1.19/client-server-api/#mcallhangup

## Appendix: Comparison to PSTN and SIP call control

This table maps the basic call of the PSTN (ISUP, [Q.764]), ISDN and H.323 access signalling ([Q.931],
[H.225.0]) and SIP ([RFC 3261]) onto MatrixRTC with [MSC4075] and this proposal. MatrixRTC leaves
media negotiation to its transports, so it has no counterpart for the bearer, H.245 or SDP parts of
those protocols. The lower part of the table lists supplementary services. This proposal does not
cover them, but nothing in it prevents future proposals from doing so.

| Function | ISUP | Q.931 / H.225.0 | SIP | MatrixRTC |
| -------- | ---- | --------------- | --- | --------- |
| Call setup | IAM | SETUP | INVITE | `m.rtc.invite` |
| Setup acknowledged | — | CALL PROCEEDING | 100 Trying | Not needed: the homeserver acknowledges the send |
| Called party alerting | ACM or CPG (alerting) | ALERTING | 180 Ringing | `m.rtc.invite_progress` with `ringing` |
| Early media | ACM or CPG with in-band information | PROGRESS (in-band information available) | 183 Session Progress with SDP | `m.rtc.member` join after `ringing`, before `answer` |
| Answer | ANM or CON | CONNECT | 200 OK, ACK | `m.rtc.invite_progress` with `answer` (or a join with no `ringing` report) |
| Caller abandons before answer | REL | DISCONNECT | CANCEL | Withdrawn `m.rtc.invite` with `withdraw_reason` `cancelled` |
| Called party busy | REL, cause 17 | DISCONNECT, cause 17 | 486, 600 | `m.rtc.decline` with `busy` |
| Called party rejects | REL, cause 21 | DISCONNECT, cause 21 | 603 | `m.rtc.decline` with `declined` |
| No answer | REL, cause 19 | DISCONNECT, cause 19 | 480 or 408 after alerting | `m.rtc.decline` with `no_answer`, or `lifetime` expiry |
| Unreachable | REL, cause 1, 18, 20, 27, 34 or 38 | DISCONNECT, same causes | 404, 410, 480, 502, 503, 504 | `m.rtc.decline` with `unreachable` |
| Release after answer | REL, RLC | DISCONNECT, RELEASE | BYE | Leaving `m.rtc.member`; the session ends when every member has left ([MSC4075]) |
| Reliable provisional responses | Inherent in the signalling link | Inherent | PRACK ([RFC 3262]) | Sticky events ([MSC4354]) |
| Parallel alerting of several terminals | — | — | Forking; the best final response wins | Per-device `m.rtc.invite_progress`; the first `answer` wins |
| Answered elsewhere | — | — | CANCEL with Reason "Call completed elsewhere" ([RFC 3326]) | ⚠️ Other devices see the `answer` (see [stale notifications]) |
| Call identifier | CIC | Call reference | Call-ID | Session ID: event ID of the `m.rtc.invite` ([MSC4075]) |
| Crossing setups (glare) | Dual seizure resolution | — | Two independent dialogs | Oldest invite wins ([MSC4075]); the loser withdraws with `glare` |
| **Supplementary services** | | | | |
| Calling line identity | Calling party number, CLIP | Calling party number | From, P-Asserted-Identity | The sender's Matrix ID |
| Calling line identity restriction | CLIR | Presentation indicator | Privacy | ❌ Not covered |
| Call diversion | Redirection information | Redirecting number | 3xx, Diversion, History-Info | ❌ Not covered |
| Call transfer | ECT | — | REFER, Replaces | ⚠️ Invite a third party, then leave; no identity update |
| Call hold | CPG (remote hold) | HOLD, RETRIEVE | re-INVITE (`sendonly`) | ❌ Not covered; left to applications such as [MSC4196] |
| DTMF | In-band | INFORMATION, keypad | [RFC 4733], INFO | `m.rtc.dtmf` ([MSC4568]) |
| Conference | Conference supplementary service | — | Conference focus | ✅ Inherent: a slot is a conference |
| Precedence and preemption | MLPP | MLPP | Resource-Priority ([RFC 4412]) | ❌ Not covered |

[Q.764]: https://www.itu.int/rec/T-REC-Q.764
[Q.931]: https://www.itu.int/rec/T-REC-Q.931
[H.225.0]: https://www.itu.int/rec/T-REC-H.225.0
[RFC 3261]: https://www.rfc-editor.org/rfc/rfc3261
[RFC 3262]: https://www.rfc-editor.org/rfc/rfc3262
[RFC 3326]: https://www.rfc-editor.org/rfc/rfc3326
[RFC 4412]: https://www.rfc-editor.org/rfc/rfc4412
[RFC 4733]: https://www.rfc-editor.org/rfc/rfc4733
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196
[MSC4568]: https://github.com/matrix-org/matrix-spec-proposals/pull/4568
[stale notifications]: #stale-notifications-on-other-devices

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.invite_progress` | Event type | `org.matrix.msc4075.rtc.invite_progress` |
| `member_id` | Property of `m.rtc.invite_progress` | `org.matrix.msc4566.member_id` |
| `answer`, `no_answer` | Values of `state` | `org.matrix.msc4566.answer`, `org.matrix.msc4566.no_answer` |
| `decline_reason` | Property of `m.rtc.decline` | `org.matrix.msc4566.decline_reason` |
| `withdraw_reason` | Property of a withdrawn `m.rtc.invite` | `org.matrix.msc4566.withdraw_reason` |
| `sip_status`, `q850_cause` | Properties of reason objects and `m.rtc.invite_progress` | `org.matrix.msc4566.sip_status`, `org.matrix.msc4566.q850_cause` |

The unstable identifier for `m.rtc.invite_progress` uses the number of [MSC4075] because the event
was first implemented as part of that proposal before being split out into this one. The states
`ringing`, `busy` and `unreachable` keep their names from that implementation.

## Dependencies

This proposal depends on [MSC4075], and through it on [MSC4143] and [MSC4354].

## Appendix: Implementation status

The MatrixRTC SIP bridge and Element Web implement an earlier draft of this proposal. In that draft,
the sticky key of `org.matrix.msc4075.rtc.invite_progress` is the invite's event ID alone, there is
no `member_id`, a free-text `reason` is used, the answer is reported as a `connected` state, and
failures are reported only as progress rather than as a decline with a `decline_reason`. The bridge
joins the slot as soon as it dials, which under this proposal is an early membership since it
reports `ringing` first.
