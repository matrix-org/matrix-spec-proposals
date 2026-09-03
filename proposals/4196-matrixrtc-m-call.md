# MSC4196: Voice and video calling application for MatrixRTC

[MSC4143] introduces MatrixRTC as an extensible framework for real-time communication in Matrix.
MatrixRTC uses so called transports to transfer the RTC data between RTC members. Transports are
then used in what MatrixRTC calls applications to build user experiences for concrete use cases.

This proposal introduces a MatrixRTC application for voice and video calling that is able to power
a variety of calling use cases including but not limited to classical 1-on-1 and group calling
as well as Discord-style [Voice Channels] (which, previously, were attempted to be introduced
in [MSC3417]). The application is compatible with the [LiveKit] transport introduced in [MSC4195].

Note that call ringing and notifications are not in scope for this proposal. These are covered
in [MSC4075] and [MSC4310].

[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[Voice Channels]: https://support.discord.com/hc/en-us/articles/19583625604887-Voice-Channels-FAQs
[LiveKit]: https://github.com/livekit/livekit
[MSC3417]: https://github.com/matrix-org/matrix-spec-proposals/pull/3417
[MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195
[MSC4075]: https://github.com/matrix-org/matrix-spec-proposals/pull/4075
[MSC4310]: https://github.com/matrix-org/matrix-spec-proposals/pull/4310

## Proposal

A new MatrixRTC application type `m.call` is introduced. For now, only a single instance of `m.call`
per room is supported. This is sufficient for the majority of use cases and avoids the risk of two
competing slots being opened for the same call when room administrators race.

### Slot event

The `m.call` application instance MUST use an application-specific slot ID of `room`. The full
slot ID as per [MSC4143], thus, becomes:

```
slot_id = {application_type}#{application_slot_id} = m.call#room (= state_key)
``` 

No further parameters are required in the slot-level `application` object. Here is an example for
an open `m.rtc.slot` event for the `m.call` application:

```json5
{
  "type": "m.rtc.slot",
  "state_key": "m.call#room", // = slot_id
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

When clients create rooms with `preset = private_chat` in [`/createRoom`], they SHOULD by default
include an open `m.rtc.slot` event for `m.call` in `initial_state`. Clients MAY let the user
override this default behaviour.

As per [MSC4143], encryption of MatrixRTC sessions is mandatory in encrypted rooms and forbidden
in unencrypted rooms. Therefore, if [`m.room.encryption`] is also present in `initial_state`, the
`encryption` content block on the initial slot event MUST be set to `{ "type": "m.per_member" }`.
Otherwise, the `encryption` property MUST be omitted.

The default [power levels] assigned during room creation prevent room members other than the room
creator from sending state events. Including the slot event at room creation time, ensures that
room members are able to have calls in the room without depending on a room administrator to send
the slot event later.

Including `m.rtc.slot` events in `initial_state` is not required when other `preset` values are
used in [`/createRoom`]. With the `trusted_private_chat` preset, all room members get the same power
level as the room creator. Thus, they can send the `m.rtc.slot` event themselves when needed. In
rooms that use the `public_chat` preset, in turn, enabling calls by default is usually not desired
due to the open-access nature and the potentially large size of such rooms.

[`/createRoom`]: https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3createroom
[`m.room.encryption`]: https://spec.matrix.org/v1.18/client-server-api/#mroomencryption
[power levels]: https://spec.matrix.org/v1.18/client-server-api/#mroompower_levels

### Membership events

The schema for the `application` content block in `m.rtc.member` events that are joined to `m.call`
slots, looks as follows:

- `type` (string, required): MUST be `m.call`.
- `intent` (string): One of `audio`, `video`. Optionally discloses whether the member intends to
  join the call with audio only or with audio and video. Clients SHOULD set this field when joining
  and update it as they en- or disable their video stream. This gives other members a hint as to whether
  the session presents an audio or video call.

Below is an example of an `m.rtc.member` event for joining an `m.call` slot.

```json5
{
  "type": "m.rtc.member",
  "content": {
    "slot_id": "m.call#room", // = m.rtc.slot state_key
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

When a client joins an `m.call` slot where all other members have set their `intent` to `audio`,
the joining client SHOULD not publish a video track by default. It MAY allow the user to overrule
this initial setting both before and after joining though. If any other members have an
`intent` of `video`, the joining client SHOULD assume the session to
represent a video call. This does *not* imply that the client should enter the call with video
enabled, however (see [below]).

When leaving a slot, [MSC4143] allows clients to optionally provide context with regards to the
reason for leaving in the `leave_reason` property of their `m.rtc.member` event. For `m.call`
applications, the generic `leave_reason.code` values provided in [MSC4143] are extended with
the following additional codes:

- `transport_error`: The client failed to negotiate a connection over the chosen transport
  (e.g. due to an ICE/DTLS setup failure).
- `media_error`: The client failed to capture or transmit audio and/or video after joining.
- `codec_mismatch`: The client could not decode/encode the call media.

[below]: #faking-intent

### Usage with the LiveKit transport from [MSC4195]

As of writing, the only known MatrixRTC transport is the `m.livekit` transport from [MSC4195].
Clients can use the mechanisms from [MSC4195] for obtaining WebSocket URLs and access tokens
for the LiveKit SFUs involved in a MatrixRTC session. The URLs and tokens can be used with one
of the [LiveKit SDKs] to [publish] a user's own audio and video (including [screensharing]) and
to [subscribe] to other member's published audio and video. Clients can map LiveKit participants
and their media tracks to `m.rtc.member` events by means of the procedure for deriving LiveKit
participant identities given in [MSC4195].

Note that future transports might lack some or all of the capabilities listed above. Therefore,
the `m.call` application is explicitly only deemed compatible with the `m.livekit` transport for
now. If a future MSC introduces another transport, that MSC will have to evaluate the transport's
fitness for use in `m.call`.

[LiveKit SDKs]: https://docs.livekit.io/transport/sdk-platforms/
[publish]: https://docs.livekit.io/transport/media/publish/
[screensharing]: https://docs.livekit.io/transport/media/screenshare/
[subscribe]: https://docs.livekit.io/transport/media/subscribe/

## Potential issues

### Multiple slots per room

More advanced calling experiences might have a need for more than one slot per room, for instance,
for breakout sessions. This was consciously left out of scope in this proposal. A future MSC
may devise a scheme for letting clients negotiate which slot to use when multiple are present in
a room.

## Alternatives

### Injecting `m.rtc.slot` events on the server

Instead of having clients pass in the initial `m.rtc.slot` event via `initial_state` on
[`/createRoom`] requests, this logic could also be implemented by the server. This would
further complicate the already complex steps the server has to run through during room
creation though.

## Security considerations

### Metadata leakage through intent

Some users might not be comfortable with disclosing whether their camera is on or off via
the `intent` property on `m.rtc.member` events. Given that any room member can join the
session, this information is effectively obtainable by all room members anyway (though the join would at least be a visible choice). In either
case, users can opt not to fill `intent` given that it is an optional property.

### Faking intent

A malicious user could set `intent = video` without actually publishing their video stream
to trick another user into joining the call with their camera on. To mitigate this, clients
SHOULD default to joining with video disabled regardless of the `intent` values of other
members. They MAY allow users to override the default setting though.

## Unstable prefix

No unstable prefix is needed for `m.call` because it is only used inside the `m.rtc.slot`
and `m.rtc.member` events that are themselves guarded by the unstable prefix from [MSC4143].

## Dependencies

This proposal depends on [MSC4143] and [MSC4195].
