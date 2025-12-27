# MSC4168: Update `m.space.*` state on room upgrade

When a [room upgrade](https://spec.matrix.org/v1.11/client-server-api/#room-upgrades) is performed,
many state events are copied over to the new room, to minimize the amount of work the user has to do
after the upgrade. However, the spec doesn't currently recommend that `m.space.child` or `m.space.parent`
be copied over, as well as these events being updated in other rooms.

## Proposal

In the following sentences, "relevant space state events" refer to `m.space.parent` events for all
room types, in addition to `m.space.child` events for rooms with a type of
[`m.space`](https://spec.matrix.org/v1.16/client-server-api/#types).

When a room upgrade is performed, servers SHOULD copy relevant space state events from the old room
to the new room. The sender field in the new event should be set to the user who performed the
upgrade.

In addition, servers SHOULD update relevant space state events in rooms that reference the old room
(in their `state_key` field). Note that this will only be possible in rooms where the upgrading
user (or any other user on the same homeserver, if the implementation decides to use any user it
can) has the power to do so.

The `via` field of each new state event SHOULD only contain the server name of the server,
regardless of its previous content. This is because the server's listed in the previous `via` field
may not have joined the upgraded room yet, and thus servers may not be able to join through them.


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
