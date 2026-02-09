# MSC3881: Remotely toggling push notifications for another client

The [push notification API](https://spec.matrix.org/v1.3/client-server-api/#push-notifications) allows clients to
register HTTP pushers so that they can receive notifications. An HTTP pusher is always tied to a specific Matrix device
due to its `pushkey` property which is issued by the particular platform (e.g. an APNS token). As a client is aware of
its `pushkey`s, it can identify its own pushers and remove or read them as needed. There is, however, no way to modify a
client's pushers from another client logged into the same account because the latter isn't aware of the former's
`pushkey`s.

This is limiting because it means that push notifications can only be en- or disabled on the device that is receiving
them. When the latter isn't currently at hand, this can become a point of frustration.

The current proposal solves this problem by making the connection between HTTP pushers and Matrix devices explicit and
assigning an enabled state to every pusher. This enables clients to remotely silence (and un-silence) notifications for
other devices. For users with multiple active devices, this means they can avoid unwanted interruptions or duplicate
pings without having to switch context and physically retrieve each device to change settings. A common example is
silencing a mobile device once you sit down at your desktop.

## Proposal

### Pusher-dependent clients

#### Disabling pushers
A new optional field `enabled` is added to the `Pusher` model.

| Name | Type | Description |
|------|------|-------------|
| `enabled` | boolean | **Optional** Whether the pusher should actively create push notifications

In [POST /_matrix/client/v3/pushers/set](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3pushersset)
the value is optional and if omitted, defaults to `true`.

In [GET /_matrix/client/v3/pushers](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3pushers) the value
is always returned.

Pushers that are not enabled do not produce push notifications of any kind, either by sending
[`/notify`](https://spec.matrix.org/v1.3/push-gateway-api/#post_matrixpushv1notify) requests to push providers for
`http` pushers or otherwise.

#### Explicitly linking device and pusher
A new optional field `device_id` is added to the `Pusher` model as returned from [GET
/_matrix/client/v3/pushers](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3pushers).

| Name | Type | Description |
|------|------|-------------|
| `device_id` | string | **Optional** The device_id of the session that registered the pusher


To be able to remove Pushers when sessions are deleted some homeservers have some existing way to link a session to
pusher, so exposing the `device_id` on http pushers should be trivial. (Synapse, for instance, stores the [access
token](https://github.com/matrix-org/synapse/blob/3d201151152ca8ba9b9aae8da5b76a26044cc85f/synapse/storage/databases/main/pusher.py#L487)
when adding a pusher, which is usually associated with a device)

In [GET /_matrix/client/v3/pushers](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv3pushers) the value
is optional.

### Pusher-less clients

Pausing notifications for clients that create notifications outside of the Push Gateway will not be addressed in this
MSC.

## Potential issues

Adding an enabled state to pushers increases the complexity of the push notification API. In addition to a pusher
existing or not existing, implementations now have to also evaluate the pusher's `enabled` field.

## Alternatives


#### Profile tags
The spec allows for pushers to be assigned a
[`profile_tag`](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3pushersset) which can be used to
define per-device push rule sets. In combination with the `notify_in_app` action proposed in
[MSC3768](https://github.com/matrix-org/matrix-spec-proposals/pull/3768) this would allow to toggle a pusher between the
`global` push rule set and a push rule set where all rules with `notify` actions were overridden to use `notify_in_app`.
Furthermore, the overrides could be simplified through cascading profile tags as proposed in
[MSC3837](https://github.com/matrix-org/matrix-spec-proposals/pull/3837). Keeping the two sets in sync would, however,
not be trivial. Additionally, profile tags are only partially spec'ed and there is active interest in
[removing](https://github.com/matrix-org/matrix-spec/issues/637) them entirely.

#### Client side notification filtering
Another alternative is client-side notification filtering at the time of delivery which is supported on many platforms.
This feature could be (ab)used to create the _impression_ of paused push notifications. The downside, however, is that
this is not a true deactivation and the wasteful overhead of sending and processing push notifications still exists.

#### Caching pusher-client relationships in account_data
Finally, when registering a pusher, a client could store the request body for
[/_matrix/client/v3/pushers/set](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3pushersset) in a
per-device account data event. Other clients of the same user could then issue network request on the client's behalf
using the body of said event. This appears somewhat kludgey though and would also conflict with existing home server
logic to store access tokens when adding or modifying pushers.

## Security considerations

None.

## Unstable prefix

Until this proposal lands
    
- `enabled` should be referred to as `org.matrix.msc3881.enabled`
- `device_id` should be referred to as `org.matrix.msc3881.device_id`

### Migration

Home servers should indicate their support of this MSC by adding `org.matrix.msc3881` and `org.matrix.msc3881.stable` in
the response of `/_matrix/client/versions`.

Clients that connect to a home server that doesn't yet support this proposal should interpret a missing `enabled` value
as `true`.

Home servers should migrate pushers that were registered before this proposal so that `enabled` is `true`

## Dependencies

None.

