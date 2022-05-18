# MSC3818: Copy room type on upgrade

Unless the room upgrade API specifies that room type must be copied over, clients cannot rely on
rooms staying the same type leading to trouble.


## Proposal

This MSC proposes that the room upgade API MUST copy the room type over to the new room. Otherwise
clients cannot trust that to happen and Spaces or MSC3588 Story rooms may incorrectly become normal
rooms breaking user-experience.

The Spec currently specfies this in [section 11.32.3. server behaviour](https://spec.matrix.org/v1.2/client-server-api/#server-behaviour-16):

> 2. Creates a replacement room with a `m.room.create` event containing a `predecessor` field and the applicable `room_version`.

It becomes:

> 2. Creates a replacement room with a `m.room.create` event containing a `predecessor` field, a
> `type` field if it was set in the previous room, and the applicable `room_version`.


## Potential issues

Non-applicable.

## Alternatives

Non-applicable.

## Security considerations

Non-applicable.

## Unstable prefix

Non-applicable.

## Dependencies

Non-applicable.
