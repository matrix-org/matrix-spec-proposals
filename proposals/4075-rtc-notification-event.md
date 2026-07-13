# MSC4075: MatrixRTC notifications & call ringing

Notifications for MatrixRTC applications as per [MSC4143] differ from normal chat notifications.
There are also differences between MatrixRTC applications. For calling applications, for instance,
being able to ring other participants for a specific time to prompt them to join the call is a
standard use case. Whiteboard applications in turn might want to send completely different
notifications.

While it's possible to base notifications on push rules and the existing [MatrixRTC][MSC4143]
membership events, providing notification metadata in those events directly overloads them. Instead,
this proposal introduces a dedicated timeline event to trigger application-specific MatrixRTC
notifications and defines notifications for the `m.call` application type from [MSC4196].

## Proposal

A new event `m.rtc.notification` is introduced which can be sent by clients to notify others about
the existence of a session for a specific MatrixRTC application.

``` json5
{
  "type":"m.rtc.notification",
  "content": {
    "application": {
      // MatrixRTC application type
      "type": "...",
      // Application-specific notification metadata
      ...
    },
    "m.text": [{"body": "Session started by {sender}"}],
    "m.mentions": {"user_ids": [], "room": true | false},
    "m.relates_to": {"rel_type":"m.reference", "event_id":"$rtc_member_event_id"}
  }
}
```

- `application` (required):\
  A JSON object that MUST specify the application type and MAY include additional fields to convey
  required metadata for processing the notification.
- `m.text` (required):\
  A fallback textual representation of the notification as per [MSC1767].
- `m.mentions` (required):\
  As defined by `m.mentions` in the [Client-Server API]. Declares which users the notification
  targets.
- `m.relates_to` (required):\
  An `m.reference` relation to the `m.rtc.member` event of the notifying member. This can be used to
  gather session data for this notification event.

Clients can only send `m.rtc.notification` events after having sent their `m.rtc.member` event due
to the required relation between both events.

Clients SHOULD send `m.rtc.notification` as a sticky event as per [MSC4354] for the associated
delivery guarantee.

The receiving client SHOULD only notify the user if all of the following conditions apply:

- The notification event is not filtered out by the current push rules.
- The user is included in the `m.mentions` section (either directly or via `room = true`).
- The sender's `m.rtc.member` event connects them to an open MatrixRTC slot in the room.
- The user is not already connected to the respective MatrixRTC session via an `m.rtc.member` event.

Active notifications SHOULD be cancelled if any of these conditions stop being valid later.

How the notification is displayed to the user is specific to both the application and the client.

If the receiving client doesn't support the referenced application type, it SHOULD use the `m.text`
fallback to visualise the notification.

### Call ringing

For notifications associated with `m.call` applications as per [MSC4196], additional properties are
introduced in the `application` content block to enable ringing and notifying recipients.

``` json5
{
  "application": {
    "type": "m.call",
    "notification_type": "ring | notification",
    "sender_ts": 1752583130365,
    "lifetime": 30000
    "m.call.intent": "audio | video | something-else",
  }
}
```

- `notification_type` (required):\
  The type of notification to trigger. One of `ring`, `notification`.
- `sender_ts` (required):\
  The local timestamp on the sending device when the event was emitted. This is used in combination
  with `lifetime` to evaluate if the notification event is valid. To mitigate clients lying about
  the `sender_ts`, this value has to be checked against `origin_server_ts`. Receivers SHOULD use
  `origin_server_ts` if `|sender_ts - origin_server_ts| > 20000 ms`.
- `lifetime` (required if `notification_type` is `ring`, otherwise ignored):\
  The time in milliseconds relative to `sender_ts` for which the notification should be considered
  active. The recommended value is 30 seconds. The receiving client SHOULD cap the lifetime to an
  upper bound (recommended: 2 minutes). `lifetime` MUST be non-negative and SHOULD NOT exceed 120000
  ms.
- `m.call.intent`:\
  The intent of the call as per [MSC4196].

For `notification_type == "ring"`, the receiving client should audibly notify the user while for
`notification_type == "notification"` a visual indication is enough. Further specifics of how the
notification is presented to the user, including the ringing sound, are left to the receiving
client.

After sending a notification event with `notification_type = ring`, the client SHOULD indicate to
the sending user that the recipients are currently being rung until either:

- `sender_ts + lifetime` has elapsed or
- the sender has disconnected from the session or
- all recipients have connected to the session.

On top of the application-independent requirements from above, receiving clients SHOULD ignore
notification events if:

- The event's `lifetime` as measured from `sender_ts` / `origin_server_ts` has elapsed. This
  prevents outdated notification events from causing notifications.
- The client is already presenting an earlier notification event for the same session.

#### Optimistic ringing

For `notification_type = ring`, receiving clients MAY start optimistically ringing the user ahead of
validating the sender's `m.rtc.member` event and the associated `m.rtc.slot` event provided that all
other conditions pass. This helps reduce ringing delay if the client has to fetch the events from
the server.

    optimistic
    ---------------|====== ring ======|====== ring ======|
    pessimistic
    ---------------|------------------|====== ring ======|
    ^              ^                  ^
    notification   notification       MatrixRTC session
    event sent     event received     validated
                   and validated
                   locally

If the membership and slot event later fail validation, the client should stop ringing. This may
result in an intermediate erroneous ring.

    optimistic
    ---------------|====== ring ======|------------------|
    pessimistic
    ---------------|------------------|------------------|
    ^              ^                  ^
    notification   notification       MatrixRTC session
    event sent     event received     failed to validate
                   and validated
                   locally

#### Ringing acknowledgements

Federation delay, server load and client connectivity may drastically reduce the effective ringing
time for the receiving user. At the same time, the sender gets no indication of whether or not his
ring has reached the receiver at all. To mitigate this, ringing acknowledgements are introduced.

Acknowledgements are to-device messages of the type `m.call.ring.ack` with a `sender_ts` property in
their content object that indicates the timestamp at which the to-device message was sent.

Receiving clients MAY send acknowledgements back to the sender once they start ringing. If they do,
they MUST measure `lifetime` from the `sender_ts` timestamp they submitted back rather than from
`sender_ts` / `origin_ts` in the notification event.

The sending client in turn should restart its own measurement of `lifetime` with every received
acknowledgement based on the contained `sender_ts`. This does not apply if an acknowledgement
arrives after the sender has disconnected from the session or has determined the (possibly
restarted) `lifetime` to be exceeded.

    *  ringing (outgoing or incoming)
    .  previous ring duration overridden by an ack.

                                              offline
            sender    receiverA   receiverB    device
              |           |           |           |
             *|--notif.-->|--notif.-->|           |
             *|           |           |           |
           * *|<---ack.---|*          |           |
           * .|           |*          |           |
         * * .|<----------|*---ack.---|*          |
         * . .|           |*          |*          |
         * .  |           |*          |*          |
         * .  |           |*          |*          |
         *    |           |           |*          |
         *    |           |           |*          |
              |           |           |           |

In order to be able to send the to-device messages, the sender's device ID is included as a
mandatory property `device_id` inside the `application` object of the notification event.

Clients SHOULD set the notification event's sticky duration to at least twice the `lifetime` to
account for incoming acknowledgements extending the ringing.

## Potential issues

### Event size limits

Adding a large number of users in `m.mentions` can lead to the event exceeding the 64kiB event size
limit. Clients can use @room mentioning or send multiple notification events to handle this.

### Abuse of optimistic ringing

Malicious clients could spam notification events that link to invalid MatrixRTC sessions causing
clients that ring optimistically to notify the user erroneously while the session check is pending.
Receiving clients can mitigate this by adapting their notification settings for the room.

## Alternatives

### Infer ringing from membership events

Notifications could be based off of the `m.rtc.member` events from [MSC4143].

Pros:

- No separate event type meaning slightly less traffic.
- Clients cannot "forget" to notify others about a session starting because membership events are
  required to connect to a session.

Cons:

- Including notification metadata in `m.rtc.member` events would bloat them.
- Not including notification metadata in `m.rtc.member` events would mean that all the ringing
  conditions are on the receiving user. There would be no way for users to decide whether their
  membership event should notify other people in the room let alone which ones.
- Would be difficult to extend later to allow external services (such as a meeting organizer bot) to
  send notifications without having an `m.rtc.member` event.

### Measure lifetime from first acknowledgement

Rather than having senders restart their lifetime countdown with every acknowledgement, they could
only do it for the first to arrive. This could result in different ringing durations on receiving
clients though which might negatively impact a user's ability to answer the call.

### Synchronise acknowledgements among receivers

To enable receiving clients to stop ringing at the same time, acknowledgements could also be
exchanged between all receiving devices. This would vastly increase the number of required to-device
messages, however. Additionally, it would optimise for the case where the user observes but doesn't
answer the call. This can be considered rare in practice as not answering will often be due to not
observing the ring.

### Memberless ringing

The required relation to the sender's member event prevents users that are not part of the session
from sending notification events. This might be a use case though, for instance, in the form of
calendar bots. To enable this, the relation could be anchored on the slot event instead. This,
however, means that membership disconnects (the sender hung up) could no longer be used to determine
if ringing on the receiver's side can end. Since the concrete use case hasn't been validated yet,
supporting it is descoped to a future proposal.

## Security considerations

The `m.rtc.notification` event allows room participants to send notifications to other users which
could be an abuse vector especially when using ringing. Since notification events are still subject
to push rules, however, it is easy for targeted users to mitigate this "attack".

Additional control is provided via power levels for `m.mentions`. Setting
`"notifications": { "room": X }` allows to configure the level `X` required to be able to notify the
whole room.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should use:

- `org.matrix.msc4075.rtc.notification` in place of `m.rtc.notification` as the timeline event type
- `org.matrix.msc4075.call.ring.ack` in place of `m.call.ring.ack` as the to-device message's event
  type

## Dependencies

This MSC builds on:

- [MSC4143: MatrixRTC][MSC4143]

- [MSC4196: MatrixRTC voice and video calling application `m.call`][MSC4196]

- [MSC4354: Sticky events][MSC4354]

  [MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
  [MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196
  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [Client-Server API]: https://spec.matrix.org/v1.11/client-server-api/#definition-mmentions
  [MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354
