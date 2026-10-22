# MSC4531: Deprecate legacy VoIP

[MSC4196] introduces a voice and video calling application based on MatrixRTC ([MSC4143]). This
obviates the [legacy VoIP] system as it provides more robust call setup and better scaling.
Additionally, it is built on a generic system and allows for more future flexibility (such as the
introduction of different RTC transports).

This proposal therefore seeks to deprecate [legacy VoIP] to discourage implementations from putting
effort into integrating or supporting it in future while a better system is available.

## Proposal

The [legacy VoIP] feature is deprecated in (but not yet removed from) the spec.

## Potential issues

None.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.

  [MSC4196]: https://github.com/matrix-org/matrix-spec-proposals/pull/4196
  [MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
  [legacy VoIP]: https://spec.matrix.org/v1.18/client-server-api/#voice-over-ip
