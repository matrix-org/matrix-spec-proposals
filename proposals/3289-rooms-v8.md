# MSC3289: Room Version 8

A new room version, `8`, is proposed using [room version 7](https://spec.matrix.org/unstable/rooms/v7/)
as a base and incorporating the following MSCs:

* [MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083) - Restricting room
  membership based on membership in other rooms

Though other MSCs are capable of being included in this version, they do not have
sufficient implementation to be considered for this room version. A future room
version may include them.

Room version `8` upon being added to the specification shall be considered stable.
No other room versions are affected by this MSC. Before room version `8` can enter
the specification, MSC3083 needs to complete its final comment period.

## Updated redaction rules

Room version 8 shall update the redaction rules for the `m.room.join_rules` event.
[Room version 1](https://spec.matrix.org/unstable/rooms/v1/#redactions) defines
that only the `join_rule` key in the content object should be kept. Room version
8 defines that both the `join_rule` and `allow` keys of the content shall be kept.
