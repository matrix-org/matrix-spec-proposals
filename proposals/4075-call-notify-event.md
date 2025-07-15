# MSC4075: MatrixRTC Ringing

It is important that an RTC session initiated on clientA can make targeted clients ring.
This is of interest in 1:1 Rooms/Calls but also in bigger rooms ringing can be desired.

The existing "legacy" [1:1 VoIP calling in Matrix](https://spec.matrix.org/v1.11/client-server-api/#voice-over-ip)
uses room events to negotiate the call.
A client can use the initial steps in the negotiation to also make the phone ring.

With [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)
this signalling is done over state events. Furthermore, [MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)
allows for large group calls (not just 1:1) which makes it very
desirable to have more configurations over the ringing process.

## Proposal

A new event `m.rtc.notification` is proposed which can be sent by a client that
wants to notify others about the existence of a session for a MatrixRTC application.
This event is added to the push rules for clients which
support the application type so they receive push notifications. The push rules for intentional
mentions make sure no unnecessary push notification is sent.

This event contains the following fields by leveraging intentional mentions.

```json5
{
  "content": {
    "sender_ts": 1752583130365,
    "lifetime": 30000,
    "m.mentions": {"user_ids": [], "room": true | false},
    "m.relates_to": {"rel_type":"m.rtc.notification", "eventId":"$rtc_member_event_id"},
    "notification_type": "ring | notification",
  }
}
```

The fields are defined as follows:

- `sender_ts` the local timestamp observed by the sender device. Is used in combination with lifetime to evaluate if
  the notification event is valid. To mitigate clients lying about the `sender_ts` this value has to be checked with `origin_server_ts`.
  The diff between `sender_ts` and `origin_server_ts` should be at most 20s.
  If not the `origin_server_ts` should be used for the lifetime
  computation instead.
- `lifetime` the relative time to the `sender_ts` for which the `ring` is active or to define the window in which the
  `notification` is not ignored. The recommended value is **30 seconds**.
  The receiving client **should** cap the lifetime to an upper bound. (recommended: **2 minutes**).
- `m.mentions` optional:\
  Has the structure as defined for `m.mentions` in the [Client-Server API](https://spec.matrix.org/v1.11/client-server-api/#definition-mmentions).
- `notification_type` required string:\
  The type of notification to send.\
  `ring`: The client should ring.\
  `notification`: The client should show a notification.\
- `m.relates_to`: optional:\
  A relation (with type: `m.rtc.session_parent`) to the session participation event (`m.rtc.member`) of the notifying member.
  If available this can be used to gather session data for this notify event.
  It should always be used if the notify is related to an rtc session. (Eventually this event might be used to send
  RTC session independent ringing notifications with a custom message. A bot controlled tea timer for instance.)
The `session` information for this notify event can be obtained by the relation to the `m.rtc.member` event.

In the following we define **call** as any MatrixRTC session with the
same `"session"` contents.

### Client behaviour on receiving a `m.rtc.notification` event

On retrieval, the client should not render the event in the timeline.
If the notify conditions (listed below) apply,
the client has to inform the user about the **call** with an appropriate user flow.
For `notification_type == "ring"` some kind of sound is required
(except if overwritten by another client specific setting),
for `notification_type == "notification"` a visual indication is enough.
This visual indication should be more than an unread indicator
and similar to a notification banner.
This is not enforced by the spec however and ultimately a client choice.

The client should only inform the user if all of the following conditions apply:

- `m.rtc.notification` content:\
  If the user is *not* listed in the `m.mentions` section as defined in the\
  [Client-Server API](https://spec.matrix.org/v1.11/client-server-api/#definition-mmentions),\
  the event should be ignored. (Push notifications are automatically filtered
  so this only is important for events received via a sync)
- Local notification settings:\
  If the room is set to silent, the client should never play a ring sound.
  In this scenario, a `m.rtc.notification`
  event should at most be used to mark the room as unread or update the rooms
  "has active **call** icon". (the exact behavior is up to the client)
- Currently playing a ring sound (room timeline):\
  If the user already received a ring event for this **call** and is playing
  the ring sound any incoming `m.rtc.notification` for the same **call**
  should be ignored. If the user failed to pick up and a new `m.rtc.notification`
  arrives for the same room the device should ring again.
- Current user is a member of the the **call** (room state):\
  None of the devices should ring if they receive a `m.rtc.notification` if the
  rooms state `m.rtc.member` event of the user contains a membership for
  the **call** in the `m.rtc.notification` event.
  This includes stopping the current ring sound if the room state updates so
  this condition is true.
- If a notify event is received in "real time":\
  Notify events that are older then **`lifetime`** are ignored (using the
  `sender_ts` timestamp).\
  Otherwise a client syncing for the first time would ring for outdated call events.
  In general ringing only makes sense in "real time".
  Any client which is not able to receive the event in the `lifetime` period should
  not ring to prohibit annoying/misleading/irrelevant/outdated rings.

### Client behaviour when sending a `m.rtc.notification` event

Sending a `m.rtc.notification` should happen only if all of these conditions apply:

- If the user deliberately wants to send a new notify event
  (It is possible to send a `m.rtc.notification` for an ongoing call if that
  makes sense. Starting a call ahead of time, planning in a small group,
  ringing another set of users at a specific time so they don't forget to join.
  Ringing one specific user again who missed joining during the first ring.)
- If the user has not yet received a `m.rtc.notification` for the **call** they want to
  participate but the other condition applies. (So the obvious case is, that this
  is the first user in a new call session).
- If possible the user should first send their `m.rtc.member` event first to allow setting up the relation
  for the notify event.
- The sending client can compute the "exact" (or at least "a good approximation" if the local clocks are not configured correctly)
  at which the `m.rtc.notification` ring will end using the `lifeitime` + `start_ts`. This allows the sending client to
  show a local dialing/ringing animation/indicator/sound.
 the receiving
  device)
  - The location to put this information would be the invite event.
    This would be an edge case and only required for the specific usecase
    of being able to ring without a shared DM/Room.
    It should be discussed in an additional MSC and is not part of this proposal.

### Extensible Events

The concept of [extensible events](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
is used to offer a fallback f clients that do not support noticiation events and benefit from a fallback text reperentation.

The body should contain a `m.text` field with the following content:

```json5
// notification
 m.text: [{"body": "Call started by {sender}"}]

// ring event
 m.text: [{"body": "Call started by {sender} 🎶"}]
```

## Alternatives

### Use call member room state events

It would be possible to use the call member room state events to determine a call
start.
The logic would be as following:
*If we receive an event we check if  are already other members
(call.member events) for the call. In case there is not we make the phone ring.*

Pros:

- This would not require any new event.
- The clients can not "forget" to ring the others about the when they
  start a new call. Because they would automatically send an event by joining.
- There would be less traffic. With the proposed solution the first one who joins
  needs to send a `m.rtc.notification` event and a `m.rtc.member` state event.

Cons

- All the ringing conditions run on the receiving user. There is no way for the
  user who start the call to decide if it should ring the other participants.
  (Consider a very large room where I want to start a call only for the interested
  ones who want to discuss a side project. It would be very annoying if the
  initiator could not control how and who is going to be informed about that call.)
- Additionally, it is not as flexible as the proposed separate event.
  Which allows an external instance (a meeting organizer bot) to
  just ring all the users which are invited to a meeting without needing to
  participate in the call with a `m.rtc.member` event of the call.
- Push notifications would need to be sent for EVERY `m.rtc.member` state event
  update. For each joining and leaving user and for each membership update during
  a call (due to a SFU (single forwarding unit) change, changing devices
  (could even happen for screen shares if the screen share is implemented as a
  separate participating device) or matrix RTC business logic of the call.)
  This could result in a lot of push notification with no obvious/simple way to
  filter them.
- It would require bloating the `call.member` event if the `notification_type` or a
  specific list of users to notify want to be specified.
- It would not make it possible to ring without participating.

### Which properties are defined by the sender vs receiver

- The duration of the ring sound could be the receiving clients decision. This MSC tries to find a middle ground by
  allowing the sender to define a lifetime but the receiver and overwrite it in case that it is
  necessary for the expected client UX. This at least provides
  an expected ring duration that can be used for the sender UX.
  Ultimately the sender can never know how the receiving client
  will implement the ring. See [the related discussion](https://github.com/matrix-org/matrix-spec-proposals/pull/4075#discussion_r1597704775)
- The ring sound is a client choice. (It was considered to
  add the ring sound to the notify event but how "ringing" actually should
  look like is intentionally in control of the receiver. So that users can use
  clients that suit them in terms of accessibility and personal taste.)

## Security considerations

This is another timeline event where any room participant can send a push
notification to others. Since this will make clients ring this has a higher
effect on the receiver. Since ringing has to obey the mute settings, it is
very easy for the targeted users to mitigate the "attack". It can be very
much compared to spamming a room with "@room" messages.

The default power level for `m.rtc.notification` is `50` and equivalent to the default
power level required for `m.rtc.member` state events.

Additional control is provided indirectly with the use of intentional mentions.
Setting `"notifications":{"room":X}` allows to choose `X` for the power required
level to ring the whole room.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

- Use `org.matrix.msc4075.rtc.notification` in place of `m.rtc.notification` as the event type
- Use `org.matrix.msc4075.rtc.session_parent` in place of `m.rtc.session_parent` relation type.

## Dependencies

This MSC builds on [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143).
