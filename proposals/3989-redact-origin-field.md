# MSC3989: Redact `origin` field on events

The [current redaction algorithm](https://spec.matrix.org/v1.6/rooms/v10/#redactions) *keeps* the
top-level `origin` property on events during redaction, however, as of this writing, the only use within the 
spec of  `origin` as a top-level event property is a malformed example of event format. The field has no 
significant meaning in modern room versions.

Within the ecosystem, it's clear that we'd [prefer the field to disappear](https://github.com/matrix-org/matrix-spec/issues/374),
and have [tried to do so](https://github.com/matrix-org/matrix-spec/pull/998) in the past. The
malformed examples are even [known to us](https://github.com/matrix-org/matrix-spec/issues/1480).

What's not clear, and mentioned in [a comment](https://github.com/matrix-org/matrix-spec/issues/1480#issuecomment-1495183789),
is whether the `origin` field is *actually* used. There do not appear to be any auth rules or similar
which would use the field, however it'd hardly be the first time that the spec was wrong about an
ancient room version like v1. What is clear is that Synapse, where this question would be asked,
wants to [drop support](https://github.com/matrix-org/synapse/issues/3816) for the field and has
taken [steps](https://github.com/matrix-org/synapse/pull/8324) towards that mission by fixing bugs
in the area. In a [quick audit](https://github.com/matrix-org/matrix-spec-proposals/pull/3989#issuecomment-1497659507)
of the Synapse codebase during implementation of this MSC, the `origin` field appears unused.

Given the above context, this proposal removes the `origin` field from the [redaction algorithm](https://spec.matrix.org/v1.7/rooms/v10/#redactions) in
future room versions, leaving it as-is for existing versions (not that an MSC can change the behaviour
of an already-stable room version).

Some other fields are additionally useless in modern room versions, however they are already adapted
by [MSC2176](https://github.com/matrix-org/matrix-spec-proposals/pull/2176).

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
