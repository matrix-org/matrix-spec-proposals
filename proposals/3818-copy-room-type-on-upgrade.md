# MSC3818: Copy room type on upgrade

Unless the room upgrade API specifies that room type must be copied over, clients cannot rely on
rooms staying the same type leading to trouble.


## Proposal

This MSC proposes that the room upgade API MUST copy the [room type](https://spec.matrix.org/v1.2/client-server-api/#types)
over to the new room. Otherwise clients cannot trust that to happen and [Spaces](https://spec.matrix.org/v1.2/client-server-api/#spaces)
or [MSC3588](https://github.com/matrix-org/matrix-spec-proposals/pull/3588) Story rooms may incorrectly become
normal rooms breaking user-experience.

The Spec currently specfies this in [section 11.32.3. server behaviour](https://spec.matrix.org/v1.2/client-server-api/#server-behaviour-16):

> 2. Creates a replacement room with a `m.room.create` event containing a `predecessor` field and the applicable `room_version`.

It becomes:

> 2. Creates a replacement room with a `m.room.create` event containing a `predecessor` field, a
> `type` field set to what it was in the previous room (if it was set), and the applicable `room_version`.


## Potential issues

Some room types such as Spaces also require copying over state events as a part of the update progress,
in case of Spaces, `m.space.child` events. However as that can be changed later and done by the client,
it's out of scope for this MSC.

## Alternatives

A suggested alternative is having every room type specify their own update process if they use other
room types. However this would complicate the MSC process with even simple client-side proposals
requiring also a server-side implementation. This could also result in room types dependent on a
particular server software or discourage using Matrix for a smaller project where an MSC wasn't
otherwise consider necessary.

## Security considerations

Non-applicable.

## Unstable prefix

Non-applicable.

## Dependencies

Non-applicable.
