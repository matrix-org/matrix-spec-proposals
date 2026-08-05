# MSC3991: Power level up! Taking the room to new heights

Once a room is created, the highest power level is set in stone. Even if you're the only
admin in the room, if you try to raise your own power level above the initial `100`, it
just throws a `403 Forbidden` error:

`PUT /_matrix/client/r0/rooms/{roomId}/state/m.room.power_levels` -> `403 Forbidden`
```json
{
    "errcode": "M_FORBIDDEN",
    "error": "You don't have permission to add ops level greater than your own"
}
```

This is dictated by the [authorization rules (auth
rules)](https://spec.matrix.org/v1.5/rooms/v10/#authorization-rules) around
`m.room.power_levels` in a room:

>  9. If type is `m.room.power_levels`:
>     [...]
> 
>      8. For each entry being changed in, or removed from, the `users` property, other than the `sender`’s own entry:
>          1. If the current value is greater than or equal to the `sender`’s current power level, reject.
>      9. For each entry being added to, or changed in, the `users` property:
>          1. If the new value is greater than the `sender`’s current power level, reject.

It's possible to have power levels greater than the default `100` (Admin) power level
but this has to be specified at the time of room creation.

Not being able to adjust the max power level of `users` after the fact means that any
mistake is baked into the room forever and requires a room upgrade to rectify the
situation. Sometimes, more flexibility is needed in the power level ranges and this only
becomes obvious with hindsight.

For example with the [Gitter
migration](https://blog.gitter.im/2023/02/13/gitter-has-fully-migrated-to-matrix/), we
synced all Gitter room admins over as users with a power level of `90` and set the power
level to do any action at `90` so the bridge bot user could maintain a higher power
level than the rest of the users while giving the room admins autonomy over everything.
Then later after the migration, we wanted to clean up the power levels and grant room
admins the true `100` power level to avoid clients labeling `90` as a "Moderator"
instead of "Admin". But discovered this was impossible to get right because we couldn't
raise the power level of the bridge bot above `100` to still maintain a higher power
level. This condundrum is tracked by https://gitlab.com/gitterHQ/gitter.im/-/issues/4

Something like [MSC3915: Owner power
level](https://github.com/matrix-org/matrix-spec-proposals/pull/3915) could help in a
situation like this to formalize the position of owner but doesn't help with the
flexibility of an existing room. For example, imagine this MSC lands before MSC3915, it
would be nice to just upgrade your room power levels to reflect the new owners role. And
going beyond MSC3915, it can be useful to set a user/bot above `150` at a later date.
Imagine wanting a central company bot to maintain control of every room at power level
`200`. It would be nice to just update your room power levels to achieve this than have
to upgrade every room.


## Proposal

This MSC proposes updating the room event auth rules to allow for raising the `sender`'s
own `users` power level above the current max power level as long as you update all
others at the same level to the new max level.

This means that if you're a solo admin in the room, you can arbitrarily raise your own
power level however you want.

If there are multiple admins in the room, then you must raise all other admins to the
new max power level.

Propsed new auth rule language:

>  9. If type is `m.room.power_levels`:
>     [...]
> 
>      8. For each entry being removed from the `users` property, other than the `sender`’s own entry:
>          1. If the current value is greater than or equal to the `sender`’s current power level, reject.
>      9. For each entry being added to, or changed in, the `users` property:
>          1. If the new value is greater than the `sender`’s current power level and the `sender` *doesn't have* the highest power level in the room, reject.
>          1. If the new value is greater than the `sender`’s current power level, the `sender` *has* the highest power level in the room, but doesn't raise everyone else with the current highest power level to the new value, reject.

Because this MSC changes the authorization rules of a room, it requires a new room
version to ensure all participating servers are authorizing events and state
consistently.


## Potential issues

*None surmised so far*


## Alternatives

Room upgrades allow for creating a new room where you can initially specify
`m.room.power_levels` as desired. There is nothing restricting the integer range that
`users` field of `m.room.power_levels` so all of the same end results can be achieved
this way. But this has all of the flexibility downsides mentioned for existing rooms in
the intro/context paragraphs above though.

---

As an alternative that could solve the [Gitter specific
case](https://gitlab.com/gitterHQ/gitter.im/-/issues/4) where a user with a power level
of `90` appears as "Moderator" when it actually functions as an admin role; this could
be solved by spec'ing out how to figure out what is the admin PL and what is the
moderator PL. Hardcoding random integers to labels just doesn't work well. For example,
with the [Nheko](https://github.com/Nheko-Reborn/nheko) client, it considers people with
the permission to change power levels to be admins and users with redaction permissions
as moderators. Or maybe something more flexible like [MSC3949: Power Level
Tags](https://github.com/matrix-org/matrix-spec-proposals/pull/3949).

This MSC does make sense on top of those kind of changes in any case though.


## Security considerations

Changes to auth rules requires careful consideration of how things interact and the
language should be explicit in what's allowed/rejected. Please review the proposed
changes for holes in the logic.


## Unstable room version

While this feature is in development, the proposed behavior can be trialed with the
`org.matrix.msc3991` unstable room version and `org.matrix.msc3991v2`, etc as we develop
and iterate along the way.
