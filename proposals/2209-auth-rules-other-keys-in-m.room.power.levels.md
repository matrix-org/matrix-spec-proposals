# Update auth rules to check notifications key in m.room.power_levels

## Introduction

The key `notifications` was added to the `m.room.power_levels` event after the
finalisation of the auth rules specified in room version 1. This leads to the
fact, that this dictionary is not subject to the same validation as other
dictionaries in the event, such as `users` or `events`. This especially means
that Alice is able to alter any entry within the dictionary including ones,
that are above her own power level, which is inconsistent with the behaviour
for the other two dictionaries.

[m.room.power_levels](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-power-levels)
[room version 1](https://matrix.org/docs/spec/rooms/v1)

## Proposal

The auth rules regarding `m.room.power_levels` have been established in room
version 1. The general idea here was that creators of a new `m.room.power_levels`
event are only able to make changes to something that is equal to or lower than
their own power level.
So, assuming a room with Alice (50), Bob (100), `m.room.power_levels` at 50,
`m.room.name` at 75 and `m.room.topic` at 25 would mean the following:

* Alice CAN alter `m.room.topic` to any power level up to her own, in this case 50
* Alice is NOT able to alter `m.room.name` since the current value is higher than
her own (75 > 50)
* Alice is NOT able to alter the power level of Bob, since his current value is
higher than her own (100 > 50)
* Alice is free to set the level for anything that has not been defined such as
`org.alice.message` up to a maximum of 50

Later on the key `notifications` was added to the `m.room.power_levels` event.
It contains a mapping of notification keys to a power level, that is required
for a user to trigger the specific notification. The most famous notification
type is the `@room` notification.

Going back to the original example because this key was added later on, the auth
rules make no mention of it, which enables the following behaviour. *It is assumed
that `@room` is at 75*

* Alice can add any key to the dictionary and set the value to any value she wants,
including ones higher than her own.
* Alice can alter the value for `@room` to any value she wants, including ones that
are higher than her own, even though her own value is lower.

The proposed solution is to alter the auth rules and add the `notifications` dictionary
to the same rules that handle `events` and `users`.

So the rule [10.d](https://matrix.org/docs/spec/rooms/v1.html) of the auth rules in
room version 1 would be updated in a new room version to:


> For each entry being added, changed or removed in events, users __and notifications__
>keys:


## Tradeoffs

The proposed solution would be a breaking change with current room versions and
the alternative would be to leave the `notifications` key without any checks.

## Security considerations

This is likely to improve security because it prevents malicious users that were
only given the right to emit `m.room.power_levels` so that they could alter a very
specific key, such as `invite`, from altering the rules established for triggering
notifications.

## Conclusion

The current spec conform behaviour regarding `notifications` is inconsistent with
behaviour shown by the other dictionaries and room administrators are very likely
expecting the `notifications` to work the same as them. The required change is minimal
is and also in line with the general spirit of the auth rules regarding the
`m.room.power_levels` event. A new room version is, however, required. This can be
done with other pending changes.
