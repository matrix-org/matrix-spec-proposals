# MSC4196: MatrixRTC voice and video calling application `m.call`

## Proposal

We define a **MatrixRTC application** of type `m.call` for real-time calling, designed to support
the following use cases:

* **1:1 calls in direct messages (DMs)** – Private, peer-to-peer conversations.  
* **Huddles** – Adding a call to an existing room for spontaneous group discussions.  
* **Persistent “social” rooms** – Discord-style voice or video spaces that are fixed in type but act
  as a permanent hangout, where users can drop in and out freely, similar to a pub or watercooler.

### MatrixRTC Slots for voice and video calling

For voice and video calling, MatrixRTC defines **a room-level slot model** to represent calls that
are scoped to a Matrix room and shared among its participants:

* **`m.call#ROOM` — Room-level call slot**  
  Represents a call instance associated with the entire room. This slot is **managed by a user with
  sufficient power level** and is intended for calls where **any room member is welcome to join**.
  Ownership of the call is **shared** — it does not depend on who initiated it. This slot type is
  also suitable for **1:1 direct message (DM) calls**, including use cases resembling traditional
  **telephone-style calling semantics**.  

### MatrixRTC Member JSON Object for Application `m.call`

A valid `m.rtc.member` state event with **application type** `m.call` includes the standard fields
defined in [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143), **plus
additional fields specific to `m.call`**:

```
{
  "application": {
    "type": "m.call",
    // additional fields for m.call:
    "m.call.id": UUID                                 // optional
    "m.call.intent": "voice" | "video" | "any-value"  // optional
  },
}
```

**Field Description**

| Field | Type | Required | Description |
| :---- | :---- | ----- | :---- |
| `type` | string | ✅ | Must be `"m.call"`. Identifies the application type. |
| `m.call.id` | string | ⚪ | Optional call ID of the session. Serves as a unique identifier for the call instance. |
| `m.call.intent` | string | ⚪ | Optional hint expressing the intended use-case of the session, e.g., `"voice"`, `"video"`, or `"spatial-audio"`. This field is **informational only** and non-authoritative, reflecting the participant's perception of the session. |

Participants MAY include a `m.call.intent` field to express the intended use-case of their `m.call`
session (e.g. `"voice"`, `"video"`, `"spatial-audio"`). Because of Matrix decentralisation, this
field is purely informational and non-authoritative, serving only as a hint about how the
participant perceives the session.

The following is an example of a well-formed `m.rtc.member` event for a participant joining a
room-level call (`m.call#ROOM`) using the `m.call` application type:

```
// event type: "m.rtc.member"
{
  "slot_id": "m.call#ROOM",
  "member": {
    "id": "xyzABCDEF0123"                             // UUID, unique participation instance
    "claimed_device_id": "DEVICEID",
    "claimed_user_id": "@user:matrix.domain"
  },
  "sticky_key": "xyzABCDEF0123"                       // same as member.id 
  "application": {
    "type": "m.call",
    // additional fields for m.call:
    "m.call.id": UUID
    "scope": "m.room"
    "m.call.intent": "voice" | "video" | "any-value"  // optional
  },
  "m.relates_to":{                                    // Reference to original join event; omit if first event
    rel_type: "m.reference",
    event_id: "$connect_event_id"
  },
  "rtc_transports": [
    { /* TRANSPORT_1 details */ }
  ],
  "versions": [
    "v0"
  ],
}
```

### Ending a Call and Post-Connect Error Handling

Participation in a call is ended by disconnecting the MatrixRTC slot, as defined in
[MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143). The
**`disconnect_reason`** field is used to provide further details about the disconnection and can
also be used for structured error handling.

A valid `m.rtc.member` event, as a prerequisite for disconnecting from a slot, has the following
schema:

```
// event type: "m.rtc.member"
{
  "slot_id": "m.call.ROOM",
  "sticky_key": "xyzABCDEF0123",
  "m.relates_to":{                  // SHOULD
    rel_type: "m.reference",
    event_id: "$connect_event_id"
  },
  // Optional
  "disconnect_reason": { 
    "class": "server_error",
    "reason": "ice_failed",
    "description": "Failed to establish peer-to-peer connection via ICE",
  }
}
```

**Field explanations:**

* `slot_id` — The slot this member belongs to.  
* `m.relates_to` —  The `m.relates_to` field optionally references the initial connect event  
* `sticky_key` — Same as above  
* `disconnect_reason` as defined below

```
{
  "* `disconnect_reason` as defined below
": {
    "class": "server_error",
    "reason": "ice_failed",
    "description": "Failed to establish peer-to-peer connection via ICE",
  }
}
```

`disconnect_reason` **field explanations:**

| Class | Example Reason | Description / When Used |
| ----- | ----- | ----- |
| `user_action` | `hangup` | Participant intentionally ended the call after joining. |
|  | `switch_device` | User moved the session to another device mid-call. |
| `client_error` | `media_error` | Failed to capture or transmit audio/video after joining. |
|  | `transport_failure` | Local ICE/DTLS setup failed despite a successful `m.rtc.member` event. |
|  | `encryption_error` | Failed to set up E2EE for the media channel after connecting. |
| `server_error` | `ice_failed` | ICE negotiation could not complete due to network/server issues. |
|  | `dtls_failed` | DTLS handshake failed. |
|  | `network_error` | Temporary network outage caused the connection to drop. |
| `redirection` | `call_transferred` | Call was redirected to another slot, device, or user. |
|  | `moved_temporarily` | Session temporarily moved (e.g., server migration). |
| `permanent_failure` | `codec_mismatch` | Participant cannot decode/encode the call media. |
|  | `unsupported_features` | Session requested unsupported capabilities. |

### Call Ringing Using `m.rtc.notification` room event

A valid `m.rtc.notification` event for a MatrixRTC session with application `m.call` MAY have the
following fields in addition to the fields defined in
[MSC4075](https://github.com/matrix-org/matrix-spec-proposals/pull/4075):
- `m.call.intent`

```
// event type: "m.rtc.notification"
{
  "type":"m.rtc.notification",  // org.matrix.msc4075.rtc.notification
  "content": {
    "sender_ts": 1752583130365,
    "lifetime": 30000,
    "m.mentions": {"user_ids": [], "room": true | false},
    "m.relates_to": {"rel_type":"m.reference", "event_id":"$rtc_member_event_id"},
    "notification_type": "ring | notification",
    // additional fields for m.call:
    "m.call.intent": "voice" | "video" | "any-value"  // optional, 
  }
}
```

### Handling of `m.call.intent`

Clients SHOULD infer a “voice” `m.call.intent` as a voice call, and “video” as a voice and video
call. 

Clients SHOULD NOT submit a video track if the user has requested a “voice” call initially, although
this is a soft limitation and users may choose to upgrade to include a video track later in the
call.

If the intent is not understood, the default value of “video” should be assumed (both voice and
video tracks may be expected).

### Defaults

[The createRoom preset
option](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3createroom)
`trusted_private_chat` should enable a default room slot `m.call#ROOM` for the application `m.call`.

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix

The `m.call` application type is already within unstable prefixed entries (i.e.
`org.matrix.msc4143.rtc.member`) and as such doesn't need its own unstable prefix.

## Dependencies

This MSC builds on [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) and
[MSC4075](https://github.com/matrix-org/matrix-spec-proposals/pull/4075).