# MSC4298: Room version components for 'Redact on ban'

[MSC4293](https://github.com/matrix-org/matrix-spec-proposals/pull/4293) introduces a capability to
redact a sender's events upon being kicked or banned in the room. This functionality can operate in
existing room versions, but can be improved in a future room version to be more reliable.

This proposal covers the parts which require a room version, allowing MSC4293 to progress more quickly
through the process, protecting existing (and non-conflicting) room versions. Namely, this proposal
adjusts the redaction algorithm to protect the `redact_events` field from redaction itself.

**WIP Note**: This proposal may expand in scope as more room version-affecting functionality is
discovered/desired.

## Proposal

In a future room version, the [redaction algorithm](https://spec.matrix.org/v1.14/rooms/v11/#redactions)
is modified to retain `redact_events` on `m.room.member` events.

## Potential issues

None expected - this proposal resolves a potential issue highlighted in MSC4293.

## Alternatives

None relevant.

## Security considerations

None relevant - see potential issues section.

## Unstable prefix

While this proposal is not incorporated into a stable room version, implementations should instead
use `org.matrix.msc4298.v1` based upon [room version 11](https://spec.matrix.org/v1.14/rooms/v11/).

## Dependencies

This MSC requires [MSC4293](https://github.com/matrix-org/matrix-spec-proposals/pull/4293) to be
functional.
