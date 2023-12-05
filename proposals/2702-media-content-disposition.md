# MSC2702: `Content-Disposition` usage in the media repo

The current specification does not clarify how to treat `Content-Disposition` on
[`/download`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixmediav3downloadservernamemediaid)
and [`/thumbnail`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)
requests. Some clients expect attachments to be `download` only (or don't care), while other applications
like bridges rely on it sometimes being `inline` for user experience reasons.

This proposal clarifies the exact behaviour and introduces a set of suggestions for servers to follow
with respect to `Content-Disposition`.

## Context

Headers:
* [`Content-Disposition`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition)

Endpoints affected:

* [`/download`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixmediav3downloadservernamemediaid)
* [`/thumbnail`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)

Upload endpoints:
* [`POST /upload`](https://spec.matrix.org/v1.8/client-server-api/#post_matrixmediav3upload)
* [`PUT /upload`](https://spec.matrix.org/v1.8/client-server-api/#put_matrixmediav3uploadservernamemediaid)

## Proposal

For `/download`:

* `Content-Disposition` MUST be returned, and MUST be one of `inline` or `attachment` (see below).
* `Content-Disposition` MUST include the `filename` from the originating `/upload` endpoint. If the media
  being downloaded is remote, the `filename` from the remote server's `Content-Disposition` header MUST
  be used.

  * For backwards compatibility reasons, clients cannot assume that a `filename` will be present.

For `/thumbnail`:

* `Content-Disposition` MUST be returned, and MUST be `inline` (see below).
* `Content-Disposition` SHOULD include a server-generated `filename`. For example, `thumbnail.png`.

Note that in both endpoints `Content-Disposition` becomes required, though the legal set of parameters is
intentionally different. Specifically, because `/thumbnail` returns server-generated content, that content
is safe to serve inline relative to a given user upload and therefore can be inline. It is however atypical
for a client to link to `/thumbnail` directly, but in the event they do we provide a safe default.

When `Content-Disposition` is `inline`, the `Content-Type` SHOULD be one of the following mimetypes:

* `text/css`
* `text/plain`
* `text/csv`
* `application/json`
* `application/ld+json`
* `image/jpeg`
* `image/gif`
* `image/png`
* `image/apng`
* `image/webp`
* `image/avif`
* `video/mp4`
* `video/webm`
* `video/ogg`
* `video/quicktime`
* `audio/mp4`
* `audio/webm`
* `audio/aac`
* `audio/mpeg`
* `audio/ogg`
* `audio/wave`
* `audio/wav`
* `audio/x-wav`
* `audio/x-pn-wav`
* `audio/flac`
* `audio/x-flac`

If the content to be returned does *not* match these types, it SHOULD be returned as `attachment` (or in the
case of `/thumbnail`, not returned at all).

`Content-Type` additionally becomes a required header on both `/download` and `/thumbnail`, as `Content-Disposition`
without `Content-Type` is effectively useless in HTTP. The `Content-Type` header is the `Content-Type` supplied by
the client during `/upload`.

For clarity, a server is *not* required to use `inline` on `/download`. Clients SHOULD assume that a server will
always use `attachment` instead.

## Potential issues

This proposal does not require the usage of `inline` on `/download`, making it harder for IRC and similar
bridges to rely on "pastebin" behaviour. For example, when a large message is posted on the Matrix side of
the bridge, the IRC bridge might upload it as a text file due to limits on the IRC side. Ideally, that text
file would be rendered inline by the server. Bridges are encouraged to use "proxy APIs" to serve the text
file instead, where they can better control the user experience.

## Alternatives

No major alternatives identified.

## Security considerations

This MSC fixes theoretical security issues relating to Cross-Site Scripting and similar. No new security issues
are identified, and careful consideration was put into `inline` to ensure an extremely limited set of possible
media types.

The allowable content types for `inline` were inspired by [the react-sdk](https://github.com/matrix-org/matrix-react-sdk/blob/a70fcfd0bcf7f8c85986da18001ea11597989a7c/src/utils/blobs.ts#L51),
and extended to include what is present in [a related Synapse PR](https://github.com/matrix-org/synapse/pull/15988).
The react-sdk list of types has been known to be safe for several years now, and the added types in the Synapse
PR are not subject to XSS or similar attacks. Note that `image/svg`, `text/javascript`, and `text/html` are
explicitly not allowed.

## Unstable prefix

This MSC has no particular unstable prefix requirements. Servers are already able to return arbitrary
`Content-Disposition` headers on the affected endpoints.
