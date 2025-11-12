# MSC4168: Update `m.space.*` state on room upgrade

When a [room upgrade](https://spec.matrix.org/v1.11/client-server-api/#room-upgrades) is performed,
many state events are copied over to the new room, to minimize the amount of work the user has to do
after the upgrade. However, the spec doesn't currently recommend that `m.space.child` or `m.space.parent`
be copied over, as well as these events being updated in other rooms.

## Proposal

When a room upgrade is performed, servers SHOULD replicate `m.space.child` and `m.space.parent` state
in the new room.

In addition, `m.space.child` and `m.space.parent` events in other rooms, where the caller of `/upgrade`
has the permission to do so, servers SHOULD send a new state event for the old room, removing the `via` field
from it, and send a new event of the same type, with `state_key` being the new room ID, and `via` just
being the server of the sender user. Like when these events are copied into the upgraded room, the `sender`
should be set to the user calling the endpoint.

## Potential issues

This proposal does not attempt to update `m.space.*` state in rooms where the user upgrading the room
is not able to update them, as this not only likely requires something like
[MSC4049](https://github.com/matrix-org/matrix-spec-proposals/pull/4049), but also adds other additional
complications (e.g. which server should update the state?).

Users may also not want to update events in other rooms. Hopefully this proposal can be used to determine
if there is a use-case for not updating events in other rooms. If there is one, then a query parameter can
be added to toggle this feature.

## Alternatives

As above, utilizing [MSC4049](https://github.com/matrix-org/matrix-spec-proposals/pull/4049) to update
`m.space.*` events in other rooms could be an alternative, but due to additional complications in addition
to requiring this MSC to be merged, it is deemed as not the best solution (for now).

## Security considerations

None considered.

## Unstable prefix

None required, as currently no new endpoints or fields are being proposed.

## Dependencies

None.
