# MSC4167: Copy bans on room upgrade

When a [room upgrade](https://spec.matrix.org/v1.11/client-server-api/#room-upgrades) is performed,
many state events are copied over to the new room, to minimize the amount of work the user has to do
after the upgrade. However, the spec currently states that "Membership events should not be transferred
to the new room due to technical limitations of servers not being able to impersonate people from other
homeservers". While this is most notably true for `join` membership events, this is not true for `ban`
membership, which users likely want copied over to the new room.

This behavior [has been part of Synapse](https://github.com/matrix-org/synapse/pull/4642) since only a
few months after [support for room upgrades was added](https://github.com/matrix-org/synapse/pull/4091),
with Dendrite doing this
[ever since they had support for room upgrades](https://github.com/matrix-org/dendrite/pull/2307).

## Proposal

When a room upgrade is performed, servers SHOULD copy membership states with the `ban` `membership` to
the new room, to ensure that users banned in the old room are still banned in the new room.

## Potential issues

In rooms with many banned users, it may take a while to perform the upgrade, as all the bans will need
to be performed. However, not doing this would allow previously banned users to access the room, which
is why this is deemed as worth it.

## Alternatives

None considered.

## Security considerations

None considered.

## Unstable prefix

None required, as no new fields or endpoints are being proposed.

## Dependencies

None.
