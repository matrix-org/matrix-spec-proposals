# MSC4075: MatrixRTC Notification Event (call ringing)

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
  "type":"m.rtc.notification", // org.matrix.msc4075.rtc.notification
  "content": {
    "sender_ts": 1752583130365,
    "lifetime": 30000,
    "m.mentions": {"user_ids": [], "room": true | false},
    "m.relates_to": {"rel_type":"m.reference", "event_id":"$rtc_member_event_id"},
    "notification_type": "ring | notification",
  }
}
```

The fields are defined as follows:

- `sender_ts` the local timestamp observed by the sender device. Is used in combination with lifetime to evaluate if
  the notification event is valid. To mitigate clients lying about the `sender_ts` this value has to be checked with `origin_server_ts`.
  Receivers **SHOULD** use `origin_server_ts` if `|sender_ts - origin_server_ts| > 20000 ms`.
- `lifetime` the relative time to the `sender_ts` for which the `ring` is active or to define the window in which the
  `notification` is not ignored. The recommended value is **30 seconds**.
  The receiving client **SHOULD** cap the lifetime to an upper bound. (recommended: **2 minutes**).
  `lifetime` **MUST** be non-negative and SHOULD NOT exceed 120000 ms.

- `m.mentions` optional:\
  Has the structure as defined for `m.mentions` in the [Client-Server API](https://spec.matrix.org/v1.11/client-server-api/#definition-mmentions).
- `notification_type` required string:\
  The type of notification to send.\
  `ring`: The client should ring.\
  `notification`: The client should show a notification.\
- `m.relates_to`: optional:\
  A relation (with type: `m.reference`) to the session participation event
  (`m.rtc.member`) of the notifying member.
  If available this can be used to gather session data for this notification event.
  It should always be used if the notification is related to an RTC session.
  (Eventually this event might be used to send
  RTC session independent ringing notifications with a custom message. A bot-controlled tea timer for instance.)
The `session` information for this notification event can be obtained by the relation to the `m.rtc.member` event.

In the following we define **call** as any MatrixRTC session with the
same `"session"` contents.

### Client behaviour on receiving a `m.rtc.notification` event

On retrieval, the client should not render the event in the timeline.
If the notification conditions (listed below) apply,
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
  event should at most be used to mark the room as unread or update the room's
  "has active **call** icon". (the exact behaviour is up to the client)
- Currently playing a ring sound (room timeline):\
  If the user already received a ring event for this **call** and is playing
  the ring sound any incoming `m.rtc.notification` for the same **call**
  should be ignored. If the user failed to pick up and a new `m.rtc.notification`
  arrives for the same room the device should ring again.
- Current user is a member of the **call** (room state):\
  None of the devices should ring if they receive a `m.rtc.notification` if the
  room's state `m.rtc.member` event of the user contains a membership for
  the **call** in the `m.rtc.notification` event.
  This includes stopping the current ring sound if the room state updates so
  this condition is true.
- If a notification event is received in "real time":\
  Notify events that are older than **`lifetime`** are ignored (using the
  `sender_ts` timestamp).\
  Otherwise a client syncing for the first time would ring for outdated call events.
  In general ringing only makes sense in "real time".
  Any client which is not able to receive the event in the `lifetime` period should
  not ring to prohibit annoying/misleading/irrelevant/outdated rings.

### Client behaviour when sending a `m.rtc.notification` event

Sending a `m.rtc.notification` should only happen if all of these conditions apply:

- If the user deliberately wants to send a new notification event
  (It is possible to send a `m.rtc.notification` for an ongoing call if that
  makes sense. Starting a call ahead of time, planning in a small group,
  ringing another set of users at a specific time so they don't forget to join.
  Ringing one specific user again who missed joining during the first ring.)
- If the user has not yet received a `m.rtc.notification` for the **call** they want to
  participate but the other conditions apply. (So the obvious case is, that this
  is the first user in a new call session).
- If possible the user should send their `m.rtc.member` event first to allow setting up the relation
  for the notification event.
- The sending client can compute the "exact" (or at least "a good approximation"
  if the local clocks are not configured correctly) at which the
  `m.rtc.notification` ring will end using the `lifetime` + `sender_ts`.
  This allows the sending client to show a local dialling/ringing
  animation/indicator/sound.
  - The location to put this information would be the invite event.
  This would be an edge case and only required for the specific use case
    of being able to ring without a shared DM/Room.
    It should be discussed in an additional MSC and is not part of this proposal.

### Extensible Events

The concept of [extensible events](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1767-extensible-events.md)
is used to offer a fallback for clients that do not support notification events
and benefit from a fallback text representation.

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
The logic would be as follows:
*If we check if there are already other members
(`m.rtc.member` events) for the call. In case there is not we make the phone ring.*

Pros:

- This would not require any new event.
- Clients cannot "forget" to ring others about when they
  start a new call, because they would automatically send an event by joining.
- There would be less traffic. With the proposed solution the first one who joins
  needs to send a `m.rtc.notification` event and a `m.rtc.member` state event.

Cons

- All the ringing conditions run on the receiving user. There is no way for the
  user who starts the call to decide if it should ring the other participants.
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
  separate participating device) or MatrixRTC business logic of the call.)
  This could result in a lot of push notifications with no obvious/simple way to
  filter them.
- It would require bloating the `m.rtc.member` event if the `notification_type`
  or a specific list of users to notify want to be specified.
- It would not make it possible to ring without participating.

### Which properties are defined by the sender vs receiver

- The duration of the ring sound could be the receiving client's decision. This MSC
  tries to find a middle ground by allowing the sender to define a lifetime but
  the receiver can overwrite it in case that it is
  necessary for the expected client UX. This at least provides
  an expected ring duration that can be used for the sender UX.
  Ultimately the sender can never know how the receiving client
  will implement the ring. See [the related discussion](https://github.com/matrix-org/matrix-spec-proposals/pull/4075#discussion_r1597704775)
- The ring sound is a client choice. (It was considered to
  add the ring sound to the notification event but how "ringing" actually should
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

- Use `org.matrix.msc4075.rtc.notification` in place of `m.rtc.notification`
  as the event type

## Dependencies

This MSC builds on [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143).
