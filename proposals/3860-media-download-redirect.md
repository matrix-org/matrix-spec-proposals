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
