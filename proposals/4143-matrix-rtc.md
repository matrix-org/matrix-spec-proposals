# MSC4143: MatrixRTC

## Overview

This MSC defines MatrixRTC: how to set up real-time communication sessions over Matrix.
This is the base layer to build real-time systems on top of Matrix.

MatrixRTC specifies how a real-time session is described in a room and how Matrix users can connect
to a session.

The MatrixRTC specification is separated into different modules:

* **The MatrixRTC State** — defines the state of a real-time session and serves as the source of
  truth for:  
  * Which participants are part of a session  
  * Which RTC technology each participant is connected through  
  * Which kind and how many sessions can take place in this room.  
  * Per-device metadata used by other participants to decide whether streams from that source are of
    interest and should be subscribed to.  
* **Discovery of RTC Transports**  
  * The actual transport for real-time data provided by the Matrix deployment (e.g. Selective
    Forwarding Units (SFUs) or assisted by STUN/TURN)  
  * Supports real-time communication exchange, with or without backend infrastructure  
  * Works across topologies such as SFU, P2P, or MCU  
* **The E2EE key Sharing for RTC Data**  
  * Each participant requires a secret in order to publish encrypted real-time data  
  * Every participant must hold a valid key for every other participant at all times during the
    session to decrypt their media  
  * Sessions may use multiple keys or a single shared key across all participants; keys may rotate
    during the session  
  * This MSC also specifies how E2EE keys are distributed

This MSC focuses on the three aspects above, the other modules are defined by accompanying MSCs:

* **MatrixRTC Transports**  
  * Supports multiple transport implementations  
  * Defines how to connect to peers or servers, update connections, and subscribe to streams  
  * A LiveKit-based transport is the current standard proposal
    ([MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195): MatrixRTC Transport using
    LiveKit backend)  
  * Another planned transport is a full-mesh WebRTC implementation based on
    [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401)  
* **MatrixRTC Applications**  
  * Each application type can have its own specification  
  * Example: voice and video conferencing via an application of type `m.call`
    * Defining finer-grained signalling UX, e.g., ringing, declining, stopping ringing  
  * Specifies the full RTC experience, including:  
    * How to interpret member event metadata  
    * What streams to connect to  
    * What data to send over RTC channels and in which format  
    * Which MatrixRTC transports are supported

## Proposal

MatrixRTC provides a framework for building real-time communication on top of Matrix. At its core,
it introduces the concept of **applications**, which define the semantics of a real-time experience,
and **slots**, which act as containers where those experiences take place within a room.
Participants join as **members** within slots, and their overlap defines a **session**.

This proposal defines how MatrixRTC slots are opened and closed, how MatrixRTC members join and
leave, and how these interactions together form the lifecycle of a MatrixRTC session.

The proposal also specifies how:

* **Applications** describe the type of RTC activity (e.g. a call, a shared document, or a real-time
  game) and may define additional metadata and constraints.  
* **Slots** are represented in room state (`m.rtc.slot` identified by a unique `slot_id`) and govern
  what kind of application may run, along with permissions and configuration.  
* **Membership** (`m.rtc.member` [MSC4354 Sticky
  Events](https://github.com/matrix-org/matrix-spec-proposals/pull/4354)) provides a precise record
  of who is actively participating, and under which transports and devices.  
* **Sessions** emerge from the overlap of active members within an open slot, with clear start and
  end conditions.  
* **Transports** define how participants exchange media, supporting multiple backends such as SFUs,
  MCUs, or peer-to-peer.  
* **End-to-end encryption** ensures secure media exchange, including mechanisms for key sharing and
  rotation.

This design deliberately separates **slot management** (opening/closing slots, requiring higher
power levels) from **slot participation** (joining as a member, requiring lower power levels). This
separation gives applications a robust surface for conflict resolution, clear ownership of events,
and flexibility across use cases such as always-on spaces, scheduled meetings, or ephemeral
conversations.

The following sections specify these components in detail.

### MatrixRTC Application Types

An **application type** defines the semantics of a MatrixRTC session, such as a real-time game, a
voice/video call, or a shared document. Each application type has its own specification describing:

* How different RTC streams are interpreted.  
* Which MatrixRTC transport types are supported or required.

For example, a [Third Room](https://thirdroom.io) like experience could include information about
the virtual scene, e.g., a place, available objects or weather conditions.

This modular design makes MatrixRTC flexible. For example, a Jitsi-based conference could be
supported by defining a new application type and a corresponding RTC transport. While such a session
would not be compatible with Matrix clients that do not implement the Jitsi transport, those clients
would still be able to detect the presence of an unsupported application and transport type, and
handle it with a sensible user interface.

The minimum Application definition consists of a simple JSON object

```json5
{
  "application": {
    "type": "m.call", // The # character MUST NOT appear in a valid type string.
    // Optional: application-specific metadata
    "m.call.spatial_audio": true
  }
}
```

The `type` field MUST be a string that does not contain the `#` character. The type field SHOULD
follow the [*Common Namespaced Identifier
Grammar*](https://spec.matrix.org/v1.16/appendices/#common-namespaced-identifier-grammar).

Each application type MUST have its own MSC, which specifies the additional fields and defines how
communication with the corresponding transport is handled. For example:

* `m.call` — voice and video calling, as defined in
  [MSC4196](https://github.com/matrix-org/matrix-spec-proposals/pull/4196).

To facilitate interoperability, ideally each application type should provide a Matrix widget that
can serve as a reference implementation for clients. This allows client developers to support new
application types by embedding or integrating the widget, without having to implement the full
application logic themselves.

### MatrixRTC Slot and Constraining Slots

A **MatrixRTC slot** is the container for MatrixRTC members and temporal overlapping MatrixRTC
members form a MatrixRTC session. Each slot is identified by a unique `slot_id`, tied to a specific
`application` type, and represented by the `m.rtc.slot` state event with the `slot_id` as the state
key. 

> [!NOTE] Conceptually, a slot is like a virtual meeting room: MatrixRTC sessions occur within
> slots, and multiple sessions may occur consecutively without changing the slot’s configuration.

Slots are part of the shared room state and can only be created or modified by authorized users with
sufficient `power_level`. Clients MUST react on and respect latest `m.rtc.slot` definitions as
defined by the Matrix room state at all times. The ability to open and close slots with different
patterns enables a wide variety of use cases, from always-on shared spaces to short lived scheduled
meetings.

Slots are named by the RTC app, but are expected to typically be ordinals (e.g. equivalent to line 1
or line 2 on a telephone). If the app needs to define its slots out of band (e.g. mapping them to
widget IDs) then it can use those IDs as names. However, given a slot is the mechanism around which
sessions converge, it must have a predictable name. Unpredictable IDs such as session IDs should
never be used to name a slot.

#### Opening a MatrixRTC Slot

A slot is opened by sending an `m.rtc.slot` state event with `state_key = slot_id`. This event
authorises MatrixRTC members that intend to participate in the slot and follows the schema below:

```json5
// Example: an open slot with application-specific metadata
{
  "application": {
    "type": "m.call",
    // optional: app specific slot metadata
    "m.call.id": UUID,           // Note your application must handle rollback due to state resolution
    "m.call.voice_only": true
  }
}

state_key: "m.call#ROOM"         // slot_id
```

**Field description:**

* **state key**: The state key of the `m.rtc.slot` state event, referred to as the `slot_id`, serves
  as the slot name.  
* `application` An application JSON object, which **MUST** specify the application type and MAY
  include additional fields which **constrain** the application (e.g., restricting a call to be
  voice-only). **Note** those additional fields can be used in combination with MatrixRTC member
  ones subject to the application specific MSC.

The `slot_id` of an open slot acts like a virtual address where participants are allowed to meet.
The grammar for the `slot_id` is a well formed state key confined such that members of different
MatrixRTC applications never occupy the same slot according to: 

```json5
{application.type}#{application_slot_id}
```

Where

* `application.type` is the `type` field in the application JSON object  
* The `#` character MUST NOT be used in either `application.type` or `application_slot_id`  
* `application_slot_id` is the application-specific slot ID. Each application MSC defines its own
  schema (e.g., `ROOM`, `1`, `2`) to allow multiple parallel slots of the same type according to the
  application requirements.

This grammar MUST never be used to parse `slot_ids`; it exists only to namespace the `state_key`.

#### Closing a MatrixRTC Slot

To close a slot, the corresponding `m.rtc.slot` state event is updated with empty content which
removes all remaining MatrixRTC members, for example:

```json5
// Empty content represents a closed slot
{}

state_key: "m.call#ROOM" // slot_id
```

#### Examples of MatrixRTC Slot Usage

In the following example three different slot use-cases are depicted  

```
m.rtc.slot[id_1] {content_1}            ...████████████████████████████████████████████...
m.rtc.slot[id_2] {content_2}                         ███████████████████

m.rtc.slot[id_state_res] {content_ABC}         ████XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
m.rtc.slot[id_state_res] {content_XYZ}             █████████████████████████████
                                                   |
                                                   |
                                                   Rollback due to Matrix state resolution


Time                                   ────────────────────────────────────────────────────►
```

* `id_1` comprises a long-lived slot suited for a Discord-style experience or a shared whiteboard
  where people can hop on and hop off as desired.  
* `id_2` suited for a scheduled conference meeting, where the state event might be managed using
  cancellable delayed events (MSC4140) or a bot.  
* `id_state_res` This `m.rtc.slot` state event is subject to Matrix state resolution. Hence, it is
  divided potentially into two intervals. If a rollback occurs during an active MatrixRTC session,
  application logic MUST handle conflicts (e.g., a rolled-back UUID).

#### Recommended User Experience

The lifecycle of a slot follows four distinct states:

```
Closed
Open
 ├─ Active   --- at least one m.rtc.member is connected
 └─ Inactive --- no member is connected
```

Slots may transition between these states as a slot is opened or closed, or as users connect or disconnect.

While **participation** in a MatrixRTC session is possible if a **slot is open**, **management** of
slots depends on the user’s **power level**. Clients MUST respect these distinctions in the user
experience.

For **open** slots in a room, clients SHOULD clearly represent the current slot’s activity state:

* **Active:** clients SHOULD indicate which slots are currently active in a room (e.g., by showing
  participant count, showing an icon, list entry, or join button).   
* **Inactive:** clients SHOULD indicate that the slot is available and provide a way for a user to
  join as the first member (e.g., via a “Call” button or placeholder icon).

**Slot management** UX SHOULD only exposed to users who have sufficient power level to manage slots:

* **Closed slot:** The UX SHOULD provide controls to manage the slot (e.g., opening or modifying the
  slot)  
* **Open slot:** The UX SHOULD provide controls to perform management (e.g., closing or modifying
  the slot)

Multiple active slots may exist in the same room if the application type supports them.

Clients MAY present an option to room administrators to enable specific applications in the room by
adding a slot and a type to room state.  Future MSCs may change the defaults for new rooms to enable
RTC applications by default.

### MatrixRTC Membership

A MatrixRTC membership is represented by a sticky `m.rtc.member` event
([MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354) Sticky Events). These
events describe a participant’s presence in an MatrixRTC slot and provide sufficient metadata for
other room members to detect and join the same slot. 

The membership events are implemented as a key-value store according to the addendum section of
[MSC4354 Sticky Events](https://github.com/matrix-org/matrix-spec-proposals/pull/4354) giving the
same semantics as Matrix room state. If the room is encrypted `m.rtc.member` events are also
encrypted and vice versa.

An `m.rtc.member` sticky event can be either **Connected** or **Disconnected**

* **Connected**, if  
  * **Slot open**: the `sticky_key` of the event needs to match the `member.id` AND the `slot_id`
    matches the state\_key of the slot event.  
  * **Content:** MUST match the JSON content schema for connecting to a slot (see below).  
  * The sender is still a member of the room (not kicked / left)  
  * **Event is sticky**: The sticky event needs not to be expired as described in [MSC4354 Sticky
    Events](https://github.com/matrix-org/matrix-spec-proposals/pull/4354)  
* **Disconnected**, if  
  * **Not Connected:** any of the required conditions to be connected are not met.  
  * **Content:** SHOULD match the JSON content schema for disconnecting from a slot (see below). If
    it does not match, clients MUST handle the lack of information gracefully.

#### Connecting to a MatrixRTC Slot

A valid `m.rtc.member` event as a prerequisite for connecting to a slot has the following schema:

```json5
// event type: "m.rtc.member"
{
  "slot_id": "m.call#ROOM",
  "application": {
    "type": "m.call",
    // further fields for the application (optional)
    "m.call.id": UUID
  },
  "member": {
    "id": "xyzABCDEF0123"                     // UUID random/anonymise/unique (external) service identifier
    "claimed_device_id": "DEVICEID"
    "claimed_user_id": "@user:matrix.domain"
  },
  "m.relates_to":{                            // an updated m.rtc.member event MUST reference the first m.rtc.member
    rel_type: "m.reference",                  // event you sent for this call. You should omit if this is the first event.
    event_id: "$join_event_id"
  },
  "rtc_transports": [
    {...TRANSPORT_1},
    {...TRANSPORT_2}
  ],
  "sticky_key": "xyzABCDEF0123"               // same as member.id 
  "versions": [
    "v0",
    "example.mscXXXX.asymmetric_encryption"
  ],
}
```

**Field explanations:**

* `slot_id` — The slot this member belongs to.  
* `application` — Is a JSON object that identifies the MatrixRTC application type; Besides the
  mandatory `type` field which needs to match the MatrixRTC slot identified by `slot_id` it **may**
  include application-specific metadata (see MatrixRTC Application Types). For example, a [Third
  Room](https://thirdroom.io) style experience could include approximate position data on a map,
  allowing clients to avoid connecting to participants outside their area of interest.  
  **Note** application-specific metadata as part of the MatrixRTC slot `application` object have
  precedence over the MatrixRTC member ones.
* `m.relates_to` —  The `m.relates_to` field optionally references the initial connect event,
  distinguishing connect events from updates. Clients SHOULD include this field when sending updates
  to an existing `m.rtc.member` event to ensure continuity in membership lifecycle tracking, enable
  accurate historical reconstruction, and allow deriving the participant’s start time using the
  `origin_server_ts` of the referenced event.  
* `member` — Uniquely identifies this participation instance; includes:  
  * `id` — UUID to distinguish multiple participations, even for the same user and same device. This
    ID can also serve as a canonical identifier for certain MatrixRTC transports, helping to prevent
    metadata leakage if used as additional entropy, e.g., `SHA-256(user_id|device_id|member.id)`. 
    The ID MUST be unique for each connect event.
  * `claimed_device_id` — Matrix device identifier.  
  * `claimed_user_id` — Matrix user ID.  
* `rtc_transports` — List of objects describing how to access this participant’s media streams. See
  [MatrixRTC Transport](#matrixrtc-transport) for the correct object format.  
* `sticky_key` — A unique key used to track this membership across updates. The key persists for the
  lifetime of the MatrixRTC session and is a copy of the `member.id` field[^1]. 
* `versions` — Protocol versions and capabilities supported by the client.

For the example above, user `@user:matrix.domain` with `member.id = xyzABCDEF0123` is part of the
slot `m.call#ROOM`, using an application of type `m.call`, and connected over `TRANSPORT_1`. This
information is sufficient for other room members to detect the running slot and join the session.

> [!NOTE]
> to stay connected: The client MUST maintain participation by sending a new sticky event, before an
`m.rtc.member` sticky event expires (i.e., `sticky.duration_ms <= 0`). **It is strongly
recommended** that the update of the `m.rtc.member` sticky event is scheduled sufficiently ahead of
the event timing out (e.g., 5 minutes) to minimize potential connection state “flipping effects”.

#### Disconnect from a MatrixRTC Slot

A valid `m.rtc.member` event as a prerequisite for disconnecting from a slot has the following schema:

```json5
// event type: "m.rtc.member"
{
  "slot_id": "m.call#ROOM",              // MUST
  "m.relates_to":{                       // SHOULD
      rel_type: "m.reference",
      event_id: "$join_event_id"
  },
  "disconnect_reason": {                 // SHOULD
    "class": "server_error",
    "reason": "ice_failed",
    "description": "Failed to establish peer-to-peer connection via ICE",
  }
  "sticky_key": "xyzABCDEF0123"
}
```

> [!NOTE]
> Any other content for the same `sticky_key` that is not a valid connect event is also treated as a
> disconnect event. However, it is lacking important metadata useful for UX.

**Field explanations:**

- `slot_id`: The slot this member belongs to.  
- `m.relates_to`: Clients SHOULD include the `m.relates_to` field referencing the original
  `m.rtc.member` join event when disconnecting. This facilitates accurate session history and
  retrospective computations by fetching the relation to determine the participant’s original join
  time or associated metadata.  
- `sticky_key:` The sticky key from the disconnecting MatrixRTC member.  
- `disconnect_reason`: The `disconnect_reason` object is **optional** and provides additional
  context when a participant disconnects from a call. It is only meaningful if the user has
  **previously attempted to connect** (i.e., has sent at least one valid `m.rtc.member` event for
  the slot) This ensures that the disconnection reason refers to a real connection lifecycle rather
  than a pre-join cancellation. 

`disconnect_reason` **Field explanations:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| `class` | string | ✅ | High-level category of the disconnection or error. |
| `reason` | string | ✅ | Machine-readable identifier of the specific cause. |
| `description` | string | ⚪ | Optional human-readable explanation providing additional context. |

**Class categories and examples:**

| Class | Example Reason | Description / When Used |
| ----- | ----- | ----- |
| user\_action | `hangup` | Participant intentionally ended the call after joining. |
|  | `switch_device` | User moved the session to another device mid-call. |
| client\_error | `media_error` | Failed to capture or transmit audio/video after joining. |
|  | `transport_failure` | Local ICE/DTLS setup failed despite a successful `m.rtc.member` event. |
|  | `encryption_error` | Failed to set up E2EE for the media channel after connecting. |
| server\_error | `ice_failed` | ICE negotiation could not complete due to network/server issues. |
|  | `dtls_failed` | DTLS handshake failed. |
|  | `network_error` | Temporary network outage caused the connection to drop. |
| redirection | `call_transferred` | Call was redirected to another slot, device, or user. |
|  | `moved_temporarily` | Session temporarily moved (e.g., server migration). |
| permanent\_failure | `codec_mismatch` | Participant cannot decode/encode the call media. |
|  | `unsupported_features` | Session requested unsupported capabilities. |

**Note: (Pre-join)** In situations where a client never successfully connects to a call (for
example, if the user is busy or declines a MatrixRTC session), a dedicated **sticky event** is
required to convey the participant’s status. 

#### Lifecycle of a MatrixRTC Membership

The MatrixRTC membership is a collection of linked `m.rtc.member` events. With the definition of a
**Connected** and a **Disconnected** MatrixRTC membership from above:

* The **connect transition** occurs when the `m.rtc.member` collection becomes Connected. Due to the
  definition of Connected this happens at  `max(start_slot_ts, start_content_ts)` where:  
  * `start_content_ts:` is the time the connect `m.rtc.member` event is sent.  
  * `start_slot_ts:` is the time the slot is opened.  
* The **disconnect transition** occurs when the `m.rtc.member` collection becomes Disconnected. Due
  to the definition of Disconnected this happens at  `min(end_slot_ts, end_content_ts,
  end_sticky_ts).` where:  
  * `end_content_ts:` is the time the disconnect `m.rtc.member` event is sent.  
  * `end_slot_ts:` is the time the slot is closed.  
  * `end_sticky_ts` is the time the stickiness of the connected event expires.

```
       (Connect)              (Update)                (Disconnect)
       
     m.rtc.member ───────► m.rtc.member ──── ... ───► m.rtc.member
           ^                     |                          |
           ├─────────────────────┘ m.relation               |
           |                                                |
           └────────────────────────────────────────────────┘ m.relation
            References original join event


     [---------------- Connected ------- ... --------][--- Disconnected ...
Time ───────────────────────────────────────────────────────────────────────►
```

> [!NOTE]
> Updates are optional. They are only required if the participation lasts longer than the sticky
event’s timeout (`sticky.duration_ms`) or the member changes their `m.rtc.member` event (for example
to change transport). In such cases, participants MUST refresh their membership by sending a new
sticky event update.

#### Reliability for Real-Time Applications

For real-time applications, it is important to maintain an accurate view of which participants are
connected and for how long. In particular:

* **Precise membership tracking** — RTC applications rely on a high-resolution understanding of the
  lifetime of each `m.rtc.member` object. Knowing exactly when a participant joins or leaves is
  critical for computing session state.  
* **Handling (unintentionally) disconnected clients** — A client that loses network connectivity
  must not be treated as continuously connected. Otherwise, the session state may become
  inconsistent or appear to include phantom participants.

Clients MUST handle network disconnects or crashes by sending empty leave events once reconnection
is possible, or by using cancellable delayed leave events
([MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140)).

Clients SHOULD use cancellable delayed events to implement a “deadman switch” for MatrixRTC
membership by sending a leave event ahead of the join event as a delayed event with a reasonable
delay (e.g., 15–30 seconds). The client then periodically resets the delayed event’s timer. If the
timer expires due to a missing reset, the leave event is automatically emitted, marking the
participant as disconnected and ensuring accurate session state even in cases of sudden
disconnection, crashes, or network failures.

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

Counterintuitively, **state resolution is not a problem** — RTC sessions occurred in real life, and
their existence remains valid regardless of how the room state later resolves.

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

#### RTC Transports in `m.rtc.member` Events

Each `m.rtc.member` event contains an `rtc_transports` array, which allows other clients to
determine how to connect to, and exchange real-time data with that participant. This array includes
at least one transport JSON object, each containing at least the following required field:

* `type` (string) — Identifies the RTC transport.  
* Additional fields may be present depending on the RTC transport `type`.

The `versions` field of the `m.rtc.member` event SHOULD be used to determine which transports are
supported by all participants. Clients SHOULD publish their RTC data using at least one transport
supported by their application, constrained to the set of transports supported by all participants.
Clients MAY additionally publish their media via multiple transports.

To render a MatrixRTC session, a client MUST be prepared to connect to as many transports as there
are members currently connected. For bandwidth efficiency, clients are recommended to subscribe to
only one transport per member.

The exact procedures for subscribing to and publishing real-time data are defined in the dedicated
MSCs for each transport type.

#### Discovery of RTC Transports

MatrixRTC requires a mechanism for clients to discover which RTC transports — such as an SFU or TURN
server — are available in their Matrix deployment. To support this, homeservers expose an endpoint
that returns a list of JSON objects. Each transport-description object represents an RTC transport
as defined by the corresponding MSC.

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

Concrete example for a `livekit_multi_sfu` transport:

```json5
{
  "rtc_transports": [
    {
      "type":"livekit_multi_sfu",
      "livekit_service_url":"https://matrix-rtc.example.com/livekit/jwt"
    }
  ]
}
```

**Fields:**

* `rtc_transports` — array of transport-description representing the available RTC transports
  offered by the homeserver.  
* Each object in the array MUST conform to the JSON schema defined for its `type` (e.g.
  `livekit_multi_sfu` in MSC4195).

Clients SHOULD use this list to determine which RTC transports to connect to and may advertise their
selected transports according to the respective MSC in the `rtc_transports` field of their
`m.rtc.member` events.

### End-to-end Encryption of RTC Data

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
`member`.`device_id` field of the recipient’s `m.rtc.member` event. The event follows the following
schema:

```json5
// event type: "m.rtc.encryption_key"
{
    "room_id": "!roomid:matrix.domain",
    "member.id": "xyzABCDEF0123"
    "media_key": {
            "index": 10,
            "key": "base64encodedkey"
    },
}
```

**Field explanations:**

* `slot_id` required string: `slot_id` of the slot this key is related to.   
* `member.id` required string: The `member.id` from the target `m.rtc.member` event. Note, because
  `member.id` is globally unique per member instance, it is sufficient to disambiguate multiple key
  events for the same device, even if they use the same `media_key.index` value.  
* `media_key` The media key to use to decrypt  the participant media:  
  * `key` required string: The base64 encoded key material.  
  * `index` required int: The index of the key to distinguish it from other keys. This must be
    between 0 and 255 inclusive. In some implementations of MatrixRTC this may correspond to the
    `keyID` field of the WebRTC [SFrame](https://www.w3.org/TR/webrtc-encoded-transform/#sframe)
    header.  
  * `format` the key export format, `0` for the raw bytes base64 encoded.  
* consecutive sessions within the same slot.  
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

Clients SHOULD rotate their keys to ensure **confidentiality** whenever a participant joins or
leaves the slot. The **key rotation** process is as follows:

* The sending application generates the new key material for the local participant.  
* The sending application sends the new key material to all other participants with a new `index` value.  
* The receiving application stores the new key material for the specified `index`.  
* The sending application continues to use the old/current key to encrypt media.  
* After a short delay `delayBeforeUse,` default: 5 seconds), the sending application switches to the
  new key.  
  * It is possible to overwrite the default delay on a per application basis in case an application
    has specific requirements on security or wants to minimize missed stream data  
  * Also negotiation can be used over data channels to confirm all participants have received the new key.

**Note:** Rotating a key will require to re-send a to-device message to all the participants, and
this is expensive. Clients SHOULD minimize key exchange traffic for rapid joiners/leavers. 

For rapid new joiners: A key rotation grace period (`keyRotationGracePeriod`) is used, if a new
member joins during the grace period, then the same key can be used and shared just to that new
member..

For rapid leavers: The `delayBeforeUse` period is used to coalesce any membership change occurring
in that period and then a single key rotation is scheduled afterward.

`keyRotationGracePeriod` must be greater than `delayBeforeUse` or it will have no effects (default
10s and 5s)

A future version of key exchange could introduce ratcheting, this would reduce the key traffic for
new joiners (only sends the ratcheted key to the new joiners instead of rotating to all).

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

### Scope and Responsibilities of MatrixRTC Applications

This MSC defines the **foundational protocol for real-time communication (RTC)** in Matrix —
establishing the primitives and data structures needed for RTC functionality. It deliberately **does
not define a complete calling experience**, leaving that to specific MatrixRTC applications that
build on top of this foundation. Each such application can define its own UX expectations,
signalling behaviour, and feature set.

Implementations, especially chat clients, are expected to support one or more of these applications
as they are defined by future MSCs.  
The first of these is expected to be the 
**`m.call` application ([MSC4196](https://github.com/matrix-org/matrix-spec-proposals/pull/4196))**. 
Clients SHOULD treat this application as a special case and present a familiar call experience that
abstracts away the underlying slot and membership model.

Common UX patterns include:

* A “Call” button in the room header.  
* Ongoing call information displayed in the room header.  
* Moderation-style wording for slot management, e.g. *“Allow users to start a call.”*  
* Permission-related messaging, e.g. *“You are not allowed to start a call in this room.”*

This MSC’s goal is to define the **core RTC protocol**, not to specify every user-facing behaviour.
It delegates **user experience, call control, and signalling flows** to individual RTC applications
layered on top. For example, pre-call signalling (ringing, declining, etc.) is handled outside the
RTC session itself, using membership and slot application data and other events (TODO: link related
MSCs).

Importantly, **MatrixRTC can be used by custom or experimental RTC applications** without those
applications being merged into the Matrix specification. The only difference is that a *merged* RTC
application may impose additional interoperability requirements on clients, whereas *non-merged*
applications can still operate using the same MatrixRTC primitives.

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

### MatrixRTC Membership Heartbeat Keep Alive

If an RTC Transport is involved like a SFU then per definition the SFU has a very good understanding
of the connectivity of the individual participants. In that case it would be nice to be able to
delegate the ownership of the delayed leave event to that infrastructure component. However,
practical implementation has so far proven that the current implementation of delayed events are
also sufficient in adverse network conditions. So for now it's good enough and considered as an
optimisation for a future MSC.

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
- When handling client disconnects, 
- [MSC4140 delayed events](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) **cannot
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

Whilst reducing traffic by only needing to send one event per participant to the homeserver, this
approach does not allow for perfect forward secrecy as the keys are persisted in the room history.

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

## Security considerations

### Discoverability of RTC Infrastructure

RTC infrastructure details are disseminated to all participants through `m.rtc.member` events. This
transparency means that anyone part of a MatrixRTC session can view and understand the
infrastructure, which could potentially lead to unauthorized resource use. However, each
infrastructure type defines its own authentication mechanisms, as detailed in its specific MSC.
These mechanisms may involve a service interacting with the homeserver to determine whether a user
is authorized to utilize the infrastructure.

### Forward secrecy for end-to-end encryption of media streams

The considerations to ensure forward secrecy are described in the [Key
Distribution](#key-distribution) section above.

### End-to-end media encryption key rotation lag

The proposed key rotation semantics does mean that a participant could continue to decrypt media
that was sent in the three seconds after leaving the session.

## Unstable prefix

Use `org.matrix.msc4143.rtc.member` as the sticky event type in place of `m.rtc.member`.
Use `org.matrix.msc4143.rtc.slot` as the state event type in place of `m.rtc.slot`.

For MatrixRTC Transport discovery via  `GET` endpoint use
`/_matrix/client/unstable/org.matrix.msc4143/rtc/transports` instead of
`/_matrix/client/v1/rtc/transports`

Use `org.matrix.msc4143.rtc.encryption_key` in place of the `m.rtc.encryption_key` room event and
to-device event types.

## Dependencies

This proposal depends on [MSC4354 Sticky
Events](https://github.com/matrix-org/matrix-spec-proposals/pull/4354) to provide room state similar
semantics without the drawback of contributing to room state bloating. 

This proposal also depends on [MSC4140: Cancellable delayed
events](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) to provide a mechanism for
clients to ensure that they can update the room state even if they lose connection.

[^1]: Because `member.id` is generally unique, it serves as a reliable candidate for `sticky_key`,
  preventing undesired collisions. Clients can use it to distinguish new member participation from
  updates to existing RTC members.
