# MSC4143: MatrixRTC – Real-time communication over Matrix

Matrix is a generalised protocol for decentralised communication. This includes chatting but also
real-time communication (RTC) such as VoIP. While Matrix supports VoIP signalling for [1-to-1 calls],
and [MSC3401] attempts to extend it to group calling, a unified system for RTC applications is
currently missing.

[1-to-1 calls]: https://spec.matrix.org/v1.18/client-server-api/#voice-over-ip
[MSC3401]: https://github.com/matrix-org/matrix-spec-proposals/pull/3401

The present proposal aims to close this gap by introducing "MatrixRTC", a generalised framework for
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
[LiveKit SFU] are proposed in [MSC4196: MatrixRTC voice and video calling application `m.call`] and
[MSC4195: MatrixRTC Transport using LiveKit Backend], respectively.

[LiveKit SFU]: https://docs.livekit.io/reference/internals/livekit-sfu/
[MSC4196: MatrixRTC voice and video calling application `m.call`]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196
[MSC4195: MatrixRTC Transport using LiveKit Backend]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195/changes

This proposal also doesn't cover notifications for RTC sessions. These are considered outside the core
protocol and are described in [MSC4075: MatrixRTC notifications & call ringing].

[MSC4075: MatrixRTC notifications & call ringing]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075

## Proposal

### Slots

MatrixRTC slots act as containers for MatrixRTC applications to run in. Slots are represented by
state events of type `m.rtc.slot` which means that they can only be created or modified by users
with sufficient power level. As described [below], participants can connect to slots by sending
`m.rtc.member` room events.

[below]: #membership

This design deliberately separates slot management, requiring higher power level, from slot
participation, requiring lower power level. This separation gives applications a robust surface
for conflict resolution, clear ownership of events, and flexibility across use cases such as
always-on spaces, scheduled meetings, or ephemeral conversations.

Slots are always tied to specific applications through their slot ID which acts as the `state_key`. 
The slot ID is constructed as:

```json5
slot_id = {application_type}#{application_slot_id} (= state_key)
```

`application_type` is the application's globally unique identifier. This identifier is defined
by the application's specification and MUST follow the [Common Namespaced Identifier Grammar][^nohash].

`application_slot_id` is the application-specific slot ID and enables applications to support
multiple parallel application instances per room. Again, the allowed values are defined by
the application's specification and MUST follow the [Common Namespaced Identifier Grammar]
but this time without the namespacing requirements[^nohash]. Additionally, the values should
be predictable for clients given that slots act like a virtual addresses where participants
are allowed to meet.

As an example, the default slot ID for the calling applications from [MSC4196: MatrixRTC voice and video calling application `m.call`]
is `m.call#ROOM`.

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
  - Optionally includes further properties for settings that are specific to the encryption
  `type`.

[encryption section]: #end-to-end-encryption

#### Closing a slot

To close a slot, the corresponding `m.rtc.slot` state event is updated with empty content.

```json5
{
  "type": "m.rtc.slot",
  "state_key": "{application_type}#{application_slot_id}", // = slot_id
  "content": {},
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
      "claimed_device_id": "{device_id}",
      "claimed_user_id": "{user_id}"
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
  connected on a slot. The exact procedure for subscribing to and publishing real-time data is
  defined in each transport's specification.
  - `published` (array): An array of objects describing the transports on which the participant is
    publishing media.
    - `type`: (required, string): The globally unique transport identifier. MUST follow the
      [Common Namespaced Identifier Grammar] but without the namespacing requirements.
    - Optionally includes further properties specific to the transport `type`. The concrete properties
      are defined by the transport's specification. An SFU-based transport, for instance, could include
      a WebSocket URL.
  - `can_subscribe` (array): An array of transport types that the participant is able to subscribe to.
- `sticky_key` (required, string): The sticky key for the ephemeral map algorithm as defined
  in the addendum of [MSC4354]. MUST have the same value as `member.id` field.

Apart from having to match the above schema, an `m.rtc.member` event MUST only be considered to be
connected if all of the following conditions apply:

- An open slot exists in the room as an `m.rtc.slot` state event with `state_key` equalling `slot_id`.
- The sender is still a member of the room (i.e. not kicked or left).
- The event is still sticky, meaning that its stickyness duration as per [MSC4354] has not expired.
  This is to ensure that the membership view is as consistent as possible across all participants.
  When a member event's stickiness expires, the associated delivery guarantee vanishes. As a result,
  some participants might not have received the event while others did. Treating the participant as
  connected in such cases would result in inconsistent views on the participating members.

If these conditions are not fulfilled, clients MUST treat the participant as disconnected and abort
or refrain from consuming the participant's transports.

#### Disconnecting from a slot

To consciously disconnect from a slot, the client sends an `m.rtc.member` event with the following
schema:

```json5
{
  "type": "m.rtc.member",
  "content": {
    "slot_id": "{application_type}#{application_slot_id}", // = m.rtc.slot state_key
    "disconnect_reason": {                 // SHOULD
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
  This should only be used if the user has actually attempted to connect to the slot before.
  This ensures that the `disconnect_reason` refers to a real connection lifecycle rather
  than pre-join cancellation.
  - `class` (required, string): High-level category of the disconnection or error. Must be on of:
    - `user_action`: The disconnect happened due to explicit user action (e.g. a hang up).
    - `client_error`: The client experienced a failure.
    - `server_error`: The server experienced a failure.
    - `redirection`: The connection was moved somewhere else (e.g. to a different slot).
    - `permanent_failure`: An unrecoverable failure occurred.
  - `reason` (required, string): Identifier for the specific disconnection cause. MUST follow
    the [Common Namespaced Identifier Grammar] but without the namespacing requirement. The
    concrete values are defined by the application's specification.
| `description` (string): Optional human-readable explanation of the disconnection reason.
- `sticky_key` (required, string): The sticky key for the ephemeral map algorithm as defined
  in the addendum of [MSC4354]. MUST have the same value as `member.id` field in the previously
  connected `m.rtc.member` event.

[^disconnect]: The structured design of `disconnect_reason` allows representing complex error situations
such as found in e.g. [SIP](https://en.wikipedia.org/wiki/List_of_SIP_response_codes) in an
accessible way.

Again, once a participant has disconnected, clients MUST abort or refrain from consuming the
participant's transports.

#### Membership lifecycle

The MatrixRTC membership lifecycle of a participant is a collection of subsequent `m.rtc.member` events.

1. Participants first connect to a slot by sending an `m.rtc.member` event in its connected form.
1. Afterwards, participants may update their membership, e.g. to change transports or modify
   application-specific settings, by sending a new `m.rtc.member` event with the same `sticky_key`.
   Since the actual connection state is constrained by the stickyness of the member event, clients
   also need to send new `m.rtc.member` events if they want to stay connected longer than the stickyness
   duration. It is RECOMMENDED that clients send these events sufficiently ahead of the stickyness
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
the delayed event to push it into the future. If the client loses connectivity and the delay
times out, the homeserver will send the disconnecting `m.rtc.member` event.

Some transports may involve external services with high visibility on participants' connection state
such as a Selective Forwarding Unit (SFU). Clients MAY delegate management of their delayed disconnect
event to such services. How exactly the delegation is performed is defined by the transport's
specification

[MSC4140]: https://github.com/matrix-org/matrix-spec-proposals/pull/4140

### MatrixRTC Session

A **MatrixRTC Session** is defined as the period of overlapping, **Connected** `m.rtc.member` events
that share the same slot identified by `slot_id`. In other words, a session represents the span of
time during which a potentially changing set of one or more participants is continuously connected
to the same MatrixRTC slot.

Note the Connected status of the m.rtc.member event is already bounded to an open slot

Example of a MatrixRTC session: This diagram illustrates overlapping member intervals defining the
MatrixRTC session lifetime, bounded by the slot being open.

```
                       Session Start                                       Session End
                           |                                                   |
m.rtc.member[0]            |████████████████████████   ████████████████████████|████
                           |^ connect   disconnect ^   ^ connect   disconnect ^|
                           |                                                   |
m.rtc.member[1]            |       ███████████████████████████████████████     |
                           |       ^ connect                  disconnect ^     |
                           |                                                   |
m.rtc.member[2]            |            ████████████████████████               |
                           |            ^ connect   disconnect ^               |
                           |                                                   |
Slot (open)          [*********************************************************]
                           |                                                   |
Session lifetime           [***************************************************]


Time               ───────────────────────────────────────────────────────────────────►
```

The lifetime of a MatrixRTC session is implicitly defined by the union of all **connected** member
intervals, bounded by the slot’s open and close times:

* **Session start:** the first member connects  
* **Session end:** the last connected member disconnects

#### On Session Identifiers

A MatrixRTC session identifier MAY be retrospectively derived by XORing the `event_id` of all
associated `m.rtc.member` events.

Alternatively, a pre-defined MatrixRTC session identifier MAY be included in the associated
`m.rtc.slot` state event. Because Matrix state events are always subject to state resolution,
applications MUST handle potential conflicts gracefully — for example, by rolling back conflicting
state changes or employing a coordination mechanism to prevent conflicts in the first place. A
typical implementation might involve a bot maintaining a Matrix room as the sole administrator,
opening a slot for a scheduled video conference, and including a unique `m.call.id` in the
`application` JSON object. When a pre-defined session identifier is used, only one MatrixRTC session
SHOULD exist within that slot.

In essence, *slots* exist to support concurrent RTC sessions within the same room. The sessions
within each slot may or may not have an stated session ID depending on whether the app is able to
switch ID mid-session (or display multiple concurrent sessions meaningfully).

* If an application supports switching or displaying multiple sessions concurrently, participants
  SHOULD explicitly declare the session they belong to.  
* If it does not (for example, in typical group VoIP scenarios), participants may omit a session ID
  and implicitly join the default, anonymous session associated with that slot.

**Implementation note:**  
This behavior may lead to user confusion in edge cases such as network partitions. For example,
users who thought they were in one session during a network partition and then find themselves
suddenly merged into another (unified) session, and so teleported into someone else’s conversation. 

A more robust design might require all calls to have explicit session identifiers. In cases where
conflicting identifiers are detected shortly after call setup, clients could tear down the local
session and converge on the session that wins the race.

If conflicts occur later during a session, the better user experience may be to treat them as two
concurrent calls within the same room, allowing users to choose which session to join. In practice,
this could be implemented as a prompt (e.g., *“There’s already a call happening — do you want to
join it?”*), potentially automated to accept by default when no other participants remain in the
local session.

#### Session history

As MatrixRTC does not emit a single event describing past sessions, historic MatrixRTC sessions MUST
be reconstructed from room history. Clients SHOULD cache reconstructed sessions to avoid repeated,
expensive history pagination.

In general, all required information is present as part of the Matrix DAG:

* **Sticky events** are persistently recorded in the Matrix DAG.  
* **`m.rtc.slot` state event transitions**, even when affected by state resolution, are visible as
  part of the timeline.

However, for this reconstruction process to work **reliably and deterministically**, the Matrix 
protocol requires **consistent message ordering (on a homeserver basis)** across both state and 
timeline events. This remains an open problem and is discussed further in the 
[*Impact of Message Ordering wrt. Session History*](#impact-of-message-ordering-wrt-session-history) 
section. As a temporary workaround, the reconstruction process uses `origin_server_ts` ordering.

General concept
* Paginate backward through room history to collect relevant events:  
  * `m.rtc.slot` events (slot open/close boundaries)  
  * `m.rtc.member` events (connects, updates, disconnects)  
* Correlate `m.rtc.slot` events with surrounding `m.rtc.member` events to reconstruct membership
  intervals.  
* Handle incomplete membership events: clients may fail to send proper connect/disconnect events;
  using slot boundaries helps limit incorrect membership data.

Note: due to the two-tier power level model (who may manage slots vs participation), using slot
boundaries to filter membership events is typically sufficient to avoid many classes of spurious or
invalid records.

Step-by-step reconstruction algorithm

1. Gather all `m.rtc.slot` events from the timeline and determine the slot open/close intervals
   (i.e. transitions where `m.rtc.slot` content becomes non-empty → slot open; becomes empty → slot
   closed).  
2. For each open slot interval \[`slot_start, slot_end`\], as given by `origin_server_ts` at the
   slot status transitions:  
   * Collect `m.rtc.member` events whose connect/update/disconnect activity intersects the slot
     interval.  
   * Cluster related `m.rtc.member` events by their `sticky_key`  
     * For each member event cluster the `membership_interval` \=  \[`membership_start,
       membership_end`\] is given by:  
       * `membership_start = max(start_slot_ts, start_content_ts)` as defined in [Lifecycle of a MatrixRTC Membership](#lifecycle-of-a-matrixrtc-membership)
       * `membership_end = min(end_slot_ts, end_content_ts, end_sticky_ts)` as defined in [Lifecycle of a MatrixRTC Membership](#lifecycle-of-a-matrixrtc-membership)
     * Drop all `membership_interval`s where `membership_start >= membership_end`.  
     * Merge all overlapping or contiguous `membership_interval`s into a single (continuous)
       interval `collection`. Within a given slot, **MatrixRTC sessions cannot overlap**; all
       intersecting intervals form a single unified session.  
3. For each `collection` of overlapping `membership_interval`s, a (historical) MatrixRTC session
   exists with the following properties:  
   * Slot identified by `slot_id` in the interval \[`slot_start, slot_end`\].  
   * Starts at `min(m.membership_start for m in collection)`  
   * Ends at `max(m.membership_end for m in collection)`  
   * Individual MatrixRTC membership intervals given by `((m.membership_start, m.membership_end) for m in collection)`

In general, there may be more than one `collection` of overlapping membership intervals, resulting
in multiple consecutive MatrixRTC sessions within a single slot.

### MatrixRTC Transport

MatrixRTC, by design, supports multiple transport implementations, each defined in its own MSC.
Transports describe how clients connect to peers or servers, manage connections, publish and
subscribe to media streams. A transport can represent different RTC backends such as SFUs, MCUs, or
full-mesh peer-to-peer topologies.

Currently, [MSC4195: MatrixRTC Transport using LiveKit backend](https://github.com/matrix-org/matrix-spec-proposals/pull/4195) 
is the primary proposal, while a full-mesh transport based on 
[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) is also planned. 
Each transport defines its connection model, supported topologies, and any additional requirements 
for participating clients.

#### Discovery of RTC Transports

MatrixRTC requires a mechanism for clients to discover which RTC transports — such as an SFU or TURN
server — are available in their Matrix deployment. To support this, homeservers expose an 
authenticated endpoint that returns a list of JSON objects. The endpoint is authenticated as the RTC
transport information is only useful to local clients; remote clients obtain transport information 
via `m.rtc.member` events. Each transport-description object represents an RTC transport as defined
by the corresponding MSC.

> [!NOTE]
> RTC Transports in this context can be anything that can serve as the backend for a MatrixRTC
> session. In most cases this is a SFU. But also a full mesh implementation could be a transport.
> Not all kinds of RTC transports require a way of sourcing a backend resource (e.g. a
> peer-to-peer-solution). In this MSC we only refer to transport where it is necessary to have
> access to additional data to participate in the MatrixRTC session.

The endpoint: `GET /_matrix/client/v1/rtc/transports` is used to expose a sorted (by priority) list
of Transport description objects.

Response format:

```json5
{
  "rtc_transports": [
    {
      "type": "some-transport-type",
      "additional-type-specific-field": "https://my_transport.domain",
      "another-additional-type-specific-field": ["with", "Array", "type"]
    }
  ]
}
```

Concrete example for a `livekit` transport:

```json5
{
  "rtc_transports": [
    {
      "type": "livekit",
      "livekit_service_url": "https://matrix-rtc.example.com/livekit/jwt"
    }
  ]
}
```

**Fields:**

* `rtc_transports` — array of transport-description representing the available RTC transports
  offered by the homeserver.  
* Each object in the array MUST conform to the JSON schema defined for its `type` (e.g.
  `livekit` in [MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195)).

Clients SHOULD use this list to determine which RTC transports to connect to and may advertise their
selected transports according to the respective MSC in the `rtc_transports` field of their
`m.rtc.member` events.

### End-to-end encryption

This section defines how key material is shared between participants in MatrixRTC to enable
end-to-end encryption of RTC data.

MatrixRTC sessions initiated in a **non-encrypted room** will remain non-encrypted. Sessions started
in **encrypted rooms** will be encrypted.

Every member in an encrypted MatrixRTC slot maintains a unique sender key, which is securely shared
with all other members. This sender key (secure random bytes) MUST be used by the RTC application to
derive and stretch any secrets they need to encrypt/authenticate the data/media uploaded by this
user. 

Keys are distributed to the RTC members. The RTC membership is based on top of the room membership
and inherits its security properties.

The key exchange depends on the underlying secure peer-to-peer olm channel (via to-device message)
for key distribution.

This ensures that only members in the RTC slot can decrypt data/media; other people, even if in the
room, will never get the key material.

The RTC transport MSC (e.g., 
[MSC4195: MatrixRTC Transport using LiveKit backend](https://github.com/matrix-org/matrix-spec-proposals/pull/4195)) 
specifies how the key material is actually used. For example, the RTC client may generate a secure
random 256-bit key, which the application can then use to derive the required secrets (using HKDF or
other key-stretching methods as appropriate).

#### Key Distribution

When joining a MatrixRTC slot, each participant shares a generated E2EE key with the other members
(`m.rtc.member`) of the same slot by sending an **encrypted** [Matrix to-device
message](https://spec.matrix.org/v1.11/client-server-api/#send-to-device-messaging). The key is
transmitted via an event of type `m.rtc.encryption_key`. The **target device ID** is taken from the
`member.claimed_device_id` field of the recipient’s `m.rtc.member` event. The event follows the following
schema:

```json5
// event type: "m.rtc.encryption_key"
{
    "room_id": "!roomid:matrix.domain",
    "member_id": "xyzABCDEF0123",
    "media_key": {
      "index": 10,
      "key": "base64encodedkey",
    },
    "version": "0"
}
```

**Field explanations:**

* `member_id` required string: The `member.id` from the target `m.rtc.member` event. Note, because
  `member.id` is globally unique per member instance, it is sufficient to disambiguate multiple key
  events for the same device, even if they use the same `media_key.index` value.  
* `media_key` The media key to use to decrypt  the participant media:  
  * `key` required string: The key material encoded using unpadded base64.
  * `index` required int: The index of the key to distinguish it from other keys. This must be
    between 0 and 255 inclusive. In some implementations of MatrixRTC this may correspond to the
    `keyID` field of the WebRTC [SFrame](https://www.w3.org/TR/webrtc-encoded-transform/#sframe)
    header.  
* `format` the key export format, `0` for the raw bytes encoded using unpadded base64.
* Depending on the RTC application, additional fields may be added to this event.

Upon receipt, any `m.rtc.encryption_key` to-device event sent in cleartext SHOULD be discarded. The
receiving client SHOULD use the Olm decryption metadata to determine the sender’s `user_id`,
`device_id`, and the device’s verification state. Sender information is considered *claimed* unless
the device is verified.

The client SHOULD apply the same acceptance policy for these to-device messages as it would for room
messages or session setup. For example, if the client is configured to *exclude insecure devices*,
then keys received from such devices MUST also be excluded.

The corresponding  `m.rtc.member` is determined by matching its `member.id` with the one from
`m.rtc.encryption_key`.

The receiving MUST apply the following checks:

- The `sender` property from the decryption result must match the `sender` of the `m.rtc.member`
  event.
- The `device_id` property from the decryption result must match the `device_id` of the `member.device_id`
  of `m.rtc.member` event.

Any `m.rtc.encryption_key` event that does not comply with these checks MUST be discarded.

Clients SHOULD rotate their keys to ensure **confidentiality** whenever a participant joins or
leaves the slot. The **key rotation** process is as follows:

* The sending client generates the new key material for the local participant.  
* The sending client sends the new key material to all other participants with a new `index` value.  
* The receiving client stores the new key material for the specified `index`.  
* The sending client continues to use the old/current key to encrypt media.  
* After a short delay `delayBeforeUse,` default: 5 seconds), the sending client switches to the
  new key.  
  * It is possible to overwrite the default delay on a per application basis in case an application
    has specific requirements on security or wants to minimize missed stream data  
  * Also negotiation can be used over data channels to confirm all participants have received the new key.

**Note:** Rotating a key will require to re-send a to-device message to all the participants, and
this is expensive. Clients SHOULD minimize key exchange traffic for rapid joiners/leavers. 

For rapid new joiners: A key rotation grace period (`keyRotationGracePeriod`) is used, if a new
member joins during the grace period, then the same key can be used and shared just to that new
member.

For rapid leavers: The `delayBeforeUse` period is used to coalesce any membership change occurring
in that period and then a single key rotation is scheduled afterward.

`keyRotationGracePeriod` must be greater than `delayBeforeUse` or it will have no effects (default
10s and 5s)

#### Shared Key alternative

For big calls in a room, it might be interesting to use a shared key system instead of a per-sender
key system.  
In order to use a shared key, a new encrypted room event (`m.rtc.shared_encryption_key`) should be
sent in the room, and the slot should be updated to include the `event_id` of the shared key event.

```json5
// Example: an open slot with shared key encryption
{
  "application": {
    "type": "m.call",
    // optional: app specific slot metadata
    "m.call.id": UUID,    
    "m.shared_key_event": "$000"
  }
}
state_key: "m.call#ROOM" // slot_id
```

The shared key event:

```json5
  "event_id": "$000",
  "origin_server_ts": 1759827668867,
  "type": "m.rtc.shared_encryption_key"
  "content": {
     "key": "base64encodedkey"
   },
```

**Pros**: Scales for big calls as there is no need to distribute n keys via to-device and to rotate
keys on joiner/leavers  
**Cons**: Less security, every room member (and future members) have the key materials even if they
didn’t actively join the call. No automatic key rotation, so if the shared key is compromised past
recording could be decrypted.

Only users with enough power level (moderator, admin) can update the slot in order to enable shared
keys call.

Clients should detect when the slot is configured for a shared key, and then use the shared key
instead of generating and sharing sender keys.

## Potential issues

### Shared State for a MatrixRTC Session using Matrix Primitives

In the context of Matrix’s eventual consistency, we evaluated options for representing shared state
in MatrixRTC and identified the following trade-offs:

* For a **conflict-free approach**:  
* We **avoid** shared state such as a session identifier altogether (at least not a priori).  
* Each participant state is independent, and the session is computed as the aggregate of
  `m.rtc.member` events.  
* This sacrifices the simplicity of a UUID-like session identifier but avoids rollback problems due
  to state resolution  
* A good example of this approach is a room-based call or videoconference where the set of active
  participants defines the session.  
* For **shared state** (e.g., introducing a session identifier that all participants agree on):  
  * In any distributed system, if multiple participants attempt the same action at the same time,
    there is a risk of *glare* (a race condition). One side will “win,” and the other may need to
    roll back. This is not specific to Matrix: it is a well-known problem across telephony protocols
    such as PSTN, GSM, SS7, SIP, or even early rotary exchanges.  
  * Using Matrix state resolution can lead to **rollbacks**, which is problematic for real-time
    communication, since rolling back is not matching the semantics of real-time.  
  * The Matrix protocol does **not provide a consensus primitive** to prevent such rollbacks.  
  * As a result, any shared state implementation must accept the possibility of rollbacks and handle
    them at the application layer.

From this we conclude: both approaches are valid within MatrixRTC:

* For the actual session state the **conflict-free** approach is well suited. It should be avoided
  to rollback calls and should not allow a participant to initiate such a rollback and break the
  current ongoing session.  
* For permissions and (shared) metadata, **shared state** is the desired concept. By decoupling the
  concept of a **session** (people communicating in a meeting room with a predefined `slot_id`) and
  the **context** itself (the slot), we can have a conflict-free session concept but a centrally
  managed context with potential state rollbacks that do not necessarily interfere with the session
  itself.

### Discovery and Negotiation of Application Types

MatrixRTC does not currently define how clients should discover or negotiate which real-time
applications are available in a given room or between users. For example, when placing a call, it is
unclear whether the client should offer a MatrixRTC application, legacy 1:1 VoIP, or a room widget
such as Jitsi. Even in the case of similar applications (e.g., multiple call-capable MatrixRTC
apps), the proposal does not specify how a client should decide which one to launch. Application
discovery and negotiation are therefore left to a future MSC.

### Interoperation Between Different RTC Transports

MatrixRTC currently lacks a defined mechanism for interoperability across different RTC backends
(e.g., SFUs, MCUs, peer-to-peer). As a result, all participants in the same slot must share at least
one common transport implementation. This can lead to fragmentation if clients or Matrix sites
support disjoint sets of transports. A more complete interop solution is left as future work.

### Impact of Message Ordering wrt. Session History

As described above, all information required to reconstruct historic MatrixRTC sessions is available
within the Matrix DAG:

* **Sticky events** are persistently recorded in the DAG.  
* **`m.rtc.slot` state event transitions**, even when affected by state resolution, are visible as
  part of the timeline.

However, for this reconstruction process to function **reliably and deterministically**, the Matrix
protocol requires **consistent message ordering** on a **homeserver basis** across both state and
timeline events.This homeserver-centric ordering is crucial: due to netsplits or federation delays,
the room state may temporarily diverge between homeservers, even though it will eventually converge.
A concept such as [stitched
ordering](https://codeberg.org/andybalaam/stitched-order/src/branch/main/msc/msc.md) would satisfy
these requirements. Furthermore, **state resolution results** — even though they do not need to be
persisted in the DAG — **must be presented to clients as part of the timeline**. This ensures an
immutable and complete historical view per homeserver.

To accurately represent RTC session history as perceived in-real-life by participants, ordering
should ideally rely on `received_server_ts` (which is not available today) rather than
`origin_server_ts`. While `origin_server_ts` can serve as a practical workaround for now, it does
not necessarily reflect the experienced order of events in the presence of latency, netsplits, or
federation lag.

Counterintuitively, **state resolution for `m.rtc.slot` is not a problem** — RTC sessions occur in
real life, and their existence remains valid regardless of how room state later resolves. What *is*
important, however, is that each `m.rtc.slot` event, at its position in the DAG, **satisfies the
applicable authorisation rules** at that point in time to ensure the reconstructed session history
is consistent with valid room state transitions.

### Excessive key traffic

When using per-user encryption keys, keys are rotated and distributed to _all_ participants
whenever a member joins or leaves the session. This could result in a large amount of to-device
messages being exchanged. This is deemed acceptable for now given that it should usually only
occur during session setup.

To mitigate this, a future version of the key exchange mechanism could introduce ratcheting. Rather
than rotating the key for all members, this would allow to ratchet the key and send it to the new
joiner only.

## Alternatives

### Represent MatrixRTC Members as regular Matrix State

Sticky events are used because they combine persistence with efficiency

* They do have similar delivery guarantees as state events and are reliably passed down the sync
  loop for the duration of their stickiness – no pagination required in the event of gappy syncs  
* They allow clients to compute the current membership (and session) state reliably without
  contributing to long-term room state bloating.  
* As they are persisted in the DAG like regular events, they can also be used to reconstruct
  previous sessions, supporting session history and retrospective analysis.

Furthermore and In contrast to Matrix room state (as of writing this MSC), sticky events can be
already encrypted improving security significantly. 

### Organising MatrixRTC Members (`m.rtc.member`)as an Array per User

[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) proposed to have one state
event per user with that state event containing an array of RTC memberships.

This introduces two problems:

- Potential inconsistency where one user device overwrites the state of another device during a
  concurrent update.  
- When handling client disconnects, [MSC4140 delayed events](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) **cannot
  reliably maintain an accurate membership state**. This is because, at the time a delayed event is
  scheduled, the current membership array may change before the event is actually emitted, making it
  impossible to predict the correct state in advance.

### Using the Device Name as State Key for MatrixRTC Members (`m.rtc.member`)

Using the client’s **device name** instead of `member.id` as the state key for the `m.rtc.member`
event may lead to **race conditions** if the same device joins a MatrixRTC slot multiple times.

This scenario is realistic in cases such as:

* multiple widgets joining the same slot to provide different perspectives on the session (e.g.,
  moderator view vs. participant view), or  
* a native mobile application establishing an additional connection (e.g., alongside a webview) for
  purposes such as screen sharing.

### Alternative Transport Provisioning Models

This MSC proposes that the Matrix site setup is also responsible for providing the MatrixRTC
infrastructure. However, other sources for providing MatrixRTC transport could be considered,
including:

* **A separate system not associated with a Matrix account.**  
  For example, users might require both a Matrix account and a separate “LiveKit provider” account.  
  This approach is difficult to achieve across federation, since all users participating in a
  MatrixRTC session would need an account at the external service provider.  
* **Client-provided transport.**  
  The client itself could define and operate the SFU used for a session.  
  This approach represents a middle ground but introduces several challenges: most users rely on a
  small number of popular clients, meaning only a handful of transport infrastructures would
  ultimately serve the majority of traffic.  
  This concentration makes the system harder to scale and raises questions about cost, governance,
  and accountability for maintaining the infrastructure.  
* **A centralized solution.**  
  A single shared service could provide transport for all MatrixRTC users.  
  While simple to deploy, this model is **not Matrix-idiomatic**, as it contradicts the
  decentralized design principles of the protocol.

In contrast, Matrix homeservers already have diverse answers to the question of infrastructure
provision — individuals, communities, and institutions independently operate homeservers for their
own reasons and at their own expense. Replicating this **distributed sustainability model** for
MatrixRTC transport remains the most natural direction.

### E2EE Key Distribution via Room Event (`m.rtc.encryption_keys`)

Earlier iterations of this MSC used an encrypted `m.rtc.encryption_keys` room event to distribute
the per-participant sender keys.

The encrypted content of the `m.rtc.encryption_keys` event was as follows:

```json5
{
    "session": {
      "application": "m.call",
      "id": ""
    },
    "member": {
      "id": "xyzABCDEF10123",
      "device_id": "DEVICEID",
      "user_id": "@user:matrix.domain"
    }.
    "keys": [
        {
            "index": 0,
            "key": "base64encodedkey"
        },
    ],
}
```

#### Issues Encountered

1. **Scalability Problems**
   - Generated high volumes of message traffic in rooms
   - Frequently hit rate limiting thresholds

2. **Timeline Pollution**
   - Introduced invisible events into the room timeline
   - Created notification noise depending on user settings
   - Negatively impacted backpagination experience

3. **Security Concerns**
   - Over-exposed call keys by sharing them with all room participants
   - Failed to limit key distribution to active call participants only (impossibility to rotate key on leaver)

### Transport discovery via .well-known

Rather than using a dedicated endpoint, homeservers could publish supported transports
via a `.well-known` document. This exposes transports to unauthenticated users, however,
which can be a security concern. Additionally, in enterprise deployments, `.well-known`
files are often not served by the homeserver itself and it can be bureaucratically complicated
to update entries under the top-level domain.

`GET /_matrix/client/v1/rtc/transports` avoids these issues and offers more flexibility for
future extensions such as user-specific transports.

## Extensibility considerations

This MSC introduces a completely new concept to Matrix. The proposal is designed to be as abstract
and flexible as possible. While it is expected to replace legacy Matrix calling mechanisms, it does
**not** attempt to replicate or redefine how traditional calls work. Instead, it focuses on modeling
the **core principles** required for real-time communication sessions.

The design process drew heavily from real-world use cases — most notably the multi-year [Element
Call](https://github.com/element-hq/element-call) project. Other RTC application types were also
examined to identify common requirements and to test whether the proposal could be naturally
extended to support Matrix’s broader ecosystem of use cases..

### Slot constraints

Additional constraints may be defined for the `m.rtc.slot` event. Examples could include:

* **matrix ID list** – Restricting participation to a specific set of users.  
* **power level constraint** – Limiting access based on user power levels or roles.

These and other potential constraints are **not** part of this MSC and will be addressed in a
follow-up proposal. However, this MSC has been designed to remain compatible with such extensions.
Future constraint definitions would likely exist alongside the `"application"` key within the
`m.rtc.slot` event structure.

### Chaining member events with relations

An earlier version of this proposal used `m.reference` relations to link updated `m.rtc.member`
events to the initial connect event.

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

A future proposal may tackle the problem of performant session history reconstruction, possibly
by using relations. This proposal does not add relations in order not to preclude such later attempts.

## Security considerations

### Discoverability of RTC Infrastructure

RTC infrastructure details are disseminated to all participants through `m.rtc.member` events. This
transparency means that anyone part of a MatrixRTC session can view and understand the
infrastructure, which could potentially lead to unauthorized resource use. However, each
infrastructure type defines its own authentication mechanisms, as detailed in its specific MSC.
These mechanisms may involve a service interacting with the homeserver to determine whether a user
is authorized to utilize the infrastructure.

### End-to-end media encryption key rotation lag

The proposed key rotation semantics does mean that a participant could continue to decrypt media
that was sent in the three seconds after leaving the session.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| ----------------- | ------- | --------------------|
| `m.rtc.slot` | Event type | `org.matrix.msc4143.rtc.slot` |
| `m.rtc.member` | Event type | `org.matrix.msc4143.rtc.member` |
| `m.rtc.shared_encryption_key` | Event type | `org.matrix.msc4143.rtc.shared_encryption_key` |
| `m.rtc.encryption_key` | To-device message event type | `org.matrix.msc4143.rtc.encryption_key` |
| `/_matrix/client/v1/rtc/transports` | Endpoint | `/_matrix/client/unstable/org.matrix.msc4143/rtc/transports` |

Servers may advertise support for the feature by listing `org.matrix.msc4143` in the `unstable_features`
section of the response to [`GET /_matrix/client/versions`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions).

Once this proposal completes FCP, servers may advertise support for the _stable_ identifiers by listing
`org.matrix.msc4143.stable` in `unstable_features`. Clients may use this while they are waiting for the
server to adopt a version of the spec that includes it.

## Dependencies

This proposal depends on [MSC4354 Sticky
Events](https://github.com/matrix-org/matrix-spec-proposals/pull/4354) to provide room state similar
semantics without the drawback of contributing to room state bloating. 

This proposal also depends on [MSC4140: Cancellable delayed
events](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) to provide a mechanism for
clients to ensure that they can update the room state even if they lose connection.
