# MSC3989: Redact `origin` field on events

The [current redaction algorithm](https://spec.matrix.org/v1.6/rooms/v10/#redactions) *keeps* the
top-level `origin` field on events during redaction, however the only use of it as of writing is
a malformed example of event format. The field has no significant meaning in modern room versions.

Note: some other fields are additionally useless in modern room versions, however they are already
adapted by [MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176).

This proposal's scope includes *removing* other fields which are useless in modern room versions,
however makes no effort or consideration for *adding* protected fields to the redaction algorithm.
Given MSC2176, the only useless field appears to be `origin`, however the author kindly asks that
reviewers point out other examples as they arise.

## Proposal

In a future room version, the `origin` field is *removed* from the list of *event* keys which are
kept during redaction. Note that this requires a new room version because changing the redaction
algorithm changes how [event IDs](https://spec.matrix.org/v1.6/rooms/v10/#event-ids) are calculated,
as they are [reference hashes](https://spec.matrix.org/v1.6/server-server-api/#calculating-the-reference-hash-for-an-event)
which redact the event during calculation.

## Potential issues

No major concerns.

## Alternatives

No significant alternatives.

## Security considerations

No major concerns.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3989` as the room
version identifier, using v10 as a base.

## Dependencies

No blocking dependencies.

This MSC would partner well with the following MSCs, however:
* [MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176)
* [MSC2175](https://github.com/matrix-org/matrix-spec-proposals/pull/2175)
* [MSC2174](https://github.com/matrix-org/matrix-spec-proposals/pull/2174)
* [MSC3821](https://github.com/matrix-org/matrix-spec-proposals/pull/3821)
