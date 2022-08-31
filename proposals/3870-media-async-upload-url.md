# MSC3870: Async media upload extension: upload to URL

This MSC proposes an extension to [MSC2246](https://github.com/matrix-org/matrix-spec-proposals/pull/2246)
(async media uploads) that allows a media server to give clients a URL to use for uploading media
data after the MXID is created.

The rationale behind this is to enable clients to upload direct to the backing datastore, for example
by using [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
and/or [S3 transfer acceleration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/transfer-acceleration-getting-started.html)
(this is not limited to S3, just well documented by AWS). By enabling clients to upload to a different
URL server owners could improve upload performance significantly by using a CDN with closer Points
of Presence to their users than the homeserver itself.

When combined with [MSC3860](https://github.com/matrix-org/matrix-spec-proposals/pull/3860) (media
download redirect URLs) this makes it possible to run a "lean" media server that orchestrates where
media is uploaded to and downloaded from but does not directly handle much media itself. Note this 
doesn't include thubmnails or URL previews which would still go through the media server.


## Proposal

The proposal modifies the MSC2246 create endpoint to optionally include a URL that a compatible
client may use to upload the content for the created MXID. This is considered optional and the
client may continue to upload via the new upload endpoint defined in MSC2246.

`POST /_matrix/media/v3/create`

**Example response**

```json
{
  "content_uri": "mxc://example.com/AQwafuaFswefuhsfAFAgsw",
  "unused_expires_at": 1647257217083,
  "upload_url": "https://cdn.example.com/media-repo/upload/XAPw4CtrzArk?signed=h4tGOHvCu"
}
```

If the client chooses to upload media via the `upload_url` field, the media server must implement
it's own methods of detecting when an upload is complete if desired (eg. thumbnailing or spam
detection).

**Alternative**: a new endpoint that clients `POST` to after uploading media to the `upload_url`
used to notify the media server. However in the case of spam detection this makes it possible for
bad acting clients to bypass spam detection for media uploads. This means any server side only
detection is necessary anyway making the client endpoint redundant.


## Alternatives

### Run the whole homeserver behind CDN

Server owners could run their own Points of Presence to receive and handle media content and pass
through any non-media requests to a central homeserver (or run a distributed homeserver if/when
that exists). There is a significant cost (management time & infrastructure) associated with this.


## Security Considerations

Security of presigned URL uploads is well documented but important to be aware of when implementing
support for this.


## Unstable Prefix

While this MSC is not in a released version of the spec, implementations should use `com.beeper.msc3880`
as a prefix and as an unstable_features flag in the /versions endpoint.

```
 POST /_matrix/media/unstable/com.beeper.msc3870/upload/{serverName}/{mediaId}/complete
```
