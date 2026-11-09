# MSC4576: Only allow data publishing when also allowing audio/video publishing on LiveKit transports

[MSC4195] introduced a LiveKit-based transport for MatrixRTC. Access to the LiveKit SFU is guarded
by JWTs. [MSC4195] covers the various JWT properties and related requirements or recommendations in
the ["Access token properties"] section. This listing misses the property `video.canPublishData`
which, as per the [LiveKit reference], allows participants to publish data. Note that this is different
from the `video.canPublish` property which only controls the permission to publish audio and video tracks.

The voice- and video conferencing application from [MSC4196], which is the only currently specified
MatrixRTC application, doesn't use data tracks. However, future features such as [MSC4577] and
applications like [Neoboard] depend on data publishing. Therefore, the present proposal ties
the value of `video.canPublishData` to the value of `video.canPublish`.

[MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195
["Access token properties"]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195/changes#diff-08dc4f21a474f28b0a90f392f5399d4777fe93d2e0c2d2600242f8fcf0c9af33R427
[LiveKit reference]: https://docs.livekit.io/frontends/reference/tokens-grants/#video-grant
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196
[MSC4577]: https://github.com/matrix-org/matrix-spec-proposals/pull/4577
[Neoboard]: https://github.com/nordeck/matrix-neoboard

## Proposal

Servers MUST set `video.canPublishData` to the same value as `video.canPublish`.

For reference, the value of `video.canPublish` as per [MSC4195] is:

> - `video.canPublish`: MUST be true when the requesting user belongs to the home server creating
>   the token to allow local users to publish RTC data. SHOULD also be true if the requesting user is
>   from a different server but servers MAY decide to restrict publishing rights.

## Potential issues

None.

## Alternatives

None.

## Security considerations

Some MatrixRTC applications, such as the voice- and video conferencing application from [MSC4196],
may not use data tracks. As a result, client implementations for these applications are unlikely to
visualise data tracks if they occur unexpectedly. This makes allowing data publishing, a potential
resource abuse vector as malicious users could use data tracks unnoticed by other users.

However, malicious clients can already abuse audio and video tracks to exchange general data
and might do so in their own sessions. Servers can try to mitigate resource abuse by applying
rate limiting or enforcing SFU usage limits.

## Unstable prefix

None.

## Dependencies

None.
