# Asynchronous media uploads
Sending media to Matrix currently requires that clients first upload the media
to the content repository and then send the event. This is a problem for some
use cases, such as bridges that want to preserve message order, as reuploading
a large file would block all messages.

## Proposal
This proposal proposes a way to send the event containing media before actually
uploading the media, which would make the aformentioned bridge message order
preservation possible without blocking all other messages behind a long upload.

In the future, this new functionality could be used for streaming file
transfers, as requested in [#1885].

### Content repository behavior
The proposal adds two new endpoints to the content repository API and modifies
the behavior of the download endpoint.

#### `POST /_matrix/media/r0/create`
Create a new MXC URI without content. Like `/upload`, this endpoint returns the
`content_uri` that can be used in events. Additionally, the response would
contain a `media_id` field with the media ID part of the MXC URI for
convenience (see [MXC format] in the spec).

This endpoint could have a JSON body that contains metadata, such as the mime
type of the media that's going to be uploaded. In the future, the body could
also contain access control settings (related: [MSC701]).

TODO: decide if body is needed already and if yes, spec body schema

#### `PUT /_matrix/media/r0/upload/{mediaId}`
Upload content to a MXC URI that was created earlier. If the endpoint is called
with a media ID that already has content, the request should be rejected with
the error code `M_CANNOT_OVERRIDE_MEDIA`.

#### Behavior change in `/download`
When another client tries to download media that has not yet been uploaded, the
content repository should stall the request until it is uploaded. Optionally,
content repository implementations may send the data that has already been
uploaded and stream data as it comes in from the sender.

## Tradeoffs

## Potential issues
Other clients may time out the download if the sender takes too long to upload
media.

## Security considerations
There may be DoS risks in creating lots of media IDs. Especially if those media
IDs are then sent to rooms, but not given any content, the proposed stalling
method could cause a lot of open HTTP connections.

[#1885]: https://github.com/matrix-org/matrix-doc/issues/1885
[MXC format]: https://matrix.org/docs/spec/client_server/latest#matrix-content-mxc-uris
[MSC701]: https://github.com/matrix-org/matrix-doc/issues/701
