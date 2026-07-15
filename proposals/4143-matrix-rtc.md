# MSC4143: MatrixRTC – Real-time communication over Matrix

Matrix is a generalised protocol for decentralised communication. This includes chatting but also
real-time communication (RTC) such as VoIP. While Matrix supports VoIP signalling for [1-to-1 calls],
and [MSC3401] attempts to extend it to group calling, a unified system for RTC applications is
currently missing.

[1-to-1 calls]: https://spec.matrix.org/v1.18/client-server-api/#voice-over-ip
[MSC3401]: https://github.com/matrix-org/matrix-spec-proposals/pull/3401

The present proposal aims to close this gap by introducing *MatrixRTC*, a generalised framework for
building RTC experiences on top of Matrix. At a high level, MatrixRTC consists of the following parts:

* **End-to-end encryption** provides a generic basis for encrypted media exchange and reuses existing
  Matrix primitives such as encrypted room and to-device messages.
* **Transports** define how participants exchange media streams. This can, for instance, happen
  peer-to-peer or through Selective Forwarding Unit (SFUs). Transports also determine how the generic
  end-to-end encryption is used in transport-specific encryption.
* **Applications** describe the type of RTC activity such as a call, a shared document, or a real-time
  game. Applications also define what types of transports they can work with and how media streams are used.
* **Slots** are represented in room state and govern what kind of applications may run, along with
  any needed configuration.
* **Membership** is expressed via room events and provides a record of who is participating in a slot,
  and under which transports.
* **Sessions** are formed only indirectly through the temporal overlap of connected members within
  a slot.

This MSC is concerned with the foundational MatrixRTC protocol and covers slots, membership, sessions and
end-to-end encryption. Applications and transports are treated as generic building blocks only. The proposal
defines how these components are plugged into the system while leaving the introduction of concrete applications
and transports to other proposals.

As first concrete instances, a voice- and video conferencing application and a transport based on the
[LiveKit SFU] are proposed in [MSC4196: MatrixRTC voice and video calling application `m.call`][MSC4196] and
[MSC4195: MatrixRTC Transport using LiveKit Backend][MSC4195], respectively.

[LiveKit SFU]: https://docs.livekit.io/reference/internals/livekit-sfu/
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196
[MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195

This proposal also doesn't cover notifications for RTC sessions. These are considered outside the core
protocol and are described in [MSC4075: MatrixRTC notifications & call ringing][MSC4075] and
[MSC4310: MatrixRTC decline m.rtc.decline][MSC4310].

[MSC4075]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075
[MSC4310]: https://github.com/matrix-org/matrix-spec-proposals/pull/4310

## Proposal

### Slots

MatrixRTC slots act as containers for MatrixRTC applications to run in. Slots are represented by
state events of type `m.rtc.slot` which means that they can only be created or modified by users
with sufficient power level. This design deliberately separates slot management from slot participation
which is introduced [below] and requires lower power level.

[below]: #membership

Slots are always tied to specific applications through their slot ID which acts as the `state_key`. 
The slot ID is constructed as:

```json5
slot_id = {application_type}#{application_slot_id} (= state_key)
```

`application_type` is the application's globally unique identifier. This identifier is defined
by the application's specification and MUST follow the [Common Namespaced Identifier Grammar].

`application_slot_id` is the application-specific slot ID and enables applications to support
multiple parallel application instances per room. Again, the allowed values are defined by
the application's specification and MUST follow the [Common Namespaced Identifier Grammar]
but this time without the namespacing requirements[^nohash]. Additionally, the values should
be predictable for clients given that slots act like virtual addresses where participants
are allowed to meet.

As an example, the default slot ID for the calling application from [MSC4196] is `m.call#ROOM`.

The grammar for forming slot IDs MUST NOT be used to parse the components out of a slot ID.
It exists only to namespace the `state_key`.

[Common Namespaced Identifier Grammar]: https://spec.matrix.org/v1.16/appendices/#common-namespaced-identifier-grammar

[^nohash]: Note that due the use of the [Common Namespaced Identifier Grammar](https://spec.matrix.org/v1.16/appendices/#common-namespaced-identifier-grammar),
neither `application_type` nor `application_slot_id` can contain the `#` character.

#### Opening a slot

A slot is opened by sending an `m.rtc.slot` state event with `state_key = slot_id` and the
following schema:

```json5
{
  "type": "m.rtc.slot",
  "state_key": "{application_type}#{application_slot_id}", // = slot_id
  "content": {
    "application": {
      "type": "{application_type}",
      ... // Further application-specific properties (if required)
    },
    "encryption": {
      "type": "{encryption_type}",
      ... // Further encryption-specific properties (if required)
    }
  },
  ...
}
```

- `application` (required, object): Describes the application that can run in this slot.
  - `type` (required, string): The globally unique application identifier. MUST follow the
    [Common Namespaced Identifier Grammar].
  - Optionally includes further properties for settings that are specific to the application
    `type`. The concrete properties are defined by the application's specification. A calling
    application, for instance, could include properties for constraining the call to be voice-only.
- `encryption` (optional, object): Describes the encryption mechanism to use in this slot. Further,
  details on the available mechanisms can be found in the [encryption section] below.
  - `type` (required, string): The globally unique identifier of the encryption mechanism.
    MUST follow the [Common Namespaced Identifier Grammar].
  - Optionally includes further properties for settings that are specific to the encryption
  `type`.

[encryption section]: #end-to-end-encryption

#### Closing a slot

To close a slot, the corresponding `m.rtc.slot` state event is updated by removing the `application`
object.

```json5
{
  "type": "m.rtc.slot",
  "state_key": "{application_type}#{application_slot_id}", // = slot_id
  "content": {
    // No application property
    "encryption": { ... }
  },
  ...
}
```

The semantics of open and closed slots for slot participation are described in the membership
event section [below].

#### Slot lifecycle

Slots may follow different lifecycles depending on the use case. For instance, a long-lived slot
that is kept open continually could power a Discord-style experience where participants can hop on
and hop off as desired. Scheduled conference meetings, in turn, could benefit from a time-bounded
slot that is only opened when the meeting starts and closed again afterwards.

For the time being, slots will have to be created manually. A future proposal may change the
defaults for newly created rooms to provide slots for standard RTC applications.

### Membership

Participation in slots is expressed via `m.rtc.member` room events. These events provide sufficient
metadata for other room members to connect to the same slot and to exchange media streams via the
chosen transports.

`m.rtc.member` events MUST be sent as sticky events as per [MSC4354: Sticky Events][MSC4354]. This
results in the same delivery guarantee that state events have which is highly desirable for RTC
experiences. At the same time, it avoids the drawbacks associated with state events. Further details
on this can be found in [MSC4354]. Clients MUST also implement the ephemeral map algorithm as defined
in the addendum of [MSC4354] to construct a state-like store of membership events.

[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354

#### Connecting to a slot

To connect to a slot, the client sends an `m.rtc.member` event with the following schema:

```json5
{
  "type": "m.rtc.member",
  "content": {
    "slot_id": "{application_type}#{application_slot_id}", // = m.rtc.slot state_key
    "application": {
      "type": "{application_type}",
      ... // Further application-specific properties (if required)
    },
    "member": {
      "id": "{member_id}",
      "claimed_device_id": "{device_id}"
    },
    "transports": {
      "published": [
        {
          "type": "{transport_type}",
          ... // Further transport-specific properties (if required)
        },
        ...
      ],
      "can_subscribe": [
        "{transport_type}",
        ...
      ]
    },
    "sticky_key": "{member_id}" // = member.id
  },
  ...
}
```

- `slot_id` (required, string): The `state_key` of the slot that is being connected to.
- `application` (required, object): Describes the application that is running in the slot.
  - `type` (required, string): The application's globally unique identifier; same as in `m.rtc.slot`.
  - Optionally includes further properties for settings that are specific to the application
    `type`. As in `m.rtc.slot`, the concrete properties are defined by the application's specification.
    For example, a [Third Room](https://thirdroom.io) application could include approximate map positions,
    allowing clients to avoid connecting to participants outside their area of interest.
- `member` (required, object): Information to identify the member.
  - `id` (required, string): Identifier to distinguish multiple participations, even for the same user
    and device. MUST be unique for each connection. This means that clients need to use a different
    identifier when disconnecting and then reconnecting to a slot. Transports can use `id` as the
    canonical participant identifier to help prevent leaking metadata such as user or device IDs to
    external services.
  - `claimed_device_id` (required, string) — Matrix device identifier. This is "claimed" because a
    receiving device has no way to tell if the event actually came from this device ID without the
    encryption envelope. The device ID is used to exchange encryption keys as explained later in the
    [encryption section].
- `transports` (object): Details on the MatrixRTC transports of this member. Other clients use the
  information in this object to determine how to connect to and exchange real-time data with this
  participant. Client should be prepared to connect to as many transports as there are members
  connected on a slot. The exact procedure for publishing and subscribing to real-time data is
  defined in each transport's specification.
  - `published` (array): An array of objects describing the transports on which the participant is
    publishing media.
    - `type`: (required, string): The globally unique transport identifier. MUST follow the
      [Common Namespaced Identifier Grammar] but without the namespacing requirements.
    - Optionally includes further properties specific to the transport `type`. The concrete properties
      are defined by the transport's specification. This could, for instance, include WebSocket URLs.
  - `can_subscribe` (array): An array of transport types that the participant is able to subscribe to.
- `sticky_key` (required, string): The sticky key for the ephemeral map algorithm as defined
  in the addendum of [MSC4354]. MUST have the same value as `member.id`.

Apart from having to match the above schema, an `m.rtc.member` event MUST only be considered to be
connected if all of the following conditions apply:

- An open slot exists in the room as an `m.rtc.slot` state event with `state_key` equalling `slot_id`.
- The sender is still a member of the room (i.e. not kicked or left).
- The event is still sticky, meaning that its stickiness duration as per [MSC4354] has not expired.
  This is to ensure that the membership view is as consistent as possible across all participants.
  When a member event's stickiness expires, the associated delivery guarantee vanishes. As a result,
  some participants might not have received the event while others did. Treating the participant as
  connected in such cases would result in inconsistent views on the participating members.

If these conditions are not fulfilled, clients MUST treat the participant as disconnected and refrain
from sending them encryption keys and consuming their transports.

#### Disconnecting from a slot

To consciously disconnect from a slot, the client sends an `m.rtc.member` event with the following
schema:

```json5
{
  "type": "m.rtc.member",
  "content": {
    "slot_id": "{application_type}#{application_slot_id}", // = m.rtc.slot state_key
    "disconnect_reason": {
      "class": "{class}",
      "reason": "{reason}",
      "description": "{description}",
    },
    "sticky_key": "{member_id}" // = member.id from previously connected m.rtc.member event
  },
  ...
}
```

- `slot_id` (required, string): The `state_key` of the slot that is being disconnected from.
- `disconnect_reason` (object): Optionally provides context on why the client disconnected[^disconnect].
  This SHOULD only be used by clients if the user has actually attempted to connect to the slot before.
  This ensures that the `disconnect_reason` refers to a real connection lifecycle rather
  than pre-join cancellation.
  - `class` (required, string): High-level category of the disconnection or error. Must be one of:
    - `user_action`: The disconnect happened due to explicit user action (e.g. a hang up).
    - `client_error`: The client experienced a failure.
    - `server_error`: The server experienced a failure.
    - `redirection`: The connection was moved somewhere else (e.g. to a different slot).
    - `permanent_failure`: An unrecoverable failure occurred.
  - `reason` (required, string): Identifier for the specific disconnection cause. MUST follow
    the [Common Namespaced Identifier Grammar] but without the namespacing requirement. The
    concrete values are defined by the application's specification.
  - `description` (string): Optional human-readable explanation of the disconnection reason.
- `sticky_key` (required, string): The sticky key for the ephemeral map algorithm as defined
  in the addendum of [MSC4354]. MUST have the same value as `member.id` in the previously
  connected `m.rtc.member` event.

[^disconnect]: The structured design of `disconnect_reason` allows representing complex error situations
such as found in e.g. [SIP](https://en.wikipedia.org/wiki/List_of_SIP_response_codes) in an
accessible way.

Again, once a participant has disconnected, clients MUST refrain from sending them encryption keys
and consuming their transports.

#### Membership lifecycle

The MatrixRTC membership lifecycle of a participant is a collection of subsequent `m.rtc.member` events.

1. Participants first connect to a slot by sending an `m.rtc.member` event in its connected form.
1. Afterwards, participants may update their membership, e.g. to change transports or modify
   application-specific settings, by sending a new `m.rtc.member` event with the same `sticky_key`.
   Since the actual connection state is constrained by the stickiness of the member event, clients
   also need to send new `m.rtc.member` events if they want to stay connected longer than the stickiness
   duration. It is RECOMMENDED that clients send these events sufficiently ahead of the stickiness
   expiration to minimize potential connection state flickering.
1. Finally, to disconnect from the slot, participants send an `m.rtc.member` event in its disconnected form.

As explained above, the resolved connection state is also constrained by the associated `m.rtc.slot`
event existing and being open. Since `m.rtc.slot` events may generally be changed at any time, clients
MUST constantly react to and respect the latest known `m.rtc.slot` event.

One problem with the membership lifecycle as listed above is that a client may not be able to
send its disconnecting `m.rtc.member` event if it loses network connectivity. This would result
in other participants considering the member as still connected, possibly for longer periods,
even though no media can be exchanged. To mitigate the impact of this, clients SHOULD use
delayed events as per [MSC4140: Cancellable delayed events][MSC4140] to implement a "dead man's switch".
This means scheduling the `m.rtc.member` disconnection event as a delayed event with a reasonably
short delay (e.g. 15-30 seconds). While being connected, the client can periodically restart
the delayed event to push it into the future. If the client then happens to lose connectivity
and the delay times out, the homeserver will automatically send the disconnecting `m.rtc.member` event.

[MSC4140]: https://github.com/matrix-org/matrix-spec-proposals/pull/4140

### Sessions

MatrixRTC sessions only exist indirectly through the temporal overlap of `m.rtc.member` events
that are considered to be connected to the same `m.rtc.slot` event. In other words, a session
represents the span of time during which a potentially changing set of one or more participants
is continuously connected to the same slot.

The examples below illustrate how different membership lifecycles and slot configurations
lead to sessions.

```
m.rtc.member[0]            |████████████████████████            ████████████████████████|████
                           |^ connect   disconnect ^            ^ connect   disconnect ^|
                           |                                                            |
m.rtc.member[1]            |       ████████████████████████████████████████████████     |
                           |       ^ connect                           disconnect ^     |
                           |                                                            |
Slot (open)          [******************************************************************]
                           |                                                            |
Session lifetime           [************************************************************]

Time                 ───────────────────────────────────────────────────────────────────────►
```

```
m.rtc.member[0]        ████|███████████████████████████|    |███████████████████████████|
                           |^ connect      disconnect ^|    |^ connect      disconnect ^|
                           |                           |    |                           |
m.rtc.member[1]            |  ████████████████████████ |    | ████████████████████████  |
                           |  ^ connect   disconnect ^ |    | ^ connect   disconnect ^  |
                           |                           |    |                           |
Slot (open)                [******************************************************************]
                           |                           |    |                           |
Session lifetime           [***************************|    |***************************]

Time                 ───────────────────────────────────────────────────────────────────────►
```

### Discovery of transport infrastructure

Some RTC transports may require server-side infrastructure such as SFUs or TURN servers. Clients
need a mechanism to discover the availability of such infrastructure and any potentially required
connection details. To enable this, a new authenticated Client-Server endpoint
`GET /_matrix/client/v1/rtc/transports` is introduced. The endpoint returns the available
server-supported transport types:

```json5
// 200 OK
// Content-Type: application/json

{
  "rtc_transports": [
    {
      "type": "{transport_type}",
      ... // Further transport-specific properties (if required)
    }
  ]
}
```

- `rtc_transports` (required, array): Array of objects describing the transports the homeserver
  supports. Elements in the array are sorted descendingly by preference.
  - `type`: (required, string): The globally unique transport identifier. MUST follow the
    [Common Namespaced Identifier Grammar] but without the namespacing requirements.
  - Optionally includes further properties specific to the transport `type`. The concrete properties
    are defined by the transport's specification.

### End-to-end encryption

`m.rtc.member` events MUST be encrypted when sent in an encrypted room. Seperately from this, the
process of encrypting the RTC data itself is generally specific to the transport being used.
Additionally, participants need to agree on the key material so that the data can be decrypted again.
To support this, MatrixRTC provides a generic system for establishing shared key material between
participants. Transports can then define how to actually use this key material which may involve
deriving further secrets from it.

The concrete mechanism for agreeing on the shared key material within a slot is prescribed through
the `encryption` object in `m.rtc.slot` events. Clients SHOULD enforce the use of encryption when
opening a slot in encrypted rooms. When a client observes encryption being enabled in an `m.rtc.slot`
event, it SHOULD set a flag to indicate that connections to this slot should be encrypted. This flag
SHOULD NOT be cleared if a later `m.rtc.slot` event disables encryption. In other words, once encryption
is enabled on a slot, it can never be disabled. This is to avoid a situation where a MITM can simply
ask participants to disable encryption.[^e2eeguide]

[^e2eeguide]: This is aligned with the recommendation for handling the `m.room.encryption` state
              event for normal room messaging in https://matrix.org/docs/matrix-concepts/end-to-end-encryption.

The only available mechanism for now is `m.per_participant`.

```json5
{
  "type": "m.rtc.slot",
  "content": {
    "encryption": {
      "type": "m.per_participant"
    },
    ...
  },
  ...
}
```

Under `m.per_participant` every participant maintains a unique sender key. This key is shared securely
with other participants via encrypted [to-device messages]. The RTC membership of participants is based
on their room membership and inherits its security properties. Additionally, the to-device messages
rely on secure peer-to-peer Olm channels. This ensures that keys are only distributed among participants
of the slot. Other devices, even if in the room, never get the key material.

[to-device messages]: https://spec.matrix.org/v1.18/client-server-api/#send-to-device-messaging

#### Distributing keys

When connecting to a slot, clients generate a 16-byte cryptographically secure key. They then share
the key with other clients participating in the slot by sending encrypted to-device messages of the
type `m.rtc.encryption_key`.

The recipient devices are determined from the `m.rtc.member` events that are considered to be
connected to the slot. The conditions for considering a participant connected were given
[above](#connecting-to-a-slot). Once connected participants are determined, the target device ID
is taken from the `member.claimed_device_id` property of the respective `m.rtc.member` event.

```json5
// PUT /_matrix/client/v3/sendToDevice/m.rtc.encryption_key/{txnId} 

{
    "room_id": "{room_id}",
    "member_id": "{member_id}",
    "media_key": {
      "index": {index},
      "key": "{encoded_key}",
    },
    "version": "0"
}
```

- `room_id` (required, string): The ID of the room that the slot is located in.
- `member_id` (required, string): The `member.id` value of the target's `m.rtc.member` event.
  Note that because `member.id` is unique per participant, it is sufficient to disambiguate multiple
  key events for the same device.
- `media_key` (required, object): Information on the key to use to decrypt the sender's media.
  - `key` (required, string): The key (16 bytes) encoded as specified by `format`.
  - `index` (required, number): The rolling index of the key to distinguish it from other keys. The
    value MUST be between 0 and 255 inclusive. WebRTC-based transports may use this as the `keyID`
    field of [SFrame](https://www.w3.org/TR/webrtc-encoded-transform/#sframe) headers.
- `format` (required, number): The format in which the key was exported. Only `0` is allowed for now
  and implies that the key's raw bytes were encoded using unpadded base64.

Upon receipt, clients SHOULD discard any `m.rtc.encryption_key` events that were sent in cleartext.

Receiving clients can determine the corresponding `m.rtc.member` event by matching its `member.id`
with the value of `member_id` in the `m.rtc.encryption_key` message. Once the member event was determined,
clients perform the following checks:

- The `sender` property from the decryption result must match the `sender` of the `m.rtc.member`
  event.
- The `device_id` property from the decryption result must match the `member.claimed_device_id`
  value of the `m.rtc.member` event.

Any `m.rtc.encryption_key` event that does not pass these checks MUST be discarded.

In keeping with [MSC4153: Exclude non-cross-signed devices][MSC4153], clients SHOULD also discard
`m.rtc.encryption_key` events when the sending device is not cross-signed.

[MSC4153]: https://github.com/matrix-org/matrix-spec-proposals/pull/4153

#### Rotating keys

To ensure confidentiality, clients SHOULD rotate and redistribute their key whenever the set of
participants that are considered connected to the slot changes. This prevents connecting/disconnecting
participants from decrypting past/future RTC data.

Additionally, clients SHOULD also rotate their key on a periodic schedule regardless of whether
the participants have changed. This limits the impact of compromised keys.

In order to account for the delivery latency of to-device messages, clients SHOULD add a short
delay between sending a new key and starting to use it. Otherwise, receiving participants may
be unable to decrypt the sender's streams temporarily. The RECOMMENDED delay duration is 5 seconds.

Furthermore, resending to-device messages to all participants can be expensive when multiple
participants connect and/or disconnect in short succession. To mitigate this, clients MAY apply
some flexibility to exactly when a rotation happens relative to a membership change. This means
accepting a small window in which joining or leaving participants could decrypt media that is
slightly outside their actual membership period in exchange for fewer key rotations.

As an example, let's assume a client applies the time interval `delay = 5s` between rotating a key
and starting to use it for encryption. When participants disconnect during `delay`, the client
could schedule another rotation for when `delay` has elapsed. This coalesces multiple participant
changes into a single rotation and avoids excessive key rotations when multiple disconnections
occur in short succession.

```
         A disconnects                   delay period ends               delay period ends
         → generate key n+1              → generate key n+2              → switch to key n+2
         → send to everyone              → send to everyone              │
         │                               │                               │
         ▼                               ▼                                ▼
time ────●───────────────────────────────●───────────────────────────────●───────────────────────────────▶
         t=0     ▲                  ▲    t=5s                            t=10s
                 │                  │
                 B disconnects      C disconnects
                 → invalidate
                   key n+1

encrypts ├──────────── key n ────────────┼─────────── key n+1 ───────────┼─────────── key n+2 ───────────▶
with
         ├────────── delay (5s) ─────────┤────────── delay (5s) ─────────┤
```

As another example, a client could additionally introduce a grace period `grace = 10s`. When a participant
connects within `grace` after a new key `k` was created, the client could skip rotating the key again and
instead share `k` with the new participant.

```
         A connects                delay period ends         grace period ends
         → generate key n+1        → switch to key n+1
         → send to everyone
         │                         │                         │
         ▼                         ▼                         ▼
time ────●─────────────────────────●─────────────────────────●───────────────────────────▶
         t=0          ▲            t=5s         ▲            t=10s        ▲
                      │                         │                         │
                      B connects                C connects                D connects
                      → send key n+1            → send key n+1            → generate key n+2
                        to B                      to C                    → send to everyone

encrypts ├───────── key n ─────────┼───────── key n+1 ───────────────────────────────────▶
with
         ├────── delay (5s) ───────┤                                      ├────── delay ...
         ├─────────────────── grace (10s) ───────────────────┤            ├────── grace ...
```

## Potential issues

### Shared state

In any distributed system, if multiple participants operate on the same shared state at the same
time, there is a risk of *glare* (a race condition). One side will win and the other may need to
roll back. This is not specific to Matrix. It is a well-known problem across telephony protocols
such as PSTN, GSM, SS7, SIP, or even early rotary exchanges.

MatrixRTC minimises but doesn't fully avoid shared state.

On the one hand, `m.rtc.member` events are conflict-free. Each participant's membership state is
independent and the session is computed ad-hoc and without session identifiers as the aggregate
of `m.rtc.member` events. Most importantly, normal participants cannot cause conflicts that would
break an ongoing session.

On the other hand, `m.rtc.slot` events are subject to state resolution which can lead to rollbacks
and ongoing sessions breaking. Slots are only used for administration, however, where shared state
is actually desired. They should generally see far lower usage than membership events and exhibit
a low potential for conflicts.

### Discovery and negotiation of application types

MatrixRTC does not currently define how clients should discover or negotiate which real-time
applications are available in a given room or between a set of users. For example, when multiple
calling-capable applications exist, it is unclear which of them clients should offer for making a call.
The impact of this is limited for now as only a single application exists with [MSC4196]. Therefore,
introducing a scheme for application discovery and/or negotiation is left to a future proposal.

### Interoperation between different transports

MatrixRTC currently lacks a mechanism for interoperability across different RTC transports. As a
result, participants of a slot must share at least one common transport implementation. When clients
support disjoint sets of transports, this can lead to fragmentation. This shortcoming has limited impact
for now since only a single transport exists with [MSC4195]. Ensuring compatibility in a multi-transport
setup is, therefore, left as a problem for a future proposal.

### Accurate session reconstruction

Historic MatrixRTC sessions can technically be reconstructed from `m.rtc.slot` and `m.rtc.member`
events in room history. However, to accurately represent RTC session history as perceived by participants
at the time, events would require a `received_server_ts` which is, however, not available today. While
`origin_server_ts` could serve as a practical workaround, it does not necessarily reflect the
experienced order of events which might differ per homeserver due to netsplits or federation delays.
This problem is aggravated by the fact that the [/messages] endpoint used for back-pagination returns
events in topological order.

Additionally, clients currently have no way to query the room state as observed by their homeserver
over time. As a result, they cannot identify historic state resets which, for instance, might have
caused participants to suddenly consider a slot closed rather than open.

Due to these complications, accurately reconstructing session history is left as a consideration for a
future proposal.

[/messages]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3roomsroomidmessages

### Excessive key traffic

In per-participant encryption, keys are rotated and distributed to _all_ participants whenever a
member joins or leaves the session. This could result in a large amount of to-device messages being
exchanged. This is deemed acceptable for now given that it should usually only occur during session
setup.

To further mitigate this, a future version of the key exchange mechanism could introduce ratcheting.
Rather than rotating the key for all members, this would allow to ratchet the key and send it to the
new joiner only.

## Alternatives

### Slot constraints

Additional constraints such as restricting participation to a specific set of users could be added
to slots. These have been descoped from this proposal and may be introduced by a future MSC.

### Using room state instead of sticky events for membership

Earlier iterations of MatrixRTC used room state rather than sticky events to represent session membership.
The advantages of sticky events over state events may be found in [MSC4354] and are not repeated here.

### Maintaining membership in one event per user

[MSC3401] proposed to use one state event per user with that event containing an array of RTC memberships.
This is suboptimal as it introduces the possibility of race conditions when the event is written from
different devices. Furthermore, a joint membership event is difficult to combine with delayed disconnect
mechanisms as the remaining members at the time of disconnecting would have to be known ahead of time.

### Chaining member events with relations

An earlier version of this proposal used `m.reference` relations to link updated `m.rtc.member`
events to the initial connecting event.

```
(Connect)        (Update)              (Disconnect)     (Reconnect)      (Update)

m.rtc.member ──► m.rtc.member ─ ... ─► m.rtc.member     m.rtc.member ──► m.rtc.member ─ ...
      ^                │                     │                ^                │
      ├────────────────┘                     │                └────────────────┘
      │      m.reference                     │                       m.reference
      └──────────────────────────────────────┘
                                  m.reference

Time ─────────────────────────────────────────────────────────────────────────────────────►
```

This was meant to assist in reconstructing historical sessions accurately. However, the relations
turned out to not be helpful because finding the slot as well as other participants' member events
still required manual history traversal while employing timestamp overlap logic.

### Transport provisioning models

This proposal requires the server-side Matrix deployment to also provide the MatrixRTC transport
infrastructure. Alternatives that were considered and discarded include:

* A transport system separate from Matrix accounts
  Users could obtain an account with a separate service provider for the RTC transport infrastructure.
  This is difficult to achieve across federation, however, since all users participating in a session
  would need an account with the same external service provider.  
* Client-provided transports
  Clients themself could define and operate transport infrastructure such as SFUs. This is problematic
  because most users rely on a relatively small number of popular clients. Consequently, a low number of
  transport backends would have to cover the majority of traffic which makes the system harder to scale
  and raises questions around cost, governance, and accountability for infrastructure maintenance.
* Centralized infrastructure
  A single shared service could provide transport infrastructure for all MatrixRTC users. This creates
  a single point of failure though. It's also unclear what entity would operate such a service.

### Transport discovery via .well-known

Rather than using a dedicated endpoint, homeservers could publish supported transports via a `.well-known`
document. This exposes transports to unauthenticated users, however, which can be a security concern.
Additionally, in enterprise deployments, `.well-known` files are often not served by the homeserver itself
and it can be bureaucratically complicated to update entries under the top-level domain.

`GET /_matrix/client/v1/rtc/transports` avoids these issues and offers more flexibility for future extensions
such as user-specific transports.

### Key distribution via room events

Earlier iterations of this MSC used an encrypted room event to distribute per-participant encryption
keys. This turned out to be problematic due to homeservers rate-limiting message sending, timelines
being polluted with invisible events and, most importantly, the keys being shared across all room
participants rather than just the session participants.

#### Shared key encryption

For large calls an encryption scheme based on a shared key instead of per-sender keys could be more
efficient. This would obviously weaken security properties though. A future proposal may consider the
tradeoff and introduce a shared-key system via a new encryption `type`.

## Security considerations

### Discoverability of RTC infrastructure

Details of the server-side RTC infrastructure may be disclosed to all room members through `m.rtc.member`
events. This could lead to abuse and unauthorized resource use. Guarding against this generically is not
feasible, however. Instead, each transport mechanism needs to consider its security and required
authentication mechanisms.

### Encryption key rotation lag

The recommended key rotation behaviour may allow participants to decrypt media for a short time interval
before connecting and after disconnecting. This is deemed an acceptable compromise to reduce the performance
impact of key exchange.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.slot` | Event type | `org.matrix.msc4143.rtc.slot` |
| `m.rtc.member` | Event type | `org.matrix.msc4143.rtc.member` |
| `m.rtc.encryption_key` | To-device message event type | `org.matrix.msc4143.rtc.encryption_key` |
| `/_matrix/client/v1/rtc/transports` | Endpoint | `/_matrix/client/unstable/org.matrix.msc4143/rtc/transports` |

Servers may advertise support for the feature by listing `org.matrix.msc4143` in the `unstable_features`
section of the response to [`GET /_matrix/client/versions`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions).

Once this proposal completes FCP, servers may advertise support for the _stable_ identifiers by listing
`org.matrix.msc4143.stable` in `unstable_features`. Clients may use this while they are waiting for the
server to adopt a version of the spec that includes it.

## Dependencies

This proposal depends on [MSC4354: Sticky Events][MSC4354] and [MSC4140: Cancellable delayed events][MSC4140].
