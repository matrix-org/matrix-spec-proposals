# MSC3385: Bulk small improvements to room upgrades

[Room upgrades](https://matrix.org/docs/spec/client_server/r0.6.1#id160) presently rely on client
and server implementations to determine what information, if any, gets copied to new rooms. The
spec already specifies that core parts of the room (power levels, name, etc) *should* be transferred,
though this does not account for more modern features like Spaces and other functionality.

**TODO**: Words to explain in more detail the rationale to keep the room representation the same.

## Proposal

The set of copied information is updated to say that:

* Servers must transfer "copiable" state from the original room to the new room. Copiable state is anything
  in the `m.*` namespace that isn't a membership event and is not the create event (more on that in the
  next point). This should allow for rooms to maintain future feature sets between upgrades easily.

  Some future features might be sensitive to the sender of the event, though the current spec already says
  that Matrix-namespaced events should be copied, so this is not perceived to be a problem.

* Servers must copy the `content` of the old room's `m.room.create` event before applying the `predecessor`
  and `room_version` properties. This ensures details such as the room type (eg: spaces) and federatable
  status are copied to the new room accurately.

* When the server sees an upgrade, and can validate that the upgrade happened legally (the tombstone and
  predecessor point at each other's rooms), the server must copy per-room account data from the old room
  to the new room. This is not generally done during the `/upgrade` call as rooms can be upgraded over
  federation.

... Others TBD

**TODO**: Mention how Synapse already does the last two points above.

## Potential issues

TODO

## Alternatives

TODO

## Security considerations

TODO

## Unstable prefix

This MSC does not require an unstable prefix as it is codifying behaviour in an area of the spec which permits
implementation-specific behaviour.
