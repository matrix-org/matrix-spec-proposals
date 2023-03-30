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

#### `POST /_matrix/media/v1/create`
Create a new MXC URI without content. Like `/upload`, this endpoint requires
auth and returns the `content_uri` that can be used in events.

The request body should be an empty JSON object. In the future, the body could
be used for metadata about the file, such as the mime type or access control
settings (related: [MSC701]).

The server may optionally enforce a maximum age for unused media IDs to delete
media IDs when the client doesn't start the upload in time, or when the upload
was interrupted and not resumed in time. The server should include the maximum
timestamp to complete the upload in the `unused_expires_at` field in the
response JSON. The recommended default expiration for completing the upload is 1
minute.

##### Rate Limiting

The server should rate limit requests to create media.

The server should limit the number of concurrent *pending media uploads* a given
user can have. A pending media upload is a created MXC URI that (a) is not
expired (the `unused_expires_at` timestamp has not passed) and (b) the media has
not yet been uploaded for.

In both cases, the server should respond with `M_LIMIT_EXCEEDED` optionally
providing details in the `error` field, but servers may wish to obscure the
exact limits that are used and not provide such details.

##### Example response
```json
{
  "content_uri": "mxc://example.com/AQwafuaFswefuhsfAFAgsw",
  "unused_expires_at": 1647257217083
}
```

#### `PUT /_matrix/media/v3/upload/{serverName}/{mediaId}`
Upload content to a MXC URI that was created earlier. This endpoint requires
auth. If the upload is successful, an empty JSON object and status code 200 is
returned.

If the endpoint is called with a media ID that already has content, the request
should be rejected with the error code `M_CANNOT_OVERWRITE_MEDIA` and HTTP
status code 409.

If the upload request comes from a user other than the one who created the media
ID, the request should be rejected with an `M_FORBIDDEN` error.

If the serverName/mediaId combination is not known, not local, or expired, an
`M_NOT_FOUND` error is returned.

If the MXC's `unused_expires_at` is reached before the upload completes, the
server may either respond immediately with `M_NOT_FOUND` or allow the upload to
continue.

For other errors, such as file size, file type or user quota errors, the normal
`/upload` rules apply.

#### Changes to the `/download` and `/thumbnail` endpoints
A new query parameter, `timeout_ms` is added to the endpoints that can
download media. It's an integer that specifies the maximum number of
milliseconds that the client is willing to wait to start receiving data.
The default value is 20000 (20 seconds). The content repository can and should
impose a maximum value for this parameter. The content repository can also
choose to respond before the timeout if it desires.

If the media is available immediately (for example in the case of a
non-asynchronous upload), the content repository should ignore this parameter.

If the MXC has expired, the content repository should respond with `M_NOT_FOUND`
and a HTTP 404 status code.

If the data is not available when the server chooses to respond, the content
repository returns a `M_NOT_YET_UPLOADED` error with a HTTP 504 status code.

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

The primary attack vector that must be prevented is a malicious user creating a
large number of MXC URIs and sending them to a room without uploading the
corresponding media. Clients in that room would then attempt to download the
media, holding open connections to the server and potentially exhausting the
number of available connections.

This attack vector is stopped in multiple ways:

1. Limits on `/create` prevent users from creating MXC URIs too quickly and also
   require them to finish uploading files (or let some of their MXCs expire)
   before creating new MXC URIs.

2. Servers are free to respond to `/download` and `/thumbnail` requests before
   the `timeout_ms` has been reached and respond with `M_NOT_YET_UPLOADED`. For
   example, if the server is under connection count pressure, it can choose to
   respond to waiting download connections with `M_NOT_YET_UPLOADED` to free
   connections in the pool.

3. Once the media is expired, servers can respond immediately to `/download` and
   `/thumbnail` requests with `M_NOT_FOUND`.

## Future work

Future MSCs might wish to address large file uploads. One approach would be to
add metadata to the `/create` call via a query parameter (for example
`?large_file_upload=true`. Servers would have the ability to impose restrictions
on how many such "large file" uploads a user can have concurrently. For such a
situation, the server would likely send a more generous `unused_expires_at`
timestamp to allow for a long-running upload.

## Unstable prefix
While this MSC is not in a released version of the spec, implementations should
use `fi.mau.msc2246` as a prefix and as an `unstable_features` flag in the
`/versions` endpoint.

* `POST /_matrix/media/unstable/fi.mau.msc2246/create`
* `PUT /_matrix/media/unstable/fi.mau.msc2246/upload/{serverName}/{mediaId}`
* `?fi.mau.msc2246.timeout_ms`
* `FI.MAU.MSC2246_NOT_YET_UPLOADED`
* `FI.MAU.MSC2246_CANNOT_OVERWRITE_MEDIA`

[matrix-spec#432]: https://github.com/matrix-org/matrix-spec/issues/432
[MSC701]: https://github.com/matrix-org/matrix-doc/issues/701
