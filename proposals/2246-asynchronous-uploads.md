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
transfers, as requested in [matrix-spec#432].

### Content repository behavior
The proposal adds two new endpoints to the content repository API and modifies
the download and thumbnail endpoints.

#### `POST /_matrix/media/v3/create`
Create a new MXC URI without content. Like `/upload`, this endpoint requires
auth and returns the `content_uri` that can be used in events.

The request body should be an empty JSON object. In the future, the body could
be used for metadata about the file, such as the mime type or access control
settings (related: [MSC701]).

The server may optionally enforce a maximum age for unused media IDs to delete
media IDs when the client doesn't start the upload in time, or when the upload
was interrupted and not resumed in time. The server should include the maximum
timestamp to start the upload in the `unused_expires_at` field in the response
JSON. The recommended default expiration for starting the upload is 1 minute.

The server should also rate limit requests to create media. When combined with
the maximum age for created media IDs, it effectively prevents spam by creating
lots of unused ids.

##### Example response
```json
{
  "content_uri": "mxc://example.com/AQwafuaFswefuhsfAFAgsw",
  "unused_expires_at": 1647257217083
}
```

#### `PUT /_matrix/media/v3/upload/{serverName}/{mediaId}`
Upload content to a MXC URI that was created earlier. If the endpoint is called
with a media ID that already has content, the request should be rejected with
the error code `M_CANNOT_OVERWRITE_MEDIA` and HTTP status code 409. The endpoint
should also reject upload requests from users other than the user who created
the media ID. This endpoint requires auth.

If the upload is successful, an empty JSON object and status code 200 is
returned. If the serverName/mediaId combination is not known or not local, an
`M_NOT_FOUND` error is returned. For other errors, such as file size, file type
or user quota errors, the normal `/upload` rules apply.

The client should include a `Content-Length` header to ensure the server knows
if the file was uploaded entirely. If the server receives a different amount of
data than specified in the header, the upload must fail.

#### Changes to the `/download` and `/thumbnail` endpoints
A new query parameter, `max_stall_ms` is added to the endpoints that can
download media. It's an integer that specifies the maximum number of
milliseconds that the client is willing to wait to start receiving data.
The default value is 20000 (20 seconds).

If the data is not available before the specified time is up, the content
repository returns a `M_NOT_YET_UPLOADED` error with a HTTP 404 status code.
The error may include an additional `retry_after_ms` field to suggest when the
client should try again.

For the `/download` endpoint, the server could also stream data directly as it
is being uploaded. However, streaming creates several implementation and spec
complications (e.g. how to stream if the media repo has multiple workers, what
to do if the upload is interrupted), so specifying exactly how streaming works
is left for another MSC.

## Potential issues
Other clients may time out the download if the sender takes too long to upload
media.

## Alternatives

## Security considerations

## Unstable prefix
While this MSC is not in a released version of the spec, implementations should
use `fi.mau.msc2246` as a prefix and as an `unstable_features` flag in the
`/versions` endpoint.

* `POST /_matrix/media/unstable/fi.mau.msc2246/create`
* `PUT /_matrix/media/unstable/fi.mau.msc2246/upload/{serverName}/{mediaId}`
* `?fi.mau.msc2246.max_stall_ms`
* `FI.MAU.MSC2246_NOT_YET_UPLOADED`
* `FI.MAU.MSC2246_CANNOT_OVERWRITE_MEDIA`

[matrix-spec#432]: https://github.com/matrix-org/matrix-spec/issues/432
[MSC701]: https://github.com/matrix-org/matrix-doc/issues/701
