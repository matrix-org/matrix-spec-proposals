# MSC4452: Preview URL capabilities API

It's possible for server-side implementations to want to disallow users the [GET /_matrix/client/v1/media/preview_url](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv1mediapreview_url) endpoint. This is often done to either reduce excess
load on servers, for security reasons to avoid metadata leakage, or safety to prevent a
homeserver from querying potentially untrusted services.

This proposal suggests informing clients of this configuration through the standard
capabilities API.

## Proposal

The [GET /_matrix/client/v3/capabilities](https://spec.matrix.org/latest/client-server-api/#get_matrixclientv3capabilities)
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

If `enabled` is false, any attempt to use `GET /_matrix/client/v1/media/preview_url` MUST be rejected with
a `403` `M_FORBIDDEN` error.

Servers MAY elect to allow some users access to this endpoint, so the response may be different
depending on the authenticated user (e.g. disabled for guest users).

## Potential issues

None.

## Alternatives

None.

## Security considerations

It's just a flag indicating whether you can use an endpoint, so none.

## Unstable prefix

`io.element.msc4452.preview_url` should be used instead of `m.preview_url` while this MSC is considered
unstable.

## Dependencies

None.
