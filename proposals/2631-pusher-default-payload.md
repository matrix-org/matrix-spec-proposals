# MSC2631: Add `default_payload` parameter to `PusherData`

[pushers/set](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-pushers-set) allows users to create a pusher with `PusherData` with `http` kind pushers.

This proposal suggests adding a new parameter to `PusherData` object which will be honored by *Push Gateways* to decide providing a default payload when computing the APNS and GCM payloads. So clients may have some default payload parameters for free. For instance, for the iOS side, *Push Gateways* can be made compatible with iOS `Notification Service Extension` mechanism<sup>[[ref]](#references)</sup>, if iOS clients configure the pusher to do so.

## Proposal

**New parameter on `PusherData`**

To the current parameters of [PusherData](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-pushers-set), we add
`default_payload`, defined as:

 * `default_payload` (`object`): If provided, causes *Push Gateway* to include values from this JSON data in payload, and then do incremental changes upon the payload, according to other parameters like `event_id_only`.

Has no effect if not provided or as `{}`. Default value is `None`.

## Potential issues

None currently foreseen.

## Security considerations

None currently foreseen.

<h2 id="references">References</h2>

This document was based on an initial discussion at https://docs.google.com/document/d/1NsSj-nK-nP5DJNgj3O3MmXMdYLfbFcQLTl9RNRrs5ng.
