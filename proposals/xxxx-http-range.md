# MSCXXXX: HTTP Range on content repository

## Proposal

This MSC aims to make HTTP Range capability *mandatory* on the content repository fetch endpoint.

[HTTP Range](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests) is a Header-based
method by which browsers and other clients can request a certain byte-range of a file.

Most modern browsers depend on this mechanism to scrub through video footage, and the absence would
make some media playback unable to be scrubbed through.

This would only affect CS endpoint `/_matrix/media/v3/download/{serverName}/{mediaId}`.

## Unstable prefix

This MSC would only add a well-known HTTP capability to an existing endpoint, which can easily be
ignored by existing clients, I think it's overkill to require an unstable prefix for this.