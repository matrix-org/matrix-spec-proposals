# MSC4196: Voice and video calling application for MatrixRTC

[MSC4143] introduces MatrixRTC as an extensible framework for real-time communication in Matrix.
MatrixRTC uses so called transports to transfer the RTC data between RTC members. Transports are
then used in what MatrixRTC calls applications to build user experiences for concrete use cases.

This proposal introduces a MatrixRTC application for voice and video calling that is able to power
a variety of calling use cases including but not limited to classical 1-on-1 and group calling
as well as Discord-style [Voice Channels]. The application is compatible with the [LiveKit] transport
introduced in [MSC4195].

Note that call ringing and notifications are not in scope for this proposal. These are covered
in [MSC4075] and [MSC4310].

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[Voice Channels]: https://support.discord.com/hc/en-us/articles/19583625604887-Voice-Channels-FAQs
[LiveKit]: https://github.com/livekit/livekit
[MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195
[MSC4075]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075
[MSC4310]: https://github.com/matrix-org/matrix-spec-proposals/pull/4310

## Proposal

A new MatrixRTC application type `m.call` is introduced. For now, only a single instance of `m.call`
per room is supported. This is sufficient for the majority of use cases and avoids the risk of two
competing slots being opened for the same call when room administrators race.

### Slot events

The `m.call` application instance MUST use an application-specific slot ID of `ROOM`. The full
slot ID as per [MSC4143], thus, becomes:

```
slot_id = {application_type}#{application_slot_id} = m.call#ROOM (= state_key)
``` 

No further parameters are required in the slot-level `application` object. Here is an example for
an open `m.rtc.slot` event for the `m.call` application:

```json5
{
  "type": "m.rtc.slot",
  "state_key": "m.call#ROOM", // = slot_id
  "content": {
    "status": "open",
    "application": {
      "type": "m.call",
    },
    "encryption": {
      "type": "m.per_member",
    }
  },
  ...
}
```

### Membership events

The schema for the `application` content block in `m.rtc.member` events that are joined to `m.call`
slots, looks as follows:

- `type` (string, required): MUST be `m.call`.
- `intent` (string): One of `audio`, `video`. Optionally discloses whether the member intends to
  join the session with audio only or with audio and video. Clients SHOULD set this field when joining
  and update it as they en- or disable their video stream. This gives other members a hint as to whether
  the session presents an audio or video call. 

Below is an example of an `m.rtc.member` event for joining an `m.call` slot.

```json5
{
  "type": "m.rtc.member",
  "content": {
    "slot_id": "m.call#ROOM", // = m.rtc.slot state_key
    "member": {
      "id": "xyzABCDEF0123",
      "membership": "join"
    },
    "application": {
      "type": "m.call",
      "intent": "video"
    },
    "transports": {
      ...
    },
    "sticky_key": "xyzABCDEF0123", // = member.id
  },
  ...
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
[MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354).