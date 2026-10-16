# MSC4566: MatrixRTC PSTN signalling

[MSC4075] lets a user invite others into a MatrixRTC session and lets them accept, decline or ignore
the invite. That is enough for calls between Matrix clients. It is not enough for calls that leave
Matrix: a bridge that dials a phone on the PSTN or a SIP network on behalf of a Matrix user learns a
lot more from the far side than "answered" or "not answered", and the caller expects to hear it.
A phone call tells the caller that the far end is ringing, lets them hear a ringback tone or an
announcement from the network before anybody answers, and tells them afterwards whether the line
was busy, nobody picked up, or the number could not be reached.

Consider Alice, on a Matrix client, calling Bob, who is reachable through a bridge that puppets his
phone number as a Matrix user. Alice's client sends an `m.rtc.invite`. The bridge dials Bob's phone.
Under [MSC4075] alone, Alice's client rings until the invite's `lifetime` elapses or the bridge joins
the slot, and if Bob's line is busy the bridge can only decline, which Alice's client shows as
"declined". With this proposal, the bridge reports `ringing` once the phone network says the phone is
alerting, joins the slot early to play the network's ringback tone or announcement to Alice, answers
by updating that membership when Bob picks up, and declines with `busy` if the line was engaged.
Once Bob's voicemail answers instead, Alice can press `1` to skip the greeting, because her client
sends the digit to the bridge, which plays it to the phone network.

This proposal adds what is needed for this on top of [MSC4075]: why an invite was declined,
per-device reports of ringing and failure, early media, and DTMF. It is purely additive. Clients
that only implement [MSC4075] keep working, and a native Matrix client only needs the parts that
concern an inviter, plus reporting `ringing` if it chooses to.

[MSC4075]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075

## Proposal

This proposal uses the terms of [MSC4075] and [MSC4143]. A session is the span during which members
are continuously joined to a slot. A call starts with an invite, is identified by its call ID, and
ends when it is declined, cancelled, expires unanswered or is hung up. Four additions are made:

- `decline_reason` on `m.rtc.decline`, as defined in [MSC4075], gains further codes and fields
  describing why a call to a telephone network failed.
- A new [sticky][MSC4354] room event, `m.rtc.invite_progress`, reports the progress of an invite on
  one of the recipient's devices.
- `m.rtc.member` gains an optional `early` flag, so that a device can join a slot to carry early
  media without that join counting as answering a call.
- A new room event, `m.rtc.dtmf`, sends keypad digits to a member that stands in for a non-Matrix
  endpoint, together with a `dtmf` capability for such members to advertise.

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354

### Decline reasons

[MSC4075] gives `m.rtc.decline` a `decline_reason` object with a `code` of `declined` or `busy` and an
optional human-readable `reason`. This proposal adds the codes `no_answer` and `unreachable`, listed
with the others under [call outcome codes], and two optional fields to the object:

- `sip_status` (optional, integer): The SIP status code that led to this outcome, when the decline
  is sent on behalf of a SIP or PSTN endpoint. Informational only.
- `q850_cause` (optional, integer): The [Q.850] cause value that led to this outcome, when the
  decline is sent on behalf of a PSTN endpoint. Informational only.

A bridge would typically put the SIP status line into `reason`. As in [MSC4075], receivers treat
codes they do not recognise as `declined`, so clients that only implement [MSC4075] show a
`no_answer` or `unreachable` decline as declined.

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

[Q.850]: https://www.itu.int/rec/T-REC-Q.850
[call outcome codes]: #call-outcome-codes

### Invite progress

The schema of `m.rtc.invite_progress` is as follows:

- `m.relates_to` (required, object): An [`m.reference` relation] to the `m.rtc.invite` event whose
  progress is being reported.
- `device_id` (required, string): The device whose progress is being reported. MUST be the device
  that sends the event.
- `sticky_key` (required, string): The event's sticky key as per [MSC4354]. MUST be equal to the
  event ID of the `m.rtc.invite` event, followed by `|`, followed by `device_id`. As the ephemeral map
  is keyed by sender, type and sticky key, this gives each of the user's devices its own entry, and a
  later report from a device replaces only that device's earlier one.
- `state` (required, string): The progress of the invite on that device. One of:
  - `ringing`: The device is alerting the user, or the endpoint it stands in for is (a phone behind a
    SIP bridge has returned `180 Ringing`, say).
  - `busy`, `no_answer`, `unreachable`: The device, or the endpoint it stands in for, will not answer
    this invite, for the reasons given by the [call outcome codes] below. Unlike a decline, this is
    per device: the user's other devices may still be ringing.
- `reason`, `sip_status`, `q850_cause` (optional): As in `decline_reason` above.

```json5
{
  "type": "m.rtc.invite_progress",
  "content": {
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$1"
    },
    "device_id": "SIPBRIDGE",
    "sticky_key": "$1|SIPBRIDGE",
    "state": "ringing",
    "reason": "180 Ringing",
    "sip_status": 180
  }
}
```

`m.rtc.invite_progress` events never change whether a user has acted on an invite, and so never
change whether an invite is active as per [MSC4075].

[`m.reference` relation]: https://spec.matrix.org/v1.19/client-server-api/#reference-relations

### Early membership

This proposal adds one optional property to the `member` object of `m.rtc.member` events as defined
in [MSC4143]:

- `early` (optional, boolean): If `true`, the device has joined the slot to carry early media (such as
  a network ringback tone or an announcement) on behalf of an endpoint that has not answered yet. It
  does not accept any invite. Defaults to `false`.

```json5
{
  "type": "m.rtc.member",
  "content": {
    "slot_id": "m.call#room",
    "member": {
      "id": "xyzABCDEF0123",
      "membership": "join",
      "early": true
    },
    "application": { "type": "m.call" },
    "transports": { ... },
    "sticky_key": "xyzABCDEF0123"
  }
}
```

An early member is joined for every purpose of [MSC4143]: other members connect to its transports
in the usual way. It only differs in how it counts towards invites and how its media is presented, as
set out under [call progress and early media]. A device answers by sending a new `m.rtc.member` event
with the same `sticky_key` and `early` absent or `false`, and abandons an early membership by leaving
with a leaving `m.rtc.member` event that also carries `early: true`. The flag on the leave is what
stops the leave from counting as the user having answered and left again.

To that end, the definition in [MSC4075] of when a targeted user has _not_ yet acted on an invite is
amended. The first two of its requirements become:

- There is no `m.rtc.member` event sent by the user in the ephemeral sticky events map that has a
  membership of `join` for the slot, or there is such an event but it has `early` set to `true`.
- If there is an `m.rtc.member` event sent by the user in the ephemeral sticky events map that has a
  membership of `leave` for the slot and does not have `early` set to `true`, its `origin_server_ts`
  is less than the `origin_server_ts` of the invite event.

The third requirement, that there is no `m.rtc.decline` from the user referencing the invite, is
unchanged.

[call progress and early media]: #call-progress-and-early-media

### DTMF

[MSC4143] describes who is in a call and where the media is. Once a Matrix user is talking to a
bridged phone there is no way to send `1` to an IVR, enter a conference PIN or navigate a voicemail
menu. [Legacy VoIP] had [`m.call.dtmf`]; MatrixRTC has nothing, and the member that needs it is
always one standing in for a non-Matrix endpoint, which on SIP turns the digits into [RFC 4733]
telephone-events or in-band tones. Between Matrix clients DTMF is meaningless, so this is
deliberately narrow: a point-to-point event aimed at one member of the call, ignored by everyone
else.

The schema of `m.rtc.dtmf`, a message-like room event sent in the room of the call, is as follows:

- `slot_id` (required, string): The `state_key` of the `m.rtc.slot` event the call takes place in, as
  in `m.rtc.member` and `m.rtc.invite`. A recipient not joined to that slot ignores the event.
- `device_id` (required, string): The sender's device, so that the recipient can match the event to
  the sender's `m.rtc.member` event and its media. MUST be the device that sends the event.
- `target` (required, object): The member the digits are for. Other members MUST ignore the event.
  This is not `m.mentions`: the event never notifies anyone.
  - `user_id` (required, string): The target member's Matrix ID.
  - `device_id` (optional, string): Narrows the target to one of that user's memberships. MAY be
    omitted when the user has a single membership in the slot.
- `digits` (required, string): One or more of `0`-`9`, `*`, `#` and `A`-`D`, played in order. A `,`
  is a one second pause, as in `tel:` URIs ([RFC 3966]).
- `duration_ms`, `gap_ms` (optional, integer): The tone length and the silence between tones, in
  milliseconds. Default to 100 and 70 respectively. Recipients clamp them to what the far end accepts
  ([RFC 4733] allows 40 ms to several seconds).

```json5
{
  "type": "m.rtc.dtmf",
  "content": {
    "slot_id": "m.call#room",
    "device_id": "WEB1234",
    "target": {
      "user_id": "@_sip_441onelondon:example.org",
      "device_id": "SIPBRIDGE"
    },
    "digits": "1#",
    "duration_ms": 100,
    "gap_ms": 70
  }
}
```

The recipient applies the event only if the sender is a current member of the slot. A stale event
from a device that has since left is dropped. It relays the digits to the endpoint it stands in for,
as [RFC 4733] events or in-band tones, whichever its leg negotiated. Digits are played after any
already queued from the same sender, never interleaved. There is no acknowledgement: a sender that
wants to know whether the far end reacted has the audio.

`m.rtc.dtmf` MUST be sent encrypted when the room is encrypted. Nothing in it needs to be readable
by the server, and digits are as sensitive as the call audio they are part of, such as a PIN typed
into an IVR. Clients SHOULD hide the event from the timeline, and no push rule is introduced for it.

#### Advertising a keypad

A member that can act on `m.rtc.dtmf` advertises this by including `dtmf` in the `capabilities`
list of its `m.rtc.member` event's `application` object, as defined for `m.call` in [MSC4196]. A
client SHOULD offer a keypad only while some other member joined to the slot advertises `dtmf`, and
SHOULD send the digits to that member. A recipient that does not understand the event ignores it.

[`m.call.dtmf`]: https://spec.matrix.org/v1.19/client-server-api/#mcalldtmf
[RFC 3966]: https://www.rfc-editor.org/rfc/rfc3966
[RFC 4733]: https://www.rfc-editor.org/rfc/rfc4733
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196

### Stickiness and encryption

Clients MUST send `m.rtc.invite_progress` as sticky events as per [MSC4354] for the associated
delivery guarantee. The sticky duration of an `m.rtc.invite_progress` event SHOULD NOT be smaller
than the `lifetime` of the invite it reports on. Inviting clients that present progress MUST
implement the ephemeral map algorithm as per [MSC4354] for `m.rtc.invite_progress` events, as
[MSC4075] already requires for `m.rtc.invite` and `m.rtc.decline`.

`m.rtc.invite_progress` MUST be sent encrypted when the room is encrypted, as `m.rtc.invite` and
`m.rtc.decline` are.

No push rules are introduced for `m.rtc.invite_progress`. It is not meant to notify the user.

### Call progress and early media

This section matters most for devices that stand in for an endpoint which cannot speak Matrix itself,
such as a bridge that dials a phone on the PSTN or a SIP network for a targeted user. Such a device
learns how the call is going from the far side and relays it into the room. Plain Matrix clients only
need the rules for inviting clients, plus reporting `ringing` if they choose to.

The protocol keeps two things apart, as SIP does between provisional and final responses:

- **Per-device progress** is carried by `m.rtc.invite_progress`. It is optional and best effort, and it
  never changes whether an invite is active.
- **The user's final outcome** is either an answer (a non-early join), a decline (`m.rtc.decline`,
  optionally with a `decline_reason`) or nothing, in which case the invite expires.

#### Call outcome codes

The following codes are used both as `decline_reason.code` and, except for `declined`, as the failure
values of `m.rtc.invite_progress.state`. `declined` and `busy` are defined in [MSC4075]; `no_answer`
and `unreachable` are added here. The SIP and Q.850 values listed are typical, after [RFC 3398]. They
show what a bridge would map to each code and are not exhaustive.

| Code | Meaning | Q.850 cause | SIP status |
| ---- | ------- | ----------- | ---------- |
| `declined` | The user chose not to answer. | 21 | 603 |
| `busy` | The endpoint cannot take the call now. | 17 | 486, 600 |
| `no_answer` | The endpoint alerted but nobody answered. | 19 | 408 or 480 after alerting |
| `unreachable` | The endpoint could not be reached or alerted. | 1, 3, 18, 20, 27, 34, 38 | 404, 410, 408 or 480 without alerting, 502, 503, 504 |

As [MSC4075] says, a native Matrix client does not decline with `busy` merely because its user is in
another call. Future proposals MAY define further codes. Receivers treat unknown codes as `declined`
in a decline and as no report at all in progress.

#### Reporting progress

Devices that alert for an invite MAY report `ringing`, so that the inviter can tell a delivered invite
from one that reached nothing. Devices that stand in for an endpoint SHOULD report each state as they
learn of it. Progress only moves forward: `ringing` may be followed by one of the failure states, and
a device SHOULD send each state at most once per invite. Devices SHOULD NOT report progress on
invites that are inactive for their user.

A device standing in for an endpoint that is the user's only way to be reached (for example, a bridge
puppeting a phone number as a Matrix user) SHOULD conclude a failed call with an `m.rtc.decline`
carrying the matching `decline_reason`, rather than only an `m.rtc.invite_progress` failure. This
gives the inviter a final answer straight away. A device which is one of several for its user cannot
know that the others have failed too, so it reports the failure as progress and leaves the final
outcome to the user's other devices or to the invite's `lifetime`.

#### Early media and answering

A device standing in for an endpoint follows the established rules for early media ([RFC 3960]):

- When the far side signals alerting without media (SIP `180 Ringing` without SDP, ISUP ACM or CPG
  without in-band information), the device reports `ringing` and does not join the slot. The
  inviter's client plays its own ringback tone.
- When the far side sends early media (SIP `183 Session Progress` or `180` with SDP, or in-band
  information in ISUP or Q.931), the device joins the slot with `early: true` and publishes that media.
  It may be a ringback tone, an announcement or anything else, and the device cannot reliably tell
  which.
- When the far side answers (SIP `200 OK`, ISUP ANM or CON, Q.931 CONNECT), the device sends a non-early
  join. If it was an early member, it updates that membership in place. This is the answer, and it
  inactivates the invite exactly as any other join does.
- When the call fails, the device reports the failure or declines as described above. If it was an
  early member, it leaves with `early: true`.

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

Clients other than the inviter SHOULD present early members as connecting rather than present, and
SHOULD NOT play their media. In a group call, a bridge dialling out on someone's behalf would
otherwise play ringback to everybody.

Receivers MUST ignore `m.rtc.invite_progress` and `m.rtc.decline` events whose sender is not targeted
by the referenced invite, and in encrypted rooms SHOULD discard an `m.rtc.invite_progress` event
whose `device_id` does not match the device they have established as the sender of the Megolm session
that encrypted it (see [security considerations]).

[RFC 3398]: https://www.rfc-editor.org/rfc/rfc3398
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

The bridge's early join does not inactivate the invite; its later non-early join, which updates the
same membership, does. While the early member is present, the inviter hears its media instead of a
local ringback tone.

```
m.rtc.invite                     [==========|==========|==========|==========]
m.rtc.invite_progress (ringing)  |          [==========|==========|=====================]
m.rtc.member (early join)        |          |          [==========|xxxxxxxxxxxxxxxxxxxx]
m.rtc.member (join)              |          |          |          [=====================]
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
the user, so device A can still answer.

```
m.rtc.invite                        [==========|==========|==========|==========]
m.rtc.invite_progress (A: ringing)  |          [==========|==========|=====================]
m.rtc.invite_progress (B: busy)     |          |          [==========|=====================]
m.rtc.member (A: join)              |          |          |          [=====================]
                                    |          |          |          |
Invite active                       [################################]
                                    |          |          |          |
                                    Invite     A          B          A
                                    sent       rings      busy       answers
```

## Potential issues

### Feedback is best effort

`m.rtc.invite_progress` and `decline_reason` give sending clients a way to learn whether an invite
reached a recipient and why a call was not answered. However, reports are optional and only as good
as the reporting device's knowledge. A client that rings but never reports looks the same as one the
invite never reached, and a bridge relays whatever the far side told it. Sending clients MUST
therefore not depend on progress reports for correctness, and SHOULD treat an invite without any
reports as they would without this proposal.

### Early media in group calls

An early member is a full member as far as [MSC4143] and its transports are concerned. Clients that
do not implement this proposal will treat it as present and may play its early media to everyone joined
to the slot. This proposal asks clients other than the inviter not to do so. Restricting early media
to the inviter at the transport level, for instance through SFU subscription permissions, is left to
transport specifications.

### Alerting longer than two minutes

The 2-minute cap in [MSC4075] on an invite's remaining lifetime is shorter than the no-answer timers
of some telephone networks. A caller who wants to keep ringing for longer needs to send a fresh invite
before the previous one expires. A bridge reporting on such a call will see the invite it is
reporting on replaced, and SHOULD carry on reporting against the new one.

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

### Signalling the answer with a `connected` progress state

An earlier draft let a bridge join the slot as soon as it started dialling and signal the answer with
an `m.rtc.invite_progress` state of `connected`. Inviting clients then had to rank progress reports
above membership for any device that had reported. That rule contradicted the activeness rules of
[MSC4075]: a bridge's early join would inactivate the invite for the user's other devices. It also
depended on ordering. If the join arrived before the first report, the inviter's client would take it
as the answer, start the call timer, and then have to back out. Putting `early` on the membership
itself makes "joined but not answered" a property of a single event, so no ordering can confuse it.

### Keying progress reports by sender

Using the invite's event ID alone as the sticky key for `m.rtc.invite_progress` would give each user
one entry in the ephemeral map. Reports from different devices would replace each other, so a `busy`
from one device could hide `ringing` on another. Including `device_id` in the sticky key avoids this.

### Treating a device's failure as a decline

A `busy` or `unreachable` result from one device could be taken as the user declining. This would
break calls to users with several devices, just as a single busy branch does not end a forked call in
SIP. The proposal keeps per-device failures in `m.rtc.invite_progress`, and leaves a decline with a
reason to devices that know they are the user's only endpoint.

### Sending DTMF as to-device messages

To-device messages would keep the digits out of the timeline and avoid `target`. But the room is
where the call is, DTMF to a device one is not in a call with is meaningless anyway, and
to-device delivery gives no ordering with the call's other events.

### Reusing legacy `m.call.dtmf`

Its `call_id` and `party_id` describe legacy VoIP signalling, not slots and memberships.

### Sending DTMF over the transport

A data channel of the transport, such as a LiveKit data track, would work within one SFU but not
across federated foci, and would tie the application to one transport.

### Reporting progress via to-device messages

Progress could be sent as to-device messages to the inviter's devices instead of as room events. They
would not appear in the room's timeline at all, which suits their short-lived nature. However, they
would leave no record to diagnose a failed call from, they need an Olm session with every device of
the inviter, and they do not reach devices the inviter adds later. As sticky room events, reports get
the same delivery guarantee as the invite they belong to.

## Security considerations

### Forged progress and outcomes

Any room member can send an `m.rtc.invite_progress` or `m.rtc.decline` event that references any
invite. Receivers MUST ignore both unless their sender is targeted by the referenced invite. This
prevents a third party from making a call look busy or unreachable.

`device_id` is asserted by the sender. A user can always misreport the state of their own devices, so
this only matters if one device of a user could impersonate another. In encrypted rooms, receivers
SHOULD discard an `m.rtc.invite_progress` event whose `device_id` does not match the device which
they have established as the sender of the Megolm session that encrypted it.

### Early media

An early member publishes media to the slot before answering, and could receive other members'
media before answering. The rule that an early member does not present other members' media until it
answers keeps media flowing backwards only, as in the PSTN, so that an unanswered phone cannot
overhear the caller. This rule is enforced by the early member's own client or bridge, not by the
protocol. A transport that supports it SHOULD also deny early members subscriptions until they answer.

A targeted user could also join early to play arbitrary audio to the inviter without ever answering.
Inviting clients only play an early member's media while an invite to that member's user is active,
which bounds this to the invite's `lifetime`.

### Digits into somebody else's IVR

`m.rtc.dtmf` lets a room member send digits into another member's IVR. The recipient MUST
only act on events whose sender and `device_id` are a current member of the slot, and SHOULD only
act on events from the member it is actually bridged to (in a direct chat, the other user; in a
group call, a member with a live leg to it), never from an arbitrary room member. In encrypted
rooms, recipients SHOULD discard an `m.rtc.dtmf` event whose `device_id` does not match the device
they have established as the sender of the Megolm session that encrypted it.

## Appendix: Comparison to [legacy VoIP]

These rows extend the comparison table in [MSC4075].

| Feature | Legacy VoIP | MatrixRTC |
| ------- | ----------- | --------- |
| Reason for an unanswered call | ⚠️ `user_busy` and `invite_timeout` on [`m.call.hangup`] | ✅ `no_answer` and `unreachable` in `decline_reason`, with SIP and Q.850 values |
| Ringing feedback to the caller | ❌ Not possible | ✅ via `m.rtc.invite_progress` events |
| Early media | ❌ Not possible | ✅ via early `m.rtc.member` events |
| DTMF | ✅ via [`m.call.dtmf`] events | ✅ via `m.rtc.dtmf` events, targeted at one member |

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
| Early media | ACM or CPG with in-band information | PROGRESS (in-band information available) | 183 Session Progress with SDP | Early `m.rtc.member` join publishing media |
| Answer | ANM or CON | CONNECT | 200 OK, ACK | Non-early `m.rtc.member` join |
| Caller abandons before answer | REL | DISCONNECT | CANCEL | Withdrawn `m.rtc.invite` with `withdraw_reason` `cancelled`, or redacted |
| Called party busy | REL, cause 17 | DISCONNECT, cause 17 | 486, 600 | `m.rtc.decline` with `busy` |
| Called party rejects | REL, cause 21 | DISCONNECT, cause 21 | 603 | `m.rtc.decline` with `declined` |
| No answer | REL, cause 19 | DISCONNECT, cause 19 | 480 or 408 after alerting | `m.rtc.decline` with `no_answer`, or `lifetime` expiry |
| Unreachable | REL, cause 1, 18, 20, 27, 34 or 38 | DISCONNECT, same causes | 404, 410, 480, 502, 503, 504 | `m.rtc.decline` with `unreachable` |
| Release after answer | REL, RLC | DISCONNECT, RELEASE | BYE | Leaving `m.rtc.member` with `leave_reason` `leave`; a two-party call then ends ([MSC4075]) |
| Reliable provisional responses | Inherent in the signalling link | Inherent | PRACK ([RFC 3262]) | Sticky events ([MSC4354]) |
| Parallel alerting of several terminals | — | — | Forking; the best final response wins | Per-device `m.rtc.invite_progress`; the first non-early join answers |
| Answered elsewhere | — | — | CANCEL with Reason "Call completed elsewhere" ([RFC 3326]) | ⚠️ Other devices see the join (see [stale notifications]) |
| Call identifier | CIC | Call reference | Call-ID | Call ID: event ID of the call's first `m.rtc.invite` ([MSC4075]) |
| Crossing setups (glare) | Dual seizure resolution | — | Two independent dialogs | Lowest invite event ID wins ([MSC4075]); media is unaffected |
| **Supplementary services** | | | | |
| Calling line identity | Calling party number, CLIP | Calling party number | From, P-Asserted-Identity | The sender's Matrix ID |
| Calling line identity restriction | CLIR | Presentation indicator | Privacy | ❌ Not covered |
| Call diversion | Redirection information | Redirecting number | 3xx, Diversion, History-Info | ❌ Not covered |
| Call transfer | ECT | — | REFER, Replaces | ⚠️ Invite a third party, then leave; no identity update |
| Call hold | CPG (remote hold) | HOLD, RETRIEVE | re-INVITE (`sendonly`) | ❌ Not covered; left to applications such as [MSC4196] |
| DTMF | In-band | INFORMATION, keypad | [RFC 4733], INFO | `m.rtc.dtmf` |
| Conference | Conference supplementary service | — | Conference focus | ✅ Inherent: a slot is a conference |
| Precedence and preemption | MLPP | MLPP | Resource-Priority ([RFC 4412]) | ❌ Not covered |

[Q.764]: https://www.itu.int/rec/T-REC-Q.764
[Q.931]: https://www.itu.int/rec/T-REC-Q.931
[H.225.0]: https://www.itu.int/rec/T-REC-H.225.0
[RFC 3261]: https://www.rfc-editor.org/rfc/rfc3261
[RFC 3262]: https://www.rfc-editor.org/rfc/rfc3262
[RFC 3326]: https://www.rfc-editor.org/rfc/rfc3326
[RFC 4412]: https://www.rfc-editor.org/rfc/rfc4412
[stale notifications]: #stale-notifications-on-other-devices

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.invite_progress` | Event type | `org.matrix.msc4075.rtc.invite_progress` |
| `no_answer`, `unreachable` | Values of `decline_reason.code` | `org.matrix.msc4566.no_answer`, `org.matrix.msc4566.unreachable` |
| `sip_status`, `q850_cause` | Properties of `decline_reason` | `org.matrix.msc4566.sip_status`, `org.matrix.msc4566.q850_cause` |
| `early` | Property of `member` in `m.rtc.member` | `org.matrix.msc4566.early` |
| `m.rtc.dtmf` | Event type | `io.element.call.dtmf` |
| `dtmf` | Value in `application.capabilities` of `m.rtc.member` | `dtmf` |

The unstable identifier for `m.rtc.invite_progress` uses the number of [MSC4075] because the event
was first implemented as part of that proposal before being split out into this one. `m.rtc.dtmf`
and the `dtmf` capability were implemented in Element Call and the MatrixRTC SIP bridge before this
proposal was written, hence their unstable identifiers.

## Dependencies

This proposal depends on [MSC4075], and through it on [MSC4143] and [MSC4354]. The `dtmf`
capability depends on [MSC4196].

## Appendix: Implementation status

The MatrixRTC SIP bridge and Element Web implement an earlier draft of this proposal. In that draft,
the sticky key of `org.matrix.msc4075.rtc.invite_progress` is the invite's event ID alone and a
free-text `reason` is used. There is also a `connected` state instead of an early membership, and
failures are reported only as progress rather than as a decline with a `decline_reason`.

The bridge relays `io.element.call.dtmf` as [RFC 4733] telephone-events and in-band tones, and
advertises `dtmf` in its membership's capabilities, for which Element Call offers a keypad. The
events it receives today carry only `digits`: `slot_id`, `device_id`, `target` and the timing
properties are new in this proposal. The bridge accepts both shapes, treating an event without
`target` as meant for the room's only bridged member, which is the direct chat case.
