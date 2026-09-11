# MSC4164: Leave all rooms on deactivation

When an account is
[deactivated](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3accountdeactivate),
it removes all ability for the user to login again. However, as the account is not removed from rooms
it is in, this causes the server to still be sent events for rooms that account is in, even if all
of the accounts in that room are deactivated, and hence no user is able to see them.

## Proposal

Servers SHOULD make the account leave all rooms it is currently in when the account is deactivated.

## Potential issues

This makes account deactivation a bit more complicated to implement, however as this has the ability
to save bandwidth, it is deemed worth it.

## Alternatives

None considered.

## Security considerations

None considered.

## Unstable prefix

None required, as no new endpoints or fields are being proposed.

## Dependencies

None.
