# MSC4452: Preview URL capabilities API

It's possible for server admins / implementations to disable the [GET /_matrix/client/v1/media/preview_url](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv1mediapreview_url) endpoint. This may be done for a variety of
reasons ranging from IT policies to bandwidth conservation, but in practice
this has been a feature for some time[^1].

Clients need to know about the state of this feature as it allows them to show the
state in the application's settings. Ultimately this means that users can know whether
to expect previews to appear in their rooms. Without this capability, users have no
knowledge of whether previews will work and will direct frustrations at the application
for not supplying a preview they have asked for. Hence, having proper access to the
state is useful.


This proposal suggests informing clients of this configuration through the standard
capabilities API.

## Proposal

The [GET /_matrix/client/v3/capabilities](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3capabilities)
will include a new capability key, `m.preview_url` containing a single `enabled` flag.

```json
{
  "capabilities": {
    "m.preview_url": {
      "enabled": true
    }
  }
}
```

If `enabled` is `false`, any attempt to use `GET /_matrix/client/v1/media/preview_url` MUST be rejected with
a `403` `M_FORBIDDEN` error.

If `enabled` is `true` or not defined, then the client can make queries as normal. This means that the existing
behaviour is preserved so that servers who do not support this capability will not prevent clients from
requesting previews.

Servers MAY elect to allow some users access to this endpoint, so the response may be different
depending on the authenticated user (e.g. disabled for guest users).

## Potential issues

This increases complexity for clients who offer URL previews as a feature. They will need to check
the capabilities offered by the homeserver before they can start making requests. This has been mitigated
by reusing the capabilities endpoint. For the reasons outlined in Alternatives, it's an acceptable
tradeoff to include a capability for this feature.

## Alternatives

In practice most implementations of URL previews either allow the server admin to disable/enable it, or do
not support it. With that in mind, an alternative could be to just standardise the error code without the capability.
However, this is a problem for three reasons.

1. Clients will continue to make requests to the homeserver even if the feature is disabled, increasing the amount of traffic
   the server needs to handle.
2. Clients will leak URLs to the homeserver (which may be within encrypted messages). While this is an acceptable trade-off
   if the feature works, it's pointless if the requests are being failed.
3. Clients often allow users to choose whether they want the feature on. It's useful to show the option as disabled
   if the homeserver doesn't support it.

Therefore, having both the error and the capability would be the best way forward.

## Security considerations

It's just a flag indicating whether you can use an endpoint, so none.

## Unstable prefix

`io.element.msc4452.preview_url` should be used instead of `m.preview_url` while this MSC is considered
unstable.

[^1]: https://github.com/element-hq/synapse/commit/dafef5a688b8684232346a26a789a2da600ec58e

## Dependencies

None.
