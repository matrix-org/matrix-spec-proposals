# MSC3991: Room takeover

In the current Spec, room members with the same power level cannot decrease or remove each other's power level.
However, a room admin may wish to legitimately demote another room admin.

For this proposal a "room admin" is a user with the highest power level in a room. For the use case this MSC addresses, a room must have two or more room admins.

There are multiple scenarios of why one room admin wishes to demote another room admin:

* The home server admin of a room admin can no longer be trusted.
  * "I no longer want room admins with an account on evil.com, because their home server admin started messing with rooms."
* The home server of a room admin has been compromised.
  * "I no longer want room admins with an account on compromised.com, because their home server has been hacked."
* The home server of a room admin went offline and cannot be recovered.
  * "I no longer want room admins with an account on foo.com, because the domain is available for sale and a new domain owner could use the custom power level for evil."
* The account of a room admin has been compromised.
  * "I want to demote Alice, because her account got hacked. She now has a new account."
* The account of a room admin is no longer in use or deactivated.
  * "I want to demote Bob, because he left the company."
* A room admin can no longer be trusted.
  * "I want to demote Charles, because they left their role as an organiser."

Use cases:
* The IT department of an organisation wants to demote a room admin when or after the person leaves the company.
* A meetup group with multiple organisers wants to demote a former organiser.
* An organisation migrates from one domain to another. To avoid having to ask every room admin to demote themselves while promoting their new accounts, they want one account that has the permission to do so.
* To ensure my ownership of a room, I added multiple of my accounts as room admins to a room. One of the accounts is no longer accessible to me and I want to demote that account.

## Proposal 1 (simplest: `allow_demotons`)

This MSC proposes an optional boolean `allow_demotons` to be added to the `m.room.power_levels` state event. Its default value is `false` to be compatible with the current behaviour.

If `true`, a room member with the highest power level can lower (or remove) the power level of other room members with the same power level.

```json
{
    "allow_demotons": true,
    "ban": 50,
    "events": {
        "m.room.name": 100,
        "m.room.power_levels": 100
    },
    "events_default": 0,
    "invite": 50,
    "kick": 50,
    "notifications": {
        "room": 20
    },
    "redact": 50,
    "state_default": 50,
    "users": {
        "@alice:localhost": 100,
        "@bob:localhost": 100,
        "@charles:localhost": 50,
        "@delilah:localhost": 50
    },
    "users_default": 0
}
```

* Alice and Bob can lower each other's power level. _(this is the change!)_
* Charles and Delilah can not lower each other's power level, because they don't have the highest power level.

## Proposal 2 (simple: `owner`)

This MSC proposes an optional string array `owners` to be added to the `m.room.power_level` state event. Its default value is an empty array to be compatible with the current behaviour.

Any Matrix user listed in the array can lower (or remove) the power level of any member. They cannot raise their own power level based on this, to prevent an ambiguity of their actual power level.

```json
{
    "ban": 50,
    "events": {
        "m.room.name": 100,
        "m.room.power_levels": 100
    },
    "events_default": 0,
    "invite": 50,
    "kick": 50,
    "notifications": {
        "room": 20
    },
    "owners": [
        "@delilah:localhost"
    ],
    "redact": 50,
    "state_default": 50,
    "users": {
        "@alice:localhost": 100,
        "@bob:localhost": 100,
        "@charles:localhost": 50,
        "@delilah:localhost": 50
    },
    "users_default": 0
}
```

* Alice and Bob can not lower each other's power level.
* Charles can not lower Delilah's power level.
* Delilah can lower everyone's power level. She could demote Alice to allow Bob to take over the room. _(this is the change!)_
  * She could also demote everyone but herself. This would decrease the highest power level of the room to 50 which is her own.

## Proposal 3 (complex: `takeover_users`)

This MSC proposes an optional array `takeover_users` to be added to the `m.room.power_level` state event. Its default value is an empty array to be compatible with the current behaviour.

Any Matrix user listed in the array can lower (or remove) the power level of any member. They cannot raise their own power level based on this, to prevent an ambiguity of their actual power level.

```json
{
    "ban": 50,
    "events": {
        "m.room.name": 100,
        "m.room.power_levels": 100
    },
    "events_default": 0,
    "invite": 50,
    "kick": 50,
    "notifications": {
        "room": 20
    },
    "redact": 50,
    "state_default": 50,
    "takeover_users": {
        "@charles:localhost": [
            "@alice:localhost"
        ],
        "@delilah:localhost"
    },
    "users": {
        "@alice:localhost": 100,
        "@bob:localhost": 100,
        "@charles:localhost": 100,
        "@delilah:localhost": 50
    },
    "users_default": 0
}
```

* Alice and Bob can not lower each other's power level.
* Charles can lower the power level of Alice, but not the other room admins. _(this is different!)_
* Delilah can lower everyone's power level. She could demote Alice and Charles to allow Bob to take over the room. _(this is different!)_

## Potential issues

Simplest: It's simple but might not cover more complex use cases. It could be that one wishes to only allow a subset of room admins to take over a room.

Simple: It covers more use cases and also allows a room owner who can demote admins while not being allowed to otherwise change the power levels state event.

Complex: It covers even more cases but might introduce more complexity than needed. On the Other hand it allows fine tuning over who is allowed to demote which other user.

## Similar but different MSCs

* [MSC3915: Owner power level](https://github.com/matrix-org/matrix-spec-proposals/pull/3915) introduces a new named power level 150, however, it does not solve the use case of demotng rogue users.
* [MSC3991: Power level up! Taking the room to new heights
](https://github.com/matrix-org/matrix-spec-proposals/pull/3991) allows room admins to raise their power level, however, it specifies that all members with the highest power level must be set to the new level.

## Alternatives

* I don't know of any alternatives outside of this MSC.
* While all three proposals can be implemented simultaneously, I see them as alternatives. Only one proposal should be introduced to the Matrix Spec.

## Security considerations

The current spec does not allow for a room admin to demote another admin. This MSC would allow them to become a sole room admin by upgrading the room, changing the state event for them to take over the room and then demotng other admins.

## Unstable room version

While this feature is in development, the proposed behavior can be trialed with the
`org.matrix.msc3993` unstable room version, etc as we develop and iterate along the way.
