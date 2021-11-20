# MSC3510: Let users with the same power level kick/ban/demote each other.

## Problem

Matrix currently doesn't let users with the same power level kick, ban or demote
each other. This particularly causes problems for room admins with power
level 100, as if a user is promoted to be an admin, there is no way to demote
them.  Scenarios where this is problematic include:

 * If the admin becomes abusive (e.g. due to change in circumstances, betrayal
   of trust, compromise of their account)
 * If the admin is on a homeserver which is no more, they are stuck in the
   roomlist forever

We also have a problem that it is very disturbing that admins don't have full
control to admin the users in their room. Admins quite reasonably expect to
have full control over their room - much as root has full control on UNIX,
and the current behaviour is very jarring and a constant source of
complaints.

## Solution

We change the room auth rules (which currently seem to be implicit in the
spec?) to allow users to kick, ban or demote other users with the same power
level, assuming the user meets the thresholds in the `m.room.power_levels` event
for `kick`, `ban`, or setting the `m.room.power_levels` event.  In practice, this
means that moderators and admins will then be able to kick/ban/demote each
other (given the default thresholds for kick/ban/demote are 50, which by
convention means 'moderator').

This necessitates a new room version.

This means that the problem of avoiding admins (or mods) enacting coups on
each other becomes a social one: this can be mitigated by using finer
granular PLs (e.g. setting lesser trusted admins to PL 99, if needed).  This
runs the risk of reintroducing the original problem however (that if an admin
with PL100 goes missing or goes rogue, there's no recourse but abandon the
room).

## Alternatives

You could introduce a new threshold beyond which users are allowed to
kick/ban/demote each other. In practice, it feels like the existing
thresholds in `m.room.power_levels` are good enough though.

You could also introduce the concept of a room 'owner' to provide an escape
hatch against a coup between admins.  For instance, you could special-case
the `m.room.create` sender to always be able to promote themselves to admin.
Or you could maintain an `owner` field in `m.room.power_levels` in order to
track a set of matrix IDs which are allowed to override powerlevels to
promote themselves to admin whatever happens.  However, this is orthogonal to
this proposal and should be considered in a separate MSC.

## Security considerations

This lets users enact coups on each other, in exchange for empowering admins
to have full control over their rooms.  Clients must clearly educate users
about the change in behaviour to avoid nasty surprises.