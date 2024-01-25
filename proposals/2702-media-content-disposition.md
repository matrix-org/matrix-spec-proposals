# MSC2702: `Content-Disposition` usage in the media repo

The current specification does not clarify how to treat `Content-Disposition` on responses to
[`/download`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixmediav3downloadservernamemediaid)
and [`/thumbnail`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)
requests. This has led to clients (and most notably, IRC bridges) relying on implementation-specific
behaviour for how their uploads will be represented. This reliance has caused issues in the past where
a security decision was made to use an `attachment` disposition on the download endpoint, however this
caused an IRC bridge's use of the media repo to break when trying to send large messages: users on the
IRC side were forced to download and open a text file instead of seeing it in their browser. Similar
problems have occurred in the past with respect to clients using the download endpoint as an "open in
browser" button.

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

* `Content-Disposition` MUST be returned, and MUST be one of `inline` or `attachment`.

  * `inline` *should* be used when one of the "safe" content types listed below is being served.

* When uploads are made with a `filename`, the `Content-Disposition` header MUST contain the same
  `filename`. Otherwise, `filename` is excluded from the header.

  * If the media being downloaded is remote, the remote server's `filename` in the `Content-Disposition`
    header is used as the `filename` instead. When the header is not supplied, or does not supply a
    `filename`, the local download response does not include a `filename` (though does still contain
    a generated `Content-Disposition`).

For `/thumbnail`:

* `Content-Disposition` MUST be returned, and MUST be `inline` (see below).
* `Content-Disposition` SHOULD include a server-generated `filename`. For example, `thumbnail.png`.

Note that in both endpoints `Content-Disposition` becomes required, though the legal set of parameters is
intentionally different. Specifically, because `/thumbnail` returns server-generated content, that content
is safe to serve inline relative to a given user upload and therefore can be inline. It is however atypical
for a client to link to `/thumbnail` directly, but in the event they do we provide a safe default.

The following content types are considered "safe" for `inline` usage. For `/download`, servers SHOULD
use `attachment` if the returned `Content-Type` is not on the list. For `/thumbnail`, servers SHOULD
only generate thumbnails with a `Content-Type` listed below.

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

`Content-Type` additionally becomes a required header on responses to both `/download` and `/thumbnail`, as `Content-Disposition`
without `Content-Type` is effectively useless in HTTP. The `Content-Type` header is the `Content-Type` supplied by
the client during `/upload`. If no `Content-Type` was supplied during upload, `application/octet-stream` is used.

Clients SHOULD NOT rely on servers returning `inline` rather than `attachment` on `/download`. Server
implementations might decide out of an abundance of caution that all downloads are responded to with
`attachment`, regardless of content type - clients should not be surprised by this behaviour.

## Potential issues

This proposal does not require the usage of `inline` on `/download`, making it harder for IRC and similar
bridges to rely on "pastebin" behaviour. For example, when a large message is posted on the Matrix side of
the bridge, the IRC bridge might upload it as a text file due to limits on the IRC side. Ideally, that text
file would be rendered inline by the server. Bridges are encouraged to use "proxy APIs" to serve the text
file instead, where they can better control the user experience.

## Alternatives

No major alternatives identified.

## Security considerations

This MSC fixes a theoretical Cross-Site Scripting issue where a browser improperly handling Content
Security Policy headers or sandboxes *may* reveal sensitive information about the user, if the user's
client is hosted at the same domain as the media download URL. This is mitigated by only suggesting
`inline` as a disposition on content types which are not likely to execute code within the browser
upon being viewed. A browser may still have further bugs which reveal information, though those issues
quickly become impractical for the Matrix specification to mitigate.

No new security issues are identified, and careful consideration was put into `inline` to ensure an
extremely limited set of possible media types.

The allowable content types for `inline` were inspired by [the react-sdk](https://github.com/matrix-org/matrix-react-sdk/blob/a70fcfd0bcf7f8c85986da18001ea11597989a7c/src/utils/blobs.ts#L51),
and extended to include what is present in [a related Synapse PR](https://github.com/matrix-org/synapse/pull/15988).
The react-sdk list of types has been known to be safe for several years now, and the added types in the Synapse
PR are not subject to XSS or similar attacks. Note that `image/svg`, `text/javascript`, and `text/html` are
explicitly not allowed.

## Unstable prefix

This MSC has no particular unstable prefix requirements. Servers are already able to return arbitrary
`Content-Disposition` headers on the affected endpoints.
