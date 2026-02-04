# MSC4415: Make `/_matrix/client/v3/admin/whois/{userId}` only available to admins

Currently, the `/_matrix/client/v3/admin/whois/{userId}` is available to non-admins
if the requesting user is also the target user. This makes it nonfunctional as an
"Am I an admin?" check.

## Proposals

Make the API only usable for homeserver administrators.

## Potential issues

Clients that previously relied on this API with the assumption of it being usable
for non-admins may break.

## Alternatives

A dedicated "Am I an admin" API could also work.

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.
