# MSC2998: Room Version 7

A new room version, `7`, is proposed using [room version 6](https://matrix.org/docs/spec/rooms/v6.html) as a base
and incorporating the following MSCs:

* [MSC2403](https://github.com/matrix-org/matrix-doc/pull/2403) - Add "knock" feature.

Though other MSCs are capable of being included in this version, they do not have sufficient implementation to be
considered for v7 rooms. A future room version may still include them.

Room version 7 upon being added to the specification shall be considered stable. No other room versions are affected
by this MSC. Before v7 can enter the specification, MSC2403 needs sufficient review to be eligible to enter the spec
itself. This MSC is reserving the room version for use in broader testing of MSC2403 - this does not make MSC2403
stable for use in most implementations.

## A note on spec process

The spec core team has accepted "knocking" as a concept, and is generally aligned on the ideas proposed by MSC2403. As
such, we're going ahead with reserving a room version number early for some broader testing given MSC2403 is near to the
point of being stable itself. Typically the team would declare a room version number once all the included MSCs are
eligible for becoming stable, however in this case it's ideal to push ahead and reserve the version number.

If MSC2403 were to be replaced or otherwise be rejected for some reason, we'd ultimately have a gap in room versions
which might look weird but does not necessarily have an impact on the specification: room versions have no associative
ordering, so skipping a perceived sequential version is valid. The sequential versioning is a human ideal, not one of
the spec.
