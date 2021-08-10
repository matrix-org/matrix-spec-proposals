# MSC3325: Upgrading invite-only rooms

Rooms occasionally need to be upgraded to newer versions to take use new
features or for security reasons.  When public rooms are upgraded, the new room
is public as well, so users in the old room are able to join the new room
freely.

However, if the new room are only accessible to invited users (which will
usually be the case when the original room was only accessible to invited
users), users will need to be invited to the new room, which means that the
person who upgrades the room will need to send out many invites.

Rather than inviting all the members of the old room, we can use [MSC3083:
Restricting room membership based on membership in other
rooms](https://github.com/matrix-org/matrix-doc/pull/3083) to allow members of
the old room to join the new room.

The spec currently does not define the expected state of the new room when
upgrading a room, but rather recommends that certain state events be copied
over.  We propose that the spec should additionally recommend that servers make
use of the `restricted` join rule, where possible and when necessary, to allow
members of the original room to join the new room.

## Proposal

When a client requests to upgrade a room using the `POST
/rooms/{roomId}/upgrade` endpoint on a room with `m.room.join_rules` set to
`invite` or `restricted`, and the new room is created with a room version that
supports the `restricted` join rule, the new room should be created with the
`m.room.join_rules` set to `restricted`, and with an `allow` array that
specifies that members of the old room may join, along with any room specified
in the original room's `allow` array, if its join rule was also `restricted`.

Other tools that are used to upgrade rooms should behave similarly.

## Potential issues

This proposal only applies to rooms with `m.room.join_rules` set to `invite` or
`restricted`, and not `knock` since rooms cannot (currently) be set to both
knock and to allow users based on membership in another room.  If a future room
version allows both to be used, then this proposal can be extended at that
time.

If the room is encrypted, users will not receive the keys to decrypt messages
until they join the room.  This is similar to the current room upgrade issue
where if the `m.room.history_visibility` is set to `joined`, in which users
will not be able to see messages from before they join.

## Alternatives

As mentioned in the introduction, we could continue to invite members of the
original room to the upgraded room.

Alternatively, the homeserver that creates the room could set the membership
in the new room for each member of the original room to `invited`, without
actually sending the invite, thus avoiding the problem of invite spam.

[MSC2214](https://github.com/matrix-org/matrix-doc/pull/2214) proposes a new
state event that indicates a user's membership in the original room, which can
be used to verify if a user is allowed to join the room.

## Security considerations

The security consideration listed in MSC3083 applies to this proposal as well:

> Increased trust to enforce the join rules during calls to `/join`, `/make_join`,
> and `/send_join` is placed in the homeservers whose users can issue invites.
> Although it is possible for those homeservers to issue a join event in bad faith,
> there is no real-world benefit to doing this as those homeservers could easily
> side-step the restriction by issuing an invite first anyway.

A user may get kicked from the upgraded room, but still be able to rejoin due
to being a member of the original room.  This is in contrast with an
invite-only room, where a user who is kicked cannot rejoin unless they are
re-invited.  This can be worked around by banning the user rather than kicking
them.

## Unstable prefix

This proposal only changes the behaviour of homeservers, and does not introduce
any new events or endpoints, so no unstable prefix is needed.
