# MSC2701: Media and the `Content-Type` relationship

The specification currently does not outline in great detail how `Content-Type` should be handled
with respect to media, particularly around uploads. The [`POST /upload`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixmediav3upload)
and [`PUT /upload/:serverName/:mediaId`](https://spec.matrix.org/v1.9/client-server-api/#put_matrixmediav3uploadservernamemediaid)
endpoints mention that `Content-Type` is a header that can be set, but does not list it as required,
for example. Similarly, the `Content-Type` seems to entirely disappear when talking about
[downloads](https://spec.matrix.org/v1.9/client-server-api/#get_matrixmediav3downloadservernamemediaid).

This proposal clarifies how the `Content-Type` header is used on upload and download, in line with
current best practices among server implementations.

## Proposal

For `POST` and `PUT` `/upload`, the `Content-Type` header becomes explicitly *optional*, defaulting
to `application/octet-stream`. [Synapse](https://github.com/element-hq/synapse/blob/742bae3761b7b2c638975f853ab6161527629240/synapse/rest/media/upload_resource.py#L91)
and [MMR](https://github.com/turt2live/matrix-media-repo/blob/fdb434dfd8b7ef7d93401d7b86791610fed72cb6/api/r0/upload_sync.go#L33)
both implement this behaviour. Clients SHOULD always supply a `Content-Type` header though, as this
may change in future iterations of the endpoints.

**Note**: Synapse's behaviour was changed in October 2021 with [PR #11200](https://github.com/matrix-org/synapse/pull/11200).
Previously, Synapse required the header.

For `GET /download`, the server MUST return a `Content-Type` which is either exactly the same as the
original upload, or reasonably close. The bounds of "reasonable" are:

* Adding a `charset` to `text/*` content types.
* Detecting HTML and using `text/html` instead of `text/plain`.
* Using `application/octet-stream` when the server determines the content type is obviously wrong. For
  example, an encrypted file being claimed as `image/png`.
* Returning `application/octet-stream` when the media has an unknown/unprovided `Content-Type`. For
  example, being uploaded before the server tracked content types or when the remote server is non-compliantly
  omitting the header entirely.

Actions not in the spirit of the above are not considered "reasonable". Existing server implementations
are encouraged to downgrade their behaviour to be in line with this guidance. [Synapse](https://github.com/element-hq/synapse/blob/742bae3761b7b2c638975f853ab6161527629240/synapse/media/_base.py#L154)
already does very minimal post-processing while [MMR](https://github.com/turt2live/matrix-media-repo/blob/fdb434dfd8b7ef7d93401d7b86791610fed72cb6/api/_routers/98-use-rcontext.go#L110-L139)
actively ignores the uploaded `Content-Type` (the incorrect thing to do under this MSC).

## Potential issues

Some media may have already been uploaded to a server without a content type. Such media items are
returned as `application/octet-stream` under this proposal.

## Alternatives

No significant alternatives.

## Security considerations

No relevant security considerations, though server authors are encouraged to consider the impact of
[MSC2702](https://github.com/matrix-org/matrix-spec-proposals/pull/2702) in their threat model.

## Unstable prefix

This MSC is backwards compatible with existing specification and requires no particular unstable
prefix. Servers are already able to implement this proposal's behaviour legally.

Additionally, cited in the proposal are examples of the behaviour being used in production today.
