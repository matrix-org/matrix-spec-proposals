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
Create a new MXC URI without content. Like `/upload`, this endpoint requires
auth and returns the `content_uri` that can be used in events.

This endpoint could have a JSON body that contains metadata, such as the mime
type of the media that's going to be uploaded. In the future, the body could
also contain access control settings (related: [MSC701]).

To prevent spam, servers should limit calls to this endpoint if the user has
created many media IDs without uploading any content to them. The error code
for such a spam limit is `M_TOO_MANY_IDS_ASSIGNED`. Servers should also provide
configuration options to let high-traffic clients like application services
bypass these limits. The `rate_limited` flag in the appservice registration is
one potential way to do this.

##### Example request
TODO: decide if body is needed already and if yes, spec body schema

##### Example response
```json
{
  "content_uri": "mxc://example.com/AQwafuaFswefuhsfAFAgsw"
}
```

#### `PUT /_matrix/media/r0/upload/{serverName}/{mediaId}`
Upload content to a MXC URI that was created earlier. If the endpoint is called
with a media ID that already has content, the request should be rejected with
the error code `M_CANNOT_OVERWRITE_MEDIA`. This endpoint too requires auth.

If the upload is successful, an empty JSON object and status code 200 is
returned. If the serverName/mediaId combination is not known or not local, an
`M_NOT_FOUND` error is returned. For other errors, such as file size, file type
or user quota errors, the normal `/upload` rules apply.

#### Behavior change in `/download`
When another client tries to download media that has not yet been uploaded, the
content repository should stall the request until it is uploaded. Optionally,
content repository implementations may send the data that has already been
uploaded and stream data as it comes in from the sender.

TODO: this should have at least an option to not stall if there's no data yet

## Tradeoffs

## Potential issues
Other clients may time out the download if the sender takes too long to upload
media.

## Security considerations


[#1885]: https://github.com/matrix-org/matrix-doc/issues/1885
[MSC701]: https://github.com/matrix-org/matrix-doc/issues/701
