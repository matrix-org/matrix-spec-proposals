# MSC3890: Remotely silence local notifications
Some clients (eg Element Web) do not use http pushers for notifications, but rather generate their own notifications in
the client based on the `/sync` response. Users should be able to remotely toggle on and off these notifications (as
well as [push notifications (MSC3881)](https://github.com/matrix-org/matrix-spec-proposals/pull/3881)) to control
interruptions and reachability in private and professional contexts.

To allow these clients to silence notifications remotely we will use account data and client-side notification
filtering.

This proposal seeks to silence interrupting notifications that are generated in the client. This includes:
- system notifications such as system banners, popups, system notification center
- sounds, including noisy notifications and ringers

In-app notifications will not be affected, with in-app notification center, badges, unread markers and counts remaining
the same.

*This proposal only refers to notifications that are generated on the client. Silencing of push notifications is covered
by [MSC3881: Remotely toggle push notifications](https://github.com/matrix-org/matrix-spec-proposals/pull/3881)*

## Proposal
Add a new account data event `m.local_notification_settings.<device-id>` with content:
```jsonp
{
    is_silenced: boolean
}
```

##### During client-side notification generation:

- While a registered pusher exists for the current device any `local_notification_settings` event should be ignored and
  events should trigger system notifications as normal. For servers that support
  [MSC3381](https://github.com/matrix-org/matrix-doc/pull/3881), the `local_notification_settings` is ignored and local
  notifications are triggered based on the `enabled` setting of the registered pusher.
- While no `local_notification_settings` event exists for the current device, or a `local_notification_settings` event
  exists where `is_silenced` is falsy, events should be processed as normal and trigger system notifications and sounds
  where necessary.
- While a `local_notification_settings` event exists for the current device where `is_silenced` is true, no event should
  trigger a system notification or sound.

##### Displaying notification settings:

Clients should endeavour to display notification settings that reflect the rules above.

- While a registered pusher exists for a device, notifications should be displayed as enabled. While the client has the
  ability to register/remove pushers for the device, toggling this setting should register or remove the pusher. For
  servers that support [MSC3381](https://github.com/matrix-org/matrix-doc/pull/3881), notifications should be displayed
  as enabled according to the `enabled` setting of the pusher. Changing this setting should update the `enabled`
  field of the pusher.
- While the client does not have the ability to register a pusher and a `local_notification_settings` event exists,
  notifications should be displayed as `enabled` when the event's `is_silenced` field is falsy. Updating the setting
  should change the event's `is_silenced` field.
- While the client does not have the ability to register a pusher and no `local_notification_settings` event exists,
    notifications should be displayed as disabled. The setting should not be editable.
  
##### During server-side removal of devices:

- When devices are removed servers should delete any `m.local_notification_settings.<device-id>` account_data events for
the given device, and communicate these changes to clients as described in
[MSC3391](https://github.com/matrix-org/matrix-spec-proposals/pull/3391).

A server is to clean up deleted device account data when able to do so, such as with [MSC3391: Removing account
data.](https://github.com/matrix-org/matrix-spec-proposals/pull/3391)

#### Support
Clients that implement `m.local_notification_settings.<device-id>` notification filtering should ensure a
`local_notification_settings` event exists for the active device to indicate support for that device. Clients should
only expose local notification silencing controls for devices that have indicated their support.

## Alternatives

#### Per device account data
To enable easier retrieval and management of device-scoped account data events a new per-device account data could be
introduced. This would behave similarly to per-room account data. Per-device account data events would be removed by the
server during device removal.
With per-device account data, the event type could be
simplified to `m.local_notification_settings`

#### Push rules with profile tags (aka per device push rules)
The spec allows for pushers to be assigned a
[`profile_tag`](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3pushersset) which can be used to
define per-device push rule sets. In combination with the `notify_in_app` action proposed in
[MSC3768](https://github.com/matrix-org/matrix-spec-proposals/pull/3768) this would allow to toggle a pusher between the
`global` push rule set and a push rule set where all rules with `notify` actions were overridden to use `notify_in_app`.
Furthermore, the overrides could be simplified through cascading profile tags as proposed in
[MSC3837](https://github.com/matrix-org/matrix-spec-proposals/pull/3837). Keeping the two sets in sync would, however,
not be trivial. Additionally, profile tags are only partially spec'ed and there is active interest in
[removing](https://github.com/matrix-org/matrix-spec/issues/637) them entirely. If feasible, this would allow for remote
control of notifications for clients using http-pushers and local notification generation.

Effective per device notification silencing using profile tags relies on a few complex pieces of work (push rules with
profile tags, `notify_in_app` push rule action, potentially cascading profile tags). While a more elegant solution, it
is unlikely to land in the short or medium term. This MSC proposes a short term fix for a common user issue. As
better solutions become available clients may choose to stop supporting `local_notification_settings`.

## Security considerations
N/A

## Unstable prefix
While this MSC is not included in the spec `m.local_notification_settings.<device-id>` should use the unstable prefix
`org.matrix.msc3890.local_notification_settings.<device-id>`
