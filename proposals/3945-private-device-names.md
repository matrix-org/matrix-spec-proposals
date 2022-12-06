# MSC3945: Private device names

Currently, a device's `display_name` is public; users can see other users'
devices' display names as part of the result of a `POST /keys/query` request.
This may reveal sensitive information, as device display names sometimes
identifies the type of device being used, or in some cases, even
[account names](https://github.com/vector-im/element-web/issues/2986).

In the past, the display name was useful for verifying devices, since users had
to verify devices individually, and had to select which device to verify;
asking someone to verify their device named "Dynabook" is much easier than
asking to verify the device with ID "OUDGQHN".

However, with
[cross-signing](https://github.com/matrix-org/matrix-spec-proposals/pull/1756),
users no longer need to verify devices individually, and so do not need to know
other users' device names.

We thus propose to make the device display names visible only to the user
owning the device.

Other links:

- Element-web issue: [we should consider not publishing device names in a
  cross-signing world](https://github.com/vector-im/element-web/issues/10153)
- Element-meta issue: [Rather than infer device names we should prompt users
  explicitly to name their devices when they log in](https://github.com/vector-im/element-meta/issues/382)

## Proposal

Any client-server endpoints that can return a device's `display_name` will only
do so for devices owned by the user calling the endpoint.  Currently, the only
affected endpoint is `POST /keys/query`.

On the federation side, all endpoints and EDUs will drop the
`device_display_name` fields.  Currently, the only affected endpoints are `GET
/user/devices/{userId}` and `POST /user/keys/query`, and the only affected EDU
is `m.device_list_update`.

### Compatibility with old servers

A server that implements this proposal should, as a one-time task, send updates
to other servers un-setting the device display names for its user's devices by
sending `m.device_list_update` EDUs with no `device_display_name` fields.  The
servers that these updates will be sent to are the same as servers that
`m.device_list_update` EDUs would have been sent to if the user would have
updated their device list.  Since this will case many EDUs to be sent, servers
should rate-limit sending the EDUs.

## Potential issues

The device display name may still be useful for debugging.  However, users who
are involved in debugging will likely be savvy enough to use the device ID
instead, and on the whole, the privacy benefits of hiding the device display
name outweigh the disadvantages.

## Alternatives

Rather than hiding the device name completely, we could have a public display
name and a private one.  However, this adds complexity, and does not seem to
have much benefit.

## Security considerations

None

## Unstable prefix

No unstable prefix is needed since fields are being removed.

## Dependencies

None
