# MSCXXXX: Copy room type on upgrade.

There can never be enough templates in the world, and MSCs shouldn't be any different. The level
of detail expected of proposals can be unclear - this is what this example proposal (which doubles
as a template itself) aims to resolve.

Unless the room upgrade API specifies that room type must be copied over, clients cannot rely on
rooms staying the same type leading to trouble.


## Proposal

This MSC proposes that the room upgade API MUST copy the room type over to the new room. Otherwise
clients cannot trust that to happen and Spaces or MSC3588 Story rooms may incorrectly become normal
rooms breaking user-experience.


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
