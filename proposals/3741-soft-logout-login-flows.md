# MSC3741: Revealing the useful login flows to clients after a soft logout

[Soft Logout](https://spec.matrix.org/v1.2/client-server-api/#soft-logout) is a mechanism servers
can use to expire a session without having the client wipe all local state. This is primarily
useful in settings where sessions are (relatively) short lived due to server policy or a
[refresh token](https://github.com/matrix-org/matrix-doc/pull/2918) expiring.

Currently, if a server were to offer multiple flows the client
[would be confused](https://github.com/matrix-org/matrix-doc/issues/2853) and potentially show either
the wrong flow, or an unhelpful flow. When the server uses both password registration and
[SSO](https://spec.matrix.org/v1.2/client-server-api/#sso-client-loginauthentication), it is generally
assumed by clients that the server is offering "Social Login" mechanisms as an optional way to skip
[User-Interactive Authentication](https://spec.matrix.org/v1.2/client-server-api/#user-interactive-authentication-api)
flows. In Element, this is shown as 3rd party login options alongside a regular password form.

This MSC aims to assist clients in showing a more helpful flow for the user. Specifically, it aims
to have the client tell the server who is re-authenticating and thus the server can offer *just*
the flows which are relevant for that user's account (eg: just the SSO provider they used, or just
password flows if they never used SSO to sign up).

## Proposal

Quite simply, the client provides the now-expired access token to the
[`/login`](https://spec.matrix.org/v1.2/client-server-api/#login) endpoint - just as it would any
other request.

Currently servers (should) be checking to see if the provided access token is an appservice user,
for [appservice login](https://spec.matrix.org/v1.2/client-server-api/#appservice-login), however
under this new approach the server would need to add a check for past users too.

If the access token is recognized by the server, the server would expose only the useful flows to
the client in the response. As explained in the MSC intro, this could be *just* password flows, or
just SSO flows, depending on how the user's account was created/linked up. The server should avoid
returning flows which will ultimately lead to a different user ID being logged in (eg: responding
with an SSO flow to a password-only account would mean that the original user ID could end up being
overwritten if the user clicks the SSO button instead of the password form).

If the server does not recognize the access token it simply returns flows as though authentication
was not provided. This is to avoid clients having to re-submit a login request without the token,
and to discourage simple scripts which might loop through a list of acquired tokens in hopes of
finding out more about the account (like which SSO provider they signed up with).

Servers are not required to maintain knowledge of expired tokens, even if they soft logout the token.
While helpful, there are certainly valid reasons to refuse knowledge that an access token ever existed.
A server might choose to delete knowledge of an expired token after one or more specific conditions
are met though, such as:
* When a successful login with the same device ID is made (as the client will have presumably been
  able to re-authenticate appropriately).
* When the refresh token is used to get a new access token.
* After N days of being expired.

## Potential issues

Listed in proposal text.

## Alternatives

No viable alternatives known.

## Security considerations

This effectively encourages servers to maintain knowledge of expired tokens for a period of time,
particularly when soft logout is used. This might not be desirable for some server admins/security
policies. As such, this MSC is deliberate in making knowledge of expired tokens optional.

## Unstable prefix

While this MSC is not considered stable, clients should use `/_matrix/client/unstable/org.matrix.msc3741/login`
instead of the regular login endpoint to adopt the new behaviour. To save on round trip times, servers
*SHOULD* expose `org.matrix.msc3741` in the `unstable_features` section of `/_matrix/client/versions`
so clients which already cache the `/versions` response can detect support.

## Dependencies

No known dependencies.
