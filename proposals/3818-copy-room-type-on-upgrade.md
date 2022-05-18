# MSC3818: Copy room type on upgrade

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
