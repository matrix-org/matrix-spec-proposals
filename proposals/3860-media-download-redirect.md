# MSC3860: Media Download Redirects

Currently the media download endpoints must return either a 200 with content or error responses. This
means the media server instance must stream the data from wherever it is stored, which is likely not
local to itself. Allowing redirects on these endpoints would  make it possible for the media repo to
tell clients/servers to pull data direct from the source, eg. a CDN.

## Proposal

This MSC simply proposes that a 307 redirect code is allowed and followed according to the `Location`
header. It is possible some clients would already follow these which needs to be confirmed. Specifc
endpoints in question:

+ `/_matrix/media/v3/download/{serverName}/{mediaId}`
+ `/_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`
+ `/_matrix/media/v3/thumbnail/{serverName}/{mediaId}`

The media repo already conforms to standard HTTP practices so this may already work as expected. The
MSC is proposing to add redirects to the list of possible HTTP responses for the above endpoints in
the Matrix Specifiction. Implementation would be confirming that this works in all the major clients.

## Potential Issues

There may be clients that don't follow redirect responses properly, in which case they would fail
to retrieve the media. One possible workaround for this is utilising an opt-in query string parameter
to allow redirects, e.g `?allow-redirect=true`.

## Alternatives

None at this time.

## Security Considerations

A media repo could redirect requests to a bad actor, although this would make the primary media
repo itself a bad actor, this does present any increased security issues.

## Unstable Prefix

No need for an unstable prefix for redirects as it stands. If a query string was to be used to
enable this functionality this could use the following unstable prefix:

```
?com.beeper.msc3860.allow-redirects=true
```
