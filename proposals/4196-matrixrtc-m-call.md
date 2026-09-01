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

When leaving a slot, [MSC4143] allows clients to optionally provide context with regards to the
reason for leaving in the `leave_reason` property of their `m.rtc.member` event. For `m.call`
applications, the generic `leave_reason.code` values provided in [MSC4143] are extended with
the following additional codes:

- `transport_error`: The client failed to negotiate a connection over the chosen transport
  (e.g. due to an ICE/DTLS setup failure).
- `media_error`: The client failed to capture or transmit audio and/or video after joining.
- `codec_mismatch`: The client could not decode/encode the call media.
- `encryption_error`: The client failed to set up end-to-end encryption for the media channel.


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