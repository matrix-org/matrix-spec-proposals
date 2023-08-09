# MSC4028: Push all encrypted events except for muted rooms

About notifications handling, it is currently not possible for mobile clients which get push notifications to properly implement a mentions-and-keywords-only room when encryption is enabled.

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

When this push rule matches then homeserver would push the event to all registered clients, similar to how other rules work. Clients would [decrypt the event and re-run push rules](https://spec.matrix.org/v1.7/client-server-api/#receiving-notifications) as normal. If the decrypted event results in no notification, the push is discarded [^2]. If the decryption failed, the new `.m.rule.encrypted_event` rule will match on client side, but there is no reason to notify the end user, so the push is discarded [^2] too. Globally the client must discard the push when the event stays encrypted locally because this use case should not happen except if the event was not encrypted for the current session, or if we are in front of an unexpected "Unable To Decrypt" (UTD) issue.

The overall tradeoff is that clients will receive extra pushes some of the time.

### Unread notification counts

Since the encryption has been introduced, the actual unread notification counts have to be updated/computed at the client side for the **encrypted rooms**. Nothing has been specified for that, so each client implemented its own mechanism. We want to harmonize this here.

As soon as the rule `.m.rule.encrypted_event` is present and enabled in the account push rules set, all the clients with or without push services should compute the unread notification count for each encrypted room during the client-server sync, by implementing the algorithm described below. Its complexity is similar to the existing implementations.

This algorithm depends on the unread notification count `unread_notifications` received from the server for each joined room in the [sync response](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientv3sync). It has to be adapted to the potential unread thread notification counts `unread_thread_notifications` that we will ignore here to ease the description.

Let's consider we receive the following data for a joined encrypted rooms in the sync response:
- number of new encrypted events in the timeline: n
- unread notification count: k

1. if k = 0 -> reset the local notification counts for this room (the unread notification count and the highlight count).
2. else if k <= n -> reset the local notification counts, then decrypt and run push rules on the k most recent events:
   - if the decrypted event resulted in a highlight notification -> increment the local highlight notifications count and the local unread notification count.
   - if the decrypted event results in a notification -> increment only the local unread notifications count.
   - if the decrypted event results in no notification -> no change is required on the local notification counts.
   - if the decryption failed -> increment the local unread notifications count.
3. else if k > n and no gap is mentioned in the sync response for this room -> update the local notification counts by taking into account the potential change of the read receipt position of the current user, then decrypt and run push rules on the n received events by applying the same rules as above.
4. else if k > n and a gap is mentioned in the sync response -> there is 2 options: 
- flush the local room storage, this will reset the local notification counts, then decrypt and run push rules on the n received events by applying the same rules as above. In order to compute locally accurate notification counts, back paginate to retrieve (k-n) more encrypted events.

or

- update the local notification counts by taking into account the potential change of the read receipt position of the current user, then decrypt and run push rules on the n received events by applying the same rules as above. In order to compute locally accurate notification counts, back paginate to close the gap or at least retrieve (k-n) more encrypted events.

About the case 4, the back pagination should be mandatory for mentions-and-keywords-only rooms to detect if there are some mentions in the gap. The client may decide to not trigger back pagination for rooms in "all messages" mode, but in that case the local unread notification count is unknown. No badge can be displayed at the application side, only an unread marker.

Note: some unencrypted events (for example `m.room.redaction`) may be taken into account or not in this unreads count k. This depends on the push rules set. If you force "all messages" mode on a room by creating a room-specific push rule, some unencrypted events (like redaction events) will be included in this count. This is not the case if "all messages" mode is obtained by the combination of server predefined rules. The client have locally all the information (= the push rules) to handle this edge case during the implementation of the algorithm.

### Listing notifications

This new push rule will impact the existing endpoint [`GET /_matrix/client/v3/notifications`](https://spec.matrix.org/v1.7/client-server-api/#get_matrixclientv3notifications).

When this rule will be present and enabled in the account push rules set, the clients which retrieve the list of events that it has been notified about with this endpoint, will receive most of the encrypted events (except for muted rooms). They will be able to decrypt and re-run push rules locally. This should fix the notifications panel observed in some web clients where currently the notifications of encrypted events are missing.

## Potential issues

### Client side

#### Unexpected unread counts
Until a client is updated to support this MSC, it may display a high number of unread notifications for encrypted rooms. The first workaround would be to not display the count for the encrypted rooms when the rule `.m.rule.encrypted_event` is present and enabled in the account push rules set, until the suggested algorithm is implemented, at least for the mentions-and-keywords-only encrypted rooms.

#### Battery life
The mobile client will wake up more frequently than currently. We will have to control any potential issue with battery life when we will implement this MSC. The impact on the battery life will be definitely lower than the one observed on clients without push service which poll for events in the background. The end user will be able to reduce the impact by muting some encrypted rooms. 

### Server side

#### Event fetching
The clients with push services will request more frequently the server to retrieve the event contents. I'm mainly thinking about an encrypted room with a high number of members, each mobile client of these members will try to retrieve simultaneously the event content of each new encrypted event (pushed by the server). This scenario may happen today only when most of the members configure the room in "All messages" mode.

This may be a potential performance issue if each client fetches separately each pushed event. But this should not be the case, because the clients have to run a sync if they want to be able to receive potential new encryption keys through to_devices. So they will retrieve more than one event at the time.

#### Push sending
Push is a huge bottleneck on the sending side. So calculating what to push and the unread counts (its the same process) is a big performance bottleneck currently when sending in large rooms. A bunch of optimisation has taken place to make that better, but its still quite expensive. We should plan an effort to limit potential issue server side here.

## Alternatives

[MSC3996: Encrypted mentions-only rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/3996): the suggested top-level property `m.has_mentions` may be an option to reduce the volume of pushes. But we would not be able to support notifications on keywords then.

Another alternative would be to define a new [`action`](https://spec.matrix.org/v1.7/client-server-api/#actions): `push_without_notify` or `silently_notify` in order to push all encrypted events without incrementing the notifications count. The client implementation to handle these counts would be then less complex. But this would need to implement more changes in Synapse. The current proposal is just to add a new push rules without changing the rules handling server side. This alternative should be discussed as soon as possible.

## Security considerations

None

## Future extensions

None

## Unstable prefix

During development the new push rule shall use `org.matrix.msc4028.encrypted_event` instead of `.m.rule.encrypted_event`. Contrary to the stable push rule, this unstable one should not be enabled by default until the clients are ready to support a minimum this MSC.

## Dependencies

None


[^1]: Via either an explicit `"dont_notify"` action or an empty array. These are
equivalent, see [issue #643](https://github.com/matrix-org/matrix-spec/issues/643).

[^2]: In the past it was not possible to discard notifications on iOS: if a push
notification was received it *had to be displayed*. This is [no longer the case](https://developer.apple.com/documentation/bundleresources/entitlements/com_apple_developer_usernotifications_filtering).
