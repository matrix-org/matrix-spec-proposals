# MSC3361: Opportunistic Direct Push

Mobile applications usually have to rely on a proprietary push provider for delivering messages to the phone they run on. These providers don't allow self-hosting, and aren't exactly known to respect the privacy of their users.

When a mobile application established a direct connection to a homeserver, pushes can be delivered directly through this connection to reduce metadata leakage to external push providers.

This approach is especially effective in the usual case of starting a conversation through a push and then replying instantly several times.


## Proposal

A new property is added to the response scheme of the `sync` operation: The `notifications` property with type `[Notification]` (like in `getNotifications`). The homeserver can use this property to deliver notifications directly.

A new pusher kind `direct` is added, so clients can opt-in to receive notifications in the sync response.

Homeservers should include the event and the corresponding notification in a single sync response.

For `direct` pushers, the homeserver must mark a notification as successfully sent only if the client issues the next sync with `next_batch` set to the `next_batch` of the sync response that included the notification. Therefore, notifications are never lost even if the connection unexpectedly fails.

If `direct` and `http` pushers are present, it is sufficient when the homeserver has successfully sent each notification to either the `direct` or the `http` pushers. (Alternatively, explicitly model relationships between pushers with something like a `fallback` parameter?) If a sync is pending or was pending a few seconds ago, delivery of notifications to `http` pushers must be delayed by a few seconds, so direct delivery can succeed. Both pending sync timeout and http delivery delay can be configured with parameters in the `direct` pusher. (How?)

When a clearing notification is issued that clears an unsent, delayed notification, the homeserver can cancel both notifications.


## Potential issues


## Alternatives


## Security considerations


## Unstable prefix
