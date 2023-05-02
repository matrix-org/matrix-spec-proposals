# MSC3860: Media Download Redirects

Currently the media download endpoints must return either a 200 with content or error responses. This
means the media server instance must stream the data from wherever it is stored, which is likely not
local to itself. Allowing redirects on these endpoints would  make it possible for the media repo to
tell clients/servers to pull data direct from the source, e.g. a CDN.

## Proposal

This MSC proposes that a 307 or 308 redirect code is allowed and followed according to the `Location`
header. It is possible some clients would already follow these which needs to be confirmed. Specific
endpoints in question:

+ `/_matrix/media/v3/download/{serverName}/{mediaId}`
+ `/_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}`
+ `/_matrix/media/v3/thumbnail/{serverName}/{mediaId}`

To prevent breaking clients that don't properly follow the redirect response this functionality will
be enabled by a query string flag `allow_redirect=true`. So specifically in the above cases if a
client respects redirect responses it can make requests like so to the media endpoints:

+ `/_matrix/media/v3/download/{serverName}/{mediaId}?allow_redirect=true`
+ `/_matrix/media/v3/download/{serverName}/{mediaId}/{fileName}?allow_redirect=true`
+ `/_matrix/media/v3/thumbnail/{serverName}/{mediaId}?allow_redirect=true`

In the case where a client wishes not to redirect (either implictly with no parameter or explicitly
providing `allow_redirect=false`) the server must continue to serve media directly with no redirect.

## Potential Issues

None, as opt-in functionality this change is 100% backwards compatible.

## Alternatives

None at this time.

## Security Considerations

A media repo could redirect requests to a bad actor, although this would make the primary media
repo itself a bad actor, thus this does not present any increased security issues.

## Unstable Prefix

Until this functionality has landed in the spec, the `allow_redirect` query
parameter should be prefixed with `com.beeper.msc3860.`:

```
?com.beeper.msc3860.allow_redirect=true
```
