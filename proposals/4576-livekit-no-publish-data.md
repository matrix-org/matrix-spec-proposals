# MSC4576: Do not allow data publishing on LiveKit transport unless needed

[MSC4195] introduced a LiveKit-based transport for MatrixRTC. Access to the LiveKit SFU is guarded
by JWT. [MSC4195] covers the various JWT properties and related requirements or recommendations in
the ["Access token properties"] section. This listing misses the property `video.canPublishData`
which, as per the [LiveKit reference], allows participants to publish data. Note that this is different
from the `video.canPublish` property which controls the permission to publish audio and video tracks.

The only currently specified MatrixRTC application is the voice- and video conferencing application
from [MSC4196]. This application doesn't use data tracks. As a result, client implementations are
unlikely to visualise these tracks. This makes allowing data publishing, a potential resource abuse
vector.

To mitigate this, the current proposal denies data publishing if not needed.

[MSC4195]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195
["Access token properties"]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195/changes#diff-08dc4f21a474f28b0a90f392f5399d4777fe93d2e0c2d2600242f8fcf0c9af33R427
[LiveKit reference]: https://docs.livekit.io/frontends/reference/tokens-grants/#video-grant
[MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196

## Proposal

Servers SHOULD set `video.canPublishData` to `false`.

## Potential issues

Future MatrixRTC applications might require data tracks. The treatment of `video.canPublishData`
in the spec can be reconsidered if and when that happens. If needed, servers can choose to enable
`video.canPublishData` regardless.

## Alternatives

None.

## Security considerations

The RECOMMENDED disablement of data publishing follows the principle of least privilege and
aligns with how [MSC4195] already treats `video.canUpdateOwnMetadata`.

## Unstable prefix

None.

## Dependencies

None.
