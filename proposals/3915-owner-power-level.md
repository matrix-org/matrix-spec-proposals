# MSC3915: Owner power level

## Problem

Matrix today does not distinguish between 'room admins' who have permission to do privileged operations in a room
(set PLs, ACLs, tombstones, history visibility, encryption, create/remove moderators)... and the 'owners' aka 'founders'
of a room, who have overall responsibility and ownership for it and appoint (and deappoint) admins to help them run it.

As a result, it's common for a room founder to promote a set of users to be admins at PL100 to share responsibility
for administering the room... but then regret that they have effectively relinquished ownership of the room, given there
is no way to revoke admin permissions (short of coercing the other admins to demote themselves).

This is particularly problematic for users migrating from other communities such as Discord or even IRC where room
permissions distinguish owner from admin, and so apply the same terminology in Matrix, accidentally promoting users to
admin thinking they can revoke it (despite the UI warnings to the contrary).

Finally, the current workaround of having to manually assign 'admins' to PL99 and manually rewrite the PL event
thresholds is incredibly uninuitive and bad UI (for instance, many clients will show the PL99 as 'Moderator' in the UI,
confusing it with PL50).  Moreover, you can't apply the workaround in retrospect; the owner either has to create a
whole new room with the correct permissions or anticipate the problem before you accidentally assign a user to PL100.

This closes the embarassingly long-standing https://github.com/matrix-org/matrix-spec/issues/165 spec issue, and
replaces the previous flawed [MSC3510](https://github.com/matrix-org/matrix-spec-proposals/pull/3510) proposal.

## Proposal

 * We expand the recommended range of PLs to 0-150, with 150 described as 'Owner'.
 * The room creator defaults to PL150.
 * We tighten the language in the spec which says "Clients may wish to assign names to particular power levels." to
   specify the threshold names more concretely, to avoid divergent implementations.

Everything else stays the same (e.g. the `trusted_private_chat` prefix would still give invited users Owner too, to
share ownership of the DM with them).

This clearly differentiates owners from their delegated admins, is compatible with existing rooms without a room version
bump, and lets clients implement cmopletely different UI for appointing/deappointing admins to the special-case of
transferring/sharing ownership.

## Potential issues

None?

## Alternatives

 * We could add an `owner` field or `owners` field to the PL event. However, this breaks compatibility, and has no
   obvious benefit from simply having a higher PL number for owners.

 * We could redeclare the Admin PL threshold to be 75 or 99 or similar, thus showing all existing Admins as being Owners
   in the UI.  However, this will cause confusion with older clients, as well as confusion over users being seen to
   apparently suddenly changing power levels.  It's better to reflect the current reality: that historically we haven't
   had the concept of owners, rather that retconning the historical admins into being owners.

 * We could workaround it with an 'adminbot' with PL100, which is the sole robot owner of the room, and ensures that
   human admins don't accidentally promote each other.  This is a horrible hack, given the protocol itself should
   intrinsically support basic features such as access control.

 * We could ignore it, and try to educate admins into understanding that admin = owner, and they should set custom PLs
   if they want something else.  In practice this simply hasn't worked, hence this MSC.

## Security considerations

Clients or servers which incorrectly assume that PLs range from 0 to 100 may get confused.  This would clearly be
an implementation bug however.

## Unstable prefix

None

## Dependencies

None
