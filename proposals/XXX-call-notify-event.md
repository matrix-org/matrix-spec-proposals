# MSC0000: MatrixRTC Call Ringing
It is important that a call initiated on clientA can make targeted clients ring.
This is of interest in 1:1 Rooms/Calls but also in bigger rooms ringing can be desired.

Legacy calls are using room events to negotiate the call. A client could use the initial steps in the negotiation to also make the phone ring.

With matrix RTC based calls this signalling is done over state events. Also matrix RTC enables large group calls which makes it very desirable to have more configurations over the ringing process.

## Proposal

A new event `m.call.notify` is proposed which can be sent by a client that wants to start a call. 
This event is added to the push rules for clients which support calling so they get push notifications. The push rules for intentional mentions make sure no unnecessary push notification is sent.

This event contains the following fields by leveraging intentional mentions.

```json
{
  "content": {
    "application": "m.call" | "m.other_matrix_session_type" | "...",
    "m.mentions": {"user_ids": [], "room": true | false},
    "notify_type": "ring" | "notification",
    // Application specific data,
    // optional fields to disambiguate which session 
    // this notify event belongs to:

    // for application = "m.call":
    "call_id": "some_id",
  }
}
```

In the following we define **call** as any matrix RTC session with the same `"application"` and the same application specific data. In the calse of `"m.call"`, the same `"call_id"`.

On retrieval, the event should not be rendered in the timeline. But if the notify conditions (listed below) apply, the client has to inform the user about the **call** with an appropriate user flow. 
For `notify_by == "ring"` some kind of sound is required (except if overwritten by another client specific setting), 
for `notify_by == "notification"` a visual indication is enough. This visual indication should be more than an unread indicator and similar to a notification banner. This is not enforced by the spec however and ultimately a client choice.

Notify conditions depend on:\
(here we use )
 - `m.call.notify` content:\
    If the user is not part of the `m.mentions` section as defined in [MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952) this event can be ignored. (Push notifications are automatically filtered so this only is important for events received via a sync)
 - Local notification settings:\
    If the room is set to silent, it will never play a ring sound. A `m.call.notify` event will at most be used to mark the room as unread or update the rooms "has active **call** icon". (the exact behavior is up to the client)
 - Currently playing a ring sound (room timeline):\
    If the user already received a ring event for this **call** and is playing the ring sound any incoming `m.call.notify` for the same **call** should be ignored. If the user failed to pick up and a new `m.call.notify` arrives for the same room the device should ring again.
 - Current user is a member of the the **call** (room state):\
    None of the devices should ring if they receive a `m.call.notify` if the rooms state `m.call.member` event of the user contains a membership for the **call** in the `m.call.notify` event.
    This includes stopping the current ring sound if the room state updates so this condition is true.

Sending a `m.call.notify` should happen if all of these conditions apply:
 - If the user deliberately wants to send a new notify event (It is possible to send a `m.call.notify` for an ongoing call if that makes sense. Starting a call ahead of time, planning in a small group, ringing another set of users at a specific time so they don't forget to join. Ringing one specific user again who missed joining during the first ring.)
 - If the user has not yet received a `m.call.notify` for the **call** they want to participate but the other condition applies. (So the obvious case is, that this is the first user in a new call session).


## Potential issues


## Alternatives

It would be possible to use the call member room state events to determine a call start.
The logic would be as following:

*If we receive an event we check if there is are already other members (call.member events) for the call. In case there is not we make the phone ring.*

Pros:
 - This would not require any new event.
 - The clients can not "forget" to ring the others about the when they start a new call. Because they would automatically send an event by joining.
 - There would be less traffic. With the proposed solution the first one who joins needs to send a `m.call.notify` event and a `m.call.member` state event.
 - Very flexible, since the `m.call.notify` event is separate from a call participation. This allows an external instance (a meeting organizer bot) to just ring all the users which are invited to a meeting without needing to be part of the call.

Cons
 - All the ringing conditions run on the receiving user. There is no way for the user who start the call to decide if it should ring the other participants. (Consider a very large room where I want to start a call only for the interested ones who want to discuss a side project. It would be very annoying if the initiator could not control how and who is going to be informed about that call.)
 - Push notifications would need to be sent for EVERY `m.call.member` state event update. For each joining and leaving user and for each membership update during a call (due to a SFU (single forwarding unit) change, changing devices (could even happen for screen shares if the screen share is implemented as a separate participating device) or matrix RTC business logic of the call.) - This could result in a lot of push notification with no obvious/simple way to filter them.
 - It would require bloating the `call.member` event if the `notify_type` or a specific list of users to notify want to be specified.
 - It would not make it possible to ring without participating.

## Security considerations
This is another timeline event where any room participant can send a push notification to others. Since this will make clients ring this has a higher effect on the receiver. Since ringing has to obey the mute settings, it is very easy for the targeted users to mitigate the "attack". It can be very much compared to spamming a room with "@room" messages.

## Unstable prefix
While this MSC is not present in the spec, clients and widgets should:
   - Use org.matrix.mscXXXX. in place of m. in all new identifiers of this MSC. (`m.call.notify`)

## Dependencies

This MSC builds on Intentional Mentions [MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952).
