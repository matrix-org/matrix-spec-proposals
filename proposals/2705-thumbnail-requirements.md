# MSC2705: Animated thumbnails

Users may already upload animated media to the media repository, such as gifs, webp images, and videos.
When this media is used in an event or avatar, many clients are stuck with a static thumbnail until
the user clicks on it to get the full, unedited, file. Some clients however would prefer to show an
animated thumbnail in certain conditions, like when the user is hovering over the message or avatar.

This proposal introduces a new query parameter to the [`GET /_matrix/media/v3/thumbnail`](https://spec.matrix.org/v1.9/client-server-api/#get_matrixmediav3thumbnailservernamemediaid)
endpoint, allowing clients to specifically request an animated thumbnail.

## Proposal

A new query parameter, `animated`, is added to the `/thumbnail` endpoint. It has the following behaviour:

* When `true`: the server SHOULD return an animated thumbnail if possible/supported.
* When `false`: the server MUST NOT return an animated thumbnail.
* When not provided: the server SHOULD NOT return an animated thumbnail.

The default case is a relaxed version of the `false` behaviour to allow server owners to customize the
default behaviour when their users' clients do not support requesting animated thumbnails.

Clients SHOULD respect a user's preference to [reduce motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
and request non-animated thumbnails in these cases.

The content types which are able to be animated is left as an implementation detail. The following
SHOULD be supported at a minimum, however:

* `image/gif`
* `image/png` ("APNG" format)
* `image/webp`

The returned content type for an animated thumbnail is additionally left as an implementation detail,
though servers SHOULD use `image/webp` whenever possible.

When media cannot be animated, such as a PDF or JPEG, the server should return a thumbnail as though
`animated` was `false`.

## Alternatives

No significant alternatives.

## Security considerations

Server load could increase when the server tries to thumbnail a large file. Servers are expected to
mitigate this on their own by providing an option to disable the feature or limiting how/when
they will animate the media.

## Unstable prefix

While this proposal is not considered stable, `animated` is specified as `org.matrix.msc2705.animated`
on requests. No unstable endpoints are required due to backwards compatibility being built-in to the
proposal.
