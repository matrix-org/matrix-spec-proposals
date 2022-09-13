# MSC3890: Remotely silence local notifications
Some clients (eg Element Web) do not use http pushers for notifications, but rather generate their own notifications in
the client based on the `/sync` response. Users should be able to remotely toggle on and off these notifications (as
well as [push notifications](https://github.com/matrix-org/matrix-spec-proposals/pull/3881)) to control interruptions
and reachability in private and professional contexts.

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
During client-side notification generation:
- While no `local_notification_settings` event exists for the current device, or a `local_notification_settings` event
  exists where `is_silenced` is falsy, events should be processed as normal and trigger system notifications and sounds
  where necessary.
- While a `local_notification_settings` event exists for the current device where `is_silenced` is true, no event should
  trigger a system notification or sound.

#### Support
Clients that implement `m.local_notification_settings.<device-id>` notification filtering should ensure a
`local_notification_settings` event exists for the active device to indicate support for that device. Clients should
only expose local notification silencing controls for devices that have indicated their support.

When a device is removed these events should be pruned by clients.

## Alternatives
#### Push rules with profile tags
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

## Security considerations
N/A

## Dependencies
Proper deletion of account data is enabled by [MSC3391: Removing account
data.](https://github.com/matrix-org/matrix-spec-proposals/pull/3391)

## Unstable prefix
While this MSC is not included in the spec `m.local_notification_settings.<device-id>` should use the unstable prefix
`m.msc3890.local_notification_settings.<device-id>`
