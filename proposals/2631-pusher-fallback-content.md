# MSC2631: Add `fallback_content` parameter to `PusherData`

[pushers/set](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-pushers-set) allows users to create a pusher with `PusherData` with `http` kind pushers.

This proposal suggests adding a new parameter to `PusherData` object which will be honored by *Push Gateways* to decide providing a default value for `alert` field or not, and relatedly `mutable-content` field. So *Push Gateways* can be compatible with iOS `Notification Service Extension` mechanism.<sup>[[ref]](#references)</sup>

## Proposal

**New parameter on `PusherData`**

To the current parameters of [PusherData](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-pushers-set), we add
`fallback_content`, defined as:

 * `fallback_content` (`Boolean`): If provided as `true`, causes *Push Gateway* to include staticly valued `alert` and `mutable-content` keys in the `aps` field of the payload as:

```
{
  "mutable-content": 1,
  "alert": { "loc-key": "SINGLE_UNREAD", "loc-args": [] }
}
```

Has no effect if not provided or `false`, or even `format` is not equal to `event_id_only`. Default value is `false`.

## Potential issues

None currently foreseen.

## Alternatives

None feasible currently.

## Security considerations

None currently foreseen.

<h2 id="references">References</h2>

This document was based on an initial discussion at https://docs.google.com/document/d/1NsSj-nK-nP5DJNgj3O3MmXMdYLfbFcQLTl9RNRrs5ng.
