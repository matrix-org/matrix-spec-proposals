# MSC4028: Push all encrypted events except for muted rooms

About notifications handling, it is currently not possible for mobile clients which get push notifications to properly implement a mentions-and-keywords-only room.

Like it was already described in [MSC3996: Encrypted mentions-only rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/3996): 

Currently, every new event in an encrypted room might be pushed to mobile clients due to the default **underride** rule [`.m.rule.encrypted`](https://spec.matrix.org/v1.7/client-server-api/#default-underride-rules).

However, a room can be configured to be mentions-and-keywords-only by creating a [room-specific push rule](https://spec.matrix.org/v1.7/client-server-api/#push-rules)
with the `id` property set to the room ID & `actions` set to do nothing.[^1] Since this is evaluated *before* the `.m.rule.encrypted` rule (almost) **no events get pushed for a mentions-and-keywords-only room**.

Additionally, a room can be configured to be muted by creating the **override** [push rule](https://spec.matrix.org/v1.7/client-server-api/#push-rules) which matches the room ID & has `actions` set to do nothing, e.g.:

```json
{
    "rule_id": "!abcdef:example.com",
    "conditions": [
      {
         "key": "room_id",
         "kind": "event_match",
         "pattern": "!abcdef:example.com"
      }
    ],
    "default": false,
    "enabled": true,
    "actions": []
}
```

## Proposal

A new predefined **override** push rule (`.m.rule.encrypted_event`) is added just after the `.m.rule.master` push rule to be able to push all encrypted events:

```json
{
    "rule_id": ".m.rule.encrypted_event",
    "default": true,
    "enabled": true,
    "conditions": [
      {
         "kind": "event_match",
         "key": "type",
         "pattern": "m.room.encrypted"
      }
    ],
    "actions": ["notify"]
}
```

Note: The “user-defined rules” are evaluated with a higher priority than “server-default rules”, except for the `.m.rule.master` rule which has always a higher priority than any other rule (see [here](https://spec.matrix.org/v1.7/client-server-api/#predefined-rules)). So all the **override** push rules created to mute rooms will be evaluated before this new one. The new rule will be evaluated before all the other “server-default rules”. This new rule deprecates the existing underride rule [`.m.rule.encrypted`](https://spec.matrix.org/v1.7/client-server-api/#default-underride-rules), which will become useless.

### Receiving notifications

When this push rule matches then homeserver would push the event to all registered clients, similar to how other rules work. Clients would [decrypt the event and re-run push rules](https://spec.matrix.org/v1.7/client-server-api/#receiving-notifications) as normal, but they will consider at the same time the original event is encrypted. The following algorithm has to be implemented client side as soon as it received a push for an encrypted event **and** `.m.rule.encrypted_event` is present and enabled in the account push rules set:

1. If the decryption failed, the new `.m.rule.encrypted_event` rule will match on client side too. There is no reason to notify the end user. The push is discarded [^2]. The client decrements locally the number of unread notifications received from the homeserver for this room. We decided to discard here the push because this use case should not happen except if the event was not encrypted for the current session,
or if we are in front of an unexpected "Unable To Decrypt" (UTD) issue.  
2. If the decryption succeeded, there are 3 cases:
- the decrypted event resulted in a highlight notification -> the client increments locally the highlight notifications count for this room
- the decrypted event results in a notification -> no change is required on the notifications count
- the decrypted event results in no notification -> the client decrements locally the number of unread notifications for this room

The overall tradeoff is that clients will receive extra pushes some of the time.

### Listening notifications

This new push rule will impact the existing endpoint [`GET /_matrix/client/v3/notifications`](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientv3notifications).

When this rule will be present and enabled in the account push rules set, the clients which retrieve the list of events that it has been notified about with this endpoint, will receive most of the encrypted events (except for muted rooms). They will be able to decrypt and re-run push rules locally. This should fix the notifications panel observed in some web clients where currently the notifications of encrypted events are missing.

### Polling

The clients without push services (Web or F-Droid for example) will have to take into account this new push rule (if it is enabled) during their polling mechanism. Indeed they should update the unread notifications count by following the same algorithm as above. This algorithm should replace the potential current one.

## Potential issues

The clients without push may observe encrypted rooms with a high number of unread notifications in case of gappy sync. The workaround would be to not display the count for the room until the gap is completed or the count is reset (mark all as read).

## Alternatives

[MSC3996: Encrypted mentions-only rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/3996): the suggested top-level property `m.has_mentions` may be an option to reduce the volume of pushes. But we would not be able to support notifications on keywords then.

Another alternative would be to define a new [`action`](https://spec.matrix.org/v1.7/client-server-api/#actions): `push_without_notify` or `silently_notify` in order to push all encrypted events without incrementing the notifications count. The client implementation to handle these counts would be then less complex. But this would need to implement more changes in Synapse. The current proposal is just to add a new push rules without changing the rules handling server side. This alternative should be discussed as soon as possible.

## Security considerations

None

## Future extensions

None

## Unstable prefix

During development the new push rule shall use `org.matrix.msc40xx.encrypted_event` instead of `.m.rule.encrypted_event`.

## Dependencies

None


[^1]: Via either an explicit `"dont_notify"` action or an empty array. These are
equivalent, see [issue #643](https://github.com/matrix-org/matrix-spec/issues/643).

[^2]: In the past it was not possible to discard notifications on iOS: if a push
notification was received it *had to be displayed*. This is [no longer the case](https://developer.apple.com/documentation/bundleresources/entitlements/com_apple_developer_usernotifications_filtering).
