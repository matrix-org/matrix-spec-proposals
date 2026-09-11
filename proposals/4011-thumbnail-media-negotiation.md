# MSC4011: Thumbnail media negotiation

It is currently up to the homeserver to decide which media formats are exposed
by the media repository for the [`/thumbnail` endpoint](https://spec.matrix.org/v1.6/client-server-api/#get_matrixmediav3thumbnailservernamemediaid).

It is a [frequent request](https://github.com/matrix-org/matrix-spec/issues/453)
to support thumbnailing into different (usually more modern) formats, but this
is not currently possible.

## Proposal

Homeservers will use the [`Accept` header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept)
header in its [content negotiation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation#server-driven_content_negotiation)
algorithm to determine what thumbnail format to serve to the client.

Homeservers *must* support providing responses for `image/png` and `image/jpeg`
for the `/thumbnail` endpoint, but do not need to actually provide every thumbnail
in both formats. (These formats are known as the "fallback formats" below.) Clients
which support thumbnails are expected to support both of these formats.

If the client & homeserver cannot successfully negotiate a format (e.g. due to no
overlap in supported formats, a missing, or invalid `Accept` header) then the
server shall use one of the "fallback formats" to serve the response.

A homeserver may choose to support additional formats, e.g. `image/webp`, and
serve them to clients which explicitly request them but *must* use the fallback
formats in other cases.

For example, if the `Accept` header includes `image/webp` then the homeserver
may choose to provide a WebP thumbnail, but if the header is `image/*` or `*/*`
then it must fallback to `image/png` or `image/jpeg`.

### Impact on bridges

???

## Potential issues

It is possible that a client is *already sending the `Accept`* header but would
be unable to cope with actually receiving different types of media. This seems
unlikely and would be up-to clients to fix.

## Alternatives

Synapse [previously had an unspecced `type` parameter](https://github.com/matrix-org/synapse/issues/14913),
which was a poor version of the `Accept` header.

Do nothing and leave this up to homeserver implementation.

A [`406 Not Acceptable`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406)
could be served as the response instead of a fallback response. This has more
potential to break current clients, however.

## Future extensions

It may make sense to also apply this to the `/download` resource. This could
allow simple clients to make a request to `/download` which is only fulfilled
for e.g. images (by requesting it with `Accept: image/*`).

## Security considerations

This depends on the media format that a homeserver or client wishes to support.

For example, homeservers and clients should be especially careful if attempting
to thumbnail SVG images due to the [Billion laughs Attack](https://en.wikipedia.org/wiki/Billion_laughs_attack).[^1]

There are not other expected security issues besides those inherent in the
thumbnailing endpoint.

## Unstable prefix

N/A as the `Accept` header is a [standardized](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept).

## Dependencies

N/A

[^1]: See [Synapse commit `bd77216 `](https://github.com/matrix-org/synapse/commit/bd77216d06518ace2ec6213aa0ac0c834e923456).
