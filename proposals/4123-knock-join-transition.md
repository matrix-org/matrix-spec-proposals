# MSC4123: Allow `knock` -> `join` transition

## Introduction

[MSC2403](https://github.com/matrix-org/matrix-spec-proposals/pull/2403) added knocking functionality to
rooms, with which came the membership state `knock`.
At the time, `knock` -> `join` was not deemed as a valid transition, as for a user to join a room where you
must knock, the knock must be accepted via an invite. (Although in cases where join rules were changed to
be `public`, that would also be a sensible transition, but that is more of an edge case than the following)

Later in [MSC3083](https://github.com/matrix-org/matrix-spec-proposals/pull/3083), restricted rooms were
added as a way of joining rooms only when a given condition is met, most notabily when a user is a
member of a given room.

Finally, [MSC3787](https://github.com/matrix-org/matrix-spec-proposals/pull/3787) added the functionality
to use both restricted join rules as well as knocking in a room simutainiously.
However in this MSC the transition `knock` -> `join` was not added, even though it is very much a sensible
transition with knock restricted rooms.
For example, a user could initially knock on a room to join, but then later join a room required by the
restricted join rule that could allow them to join directly without the knock being accepted.
Currently, this would require the user to retract their knock, and then join, making the following transition:
`knock` -> `leave` -> `join`.

## Proposal

In a new room version, we make `knock` -> `join` a valid transition, as it would make situations like the above
easier to handle, as an unnecessary `knock` -> `leave` transition would no longer need to be sent.

When it comes to authorizing a `knock` -> `join` transition, the same logic can be used as a `leave` -> `join`
transition, as the same could be achived with a `knock` -> `leave` -> `join` transition.

## Potential issues

Authorization would become *slightly* more complex, as developers would have to check against the room
version to see if `knock` -> `join` is a valid transition, but it is a very minor change which would have
the upside of not making redundant transitions, so it is worth it.

## Alternatives

Keep using the `knock` -> `leave` -> `join` transition instead, but the reasons this is undesireable
are stated above.

## Security considerations

This MSC does not introduce anything that couldn't be done before (be it in a more complex and unintuitive way),
so this should not have any security considerations.

## Unstable prefix

Implementations of this MSC should use `org.matrix.msc4123` for the room version, using room version 11 for all other
behaviours of the room.

## Dependencies

None
