# MSCxxxx: DTMF for MatrixRTC

[MSC4143] describes who is in a MatrixRTC session and where the media is. Once a Matrix user is
talking to a bridged phone there is no way to send `1` to an IVR, enter a conference PIN or navigate
a voicemail menu. [Legacy VoIP] had [`m.call.dtmf`]; MatrixRTC has nothing, and the member that
needs it is always one standing in for a non-Matrix endpoint, which on SIP turns the digits into
[RFC 4733] telephone-events or in-band tones. Between Matrix clients DTMF is meaningless, so this
proposal is deliberately narrow: a point-to-point event aimed at one member of the session, ignored
by everyone else, and a capability for such members to advertise so that clients know when to show
a keypad.

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[legacy VoIP]: https://spec.matrix.org/v1.19/client-server-api/#voice-over-ip
[`m.call.dtmf`]: https://spec.matrix.org/v1.19/client-server-api/#mcalldtmf
[RFC 4733]: https://www.rfc-editor.org/rfc/rfc4733

## Proposal

### The `m.rtc.dtmf` event

The schema of `m.rtc.dtmf`, a message-like room event sent in the room of the session, is as follows:

- `slot_id` (required, string): The `state_key` of the `m.rtc.slot` event the session takes place
  in, as in `m.rtc.member`. A recipient not joined to that slot ignores the event.
- `member_id` (required, string): The `member.id` of the sender's `m.rtc.member` event in the slot,
  so that the recipient can match the event to the sender's membership and its media.
- `target` (required, object): The member the digits are for. Other members MUST ignore the event.
  This is not `m.mentions`: the event never notifies anyone.
  - `user_id` (required, string): The target member's Matrix ID.
  - `member_id` (optional, string): Narrows the target to one of that user's memberships. MAY be
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
    "member_id": "xyzABCDEF0123",
    "target": {
      "user_id": "@_sip_441onelondon:example.org",
      "member_id": "SIPBRIDGE0001"
    },
    "digits": "1#",
    "duration_ms": 100,
    "gap_ms": 70
  }
}
```

The recipient applies the event only if the sender is a current member of the slot. A stale event
from a membership that has since left is dropped. It relays the digits to the endpoint it stands in
for, as [RFC 4733] events or in-band tones, whichever its leg negotiated. Digits are played after any
already queued from the same sender, never interleaved. There is no acknowledgement: a sender that
wants to know whether the far end reacted has the audio.

`m.rtc.dtmf` MUST be sent encrypted when the room is encrypted. Nothing in it needs to be readable
by the server, and digits are as sensitive as the call audio they are part of, such as a PIN typed
into an IVR. Clients SHOULD hide the event from the timeline, and no push rule is introduced for it.

[RFC 3966]: https://www.rfc-editor.org/rfc/rfc3966

### Advertising a keypad

A member that can act on `m.rtc.dtmf` advertises this by including `dtmf` in the `capabilities`
list of its `m.rtc.member` event's `application` object, as defined for `m.call` in [MSC4196]. A
client SHOULD offer a keypad only while some other member joined to the slot advertises `dtmf`, and
SHOULD send the digits to that member. A recipient that does not understand the event ignores it.

[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196

## Potential issues

### Timeline noise

Each keypress, or batch of keypresses, is a room event. Clients are asked to hide them, and they are
short-lived in meaning, but they remain in the room's history. A client SHOULD batch digits typed in
quick succession into one event where latency allows.

### Several bridged members

In a group session with more than one member advertising `dtmf`, a client has to let the user pick
which one the digits go to, or send to all of them. This proposal leaves the choice to the client.

## Alternatives

### Sending DTMF as to-device messages

To-device messages would keep the digits out of the timeline and avoid `target`. But the room is
where the session is, DTMF to a device one is not in a session with is meaningless anyway, and
to-device delivery gives no ordering with the session's other events.

### Reusing legacy `m.call.dtmf`

Its `call_id` and `party_id` describe legacy VoIP signalling, not slots and memberships.

### Sending DTMF over the transport

A data channel of the transport, such as a LiveKit data track, would work within one SFU but not
across federated foci, and would tie the application to one transport.

### Sending in-band tones in the audio

A client could synthesise DTMF tones into its own audio track, as a phone does. This depends on the
audio codec and processing chain preserving them (Opus with voice activity detection and noise
suppression often does not), and gives the bridge nothing to turn into [RFC 4733] events, which is
what most SIP peers expect.

## Security considerations

`m.rtc.dtmf` lets a room member send digits into another member's IVR. The recipient MUST
only act on events whose sender and `member_id` are a current member of the slot, and SHOULD only
act on events from the member it is actually bridged to (in a direct chat, the other user; in a
group session, a member with a live leg to it), never from an arbitrary room member.

`member_id` is asserted by the sender. This only matters if one device of a user could impersonate
another, which [MSC4143] already accepts for `member.id` itself.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.dtmf` | Event type | `io.element.call.dtmf` |
| `dtmf` | Value in `application.capabilities` of `m.rtc.member` | `dtmf` |

`m.rtc.dtmf` and the `dtmf` capability were implemented in Element Call and the MatrixRTC SIP
bridge before this proposal was written, hence their unstable identifiers.

## Dependencies

This proposal depends on [MSC4143]. The `dtmf` capability depends on [MSC4196].

## Appendix: Implementation status

The MatrixRTC SIP bridge relays `io.element.call.dtmf` as [RFC 4733] telephone-events and in-band
tones, and advertises `dtmf` in its membership's capabilities, for which Element Call offers a
keypad. The events it receives today carry only `digits`: `slot_id`, `member_id`, `target` and the
timing properties are new in this proposal. The bridge accepts both shapes, treating an event
without `target` as meant for the room's only bridged member, which is the direct chat case.
