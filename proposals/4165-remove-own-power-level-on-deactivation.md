# MSC4165: Remove own power level on deactivation

When an account is
[deactivated](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3accountdeactivate), the
[`m.room.power_levels`](https://spec.matrix.org/v1.11/client-server-api/#mroompower_levels) in rooms the
account is currently in is unmodified. If no other accounts have a higher power level than the deactivated
account, the account cannot be demoted without intervention of the server admin. This leads to potential
security issues, such as if the server is compromised or the domain is later bought by a bad actor, the rooms
where deactivated users on that domain had elevated privileges could also become compromised.

## Proposal

When an account is deactivated, the server SHOULD do the following in all rooms the account is currently in:
- If there is a `m.room.power_levels` state, and in there is a key for the current user inside the `users`
field:
  - If the auth rules for the room allow doing so, send a new `m.room.power_levels` event identical to the
  current state, with the exception of the field for the current user inside `users` removed.

## Potential issues

This adds additional complexity to the account deletion process, but as this has the potential to mitigate
the effects of certain attacks, it is deemed worth it.

This also can cause issues where the deactivated account is the only account able to moderate a room, meaning
that the account cannot then be moderated by the server administrator, unlike now.

## Alternatives

This same process can instead occur when rooms are left, which also fixes this issue for rooms which the
account is not in at the time of deletion. However, leaving a room is not a permanent action, and the user
may want to re-join, whereas account deactivation is permanent, so it may not make sense to do this process
when the room is left instead.

## Security considerations

None considered.

## Unstable prefix

None required, as no new endpoints or fields are being proposed.

## Dependencies

None.
