# MSC2918: Refresh tokens

In Matrix, requests to the Client-Server API are currently authenticated using non-expiring, revocable access tokens.
An access token might leak for various reasons, including:

 - leaking from the server database (and its backups)
 - intercepting it with a man-in-the-middle attack
 - leaking from the client storage (and its backups)

In the OAuth 2.0 world, this vector of attack is partly mitigated by having expiring access tokens with short lifetimes and rotating refresh tokens to renew them.
This MSC adds support for expiring access tokens and introduces refresh tokens to renew them.
A more [detailed rationale](#detailed-rationale) of what kind of attacks it mitigates lives at the end of this document.

## Proposal

Homeservers can choose to have access tokens expire after a short amount of time, forcing the client to renew them with a refresh token.
A refresh token is issued on login and rotates on each usage.

It allows homeservers to opt for signed and non-revocable access tokens (JWTs, Macaroon, etc.) for performance reasons if their expiration is short enough (less than 5 minutes).
Whether the access token expire and what lifetime they have is up to the homeserver, but client have to support refreshing tokens.

It is heavily recommended for clients to support refreshing tokens for additional security.
They can advertise their support by adding a `"refresh_token": true` field in the request body on the `/login` and `/register` APIs.

Handling of clients that do *not* support refreshing access tokens is up to individual homeserver deployments.
For example, server administrators may choose to support such clients for backwards-compatibility, or to expire access tokens anyway for improved security at the cost of inferior user experience in legacy clients.

If a client uses an access token that has expired, the server will respond with an `M_UNKNOWN_TOKEN` error.
Thus, if a client receives an `M_UNKNOWN_TOKEN` error, and it has a refresh token available, it should no longer assume that it has been logged out, and instead attempt to refresh the token.
If the client was in fact logged out, then the server will respond with an `M_UNKNOWN_TOKEN` error, possibly with the `soft_logout` parameter set.

### Login API changes

The login API returns two additional fields:

- `expires_in_ms`: The lifetime in milliseconds of the access token.
- `refresh_token`: The refresh token, which can be used to obtain new access tokens.

This also applies to logins done by application services.

Both fields are optional.
If `expires_in_ms` is missing, the client can assume the access token won't expire.
If `refresh_token` is missing but `expires_in_ms` is present, the client can assume the access token will expire but it won't have a way to refresh the access token without re-logging in.

Clients advertise their support for refreshing tokens by setting the `refresh_token` field to `true` in the request body.

### Account registration API changes

Unless `inhibit_login` is `true`, the account registration API returns two additional fields:

- `expires_in_ms`: The lifetime in milliseconds of the access token.
- `refresh_token`: The refresh token, which can be used to obtain new access tokens.

This also applies to registrations done by application services.

As in the login API, both field are optional.

Clients advertise their support for refreshing tokens by setting the `refresh_token` field to `true` in the request body.

### Token refresh API

This API lets the client refresh the access token.
A new refresh token is also issued.
The existing refresh token remains valid until the new access token (or refresh token) is used, at which point it is revoked.
This allows for the request to get lost in flight.
The Matrix server can revoke the old access token right away, but does not have to since its lifetime is short enough that it will expire anyway soon after.

`POST /_matrix/client/r0/refresh`

```json
{
  "refresh_token": "aaaabbbbccccdddd"
}
```

response:

```json
{
  "access_token": "xxxxyyyyzzz",
  "expires_in_ms": 60000,
  "refresh_token": "eeeeffffgggghhhh"
}
```

If the `refresh_token` is missing from the response, the client can assume the refresh token has not changed and use the same token in subsequent token refresh API requests.

The `refresh_token` parameter can be invalid for two reasons:

 - if it does not exist
 - if it was already used once

In both cases, the server must reply with a `401` HTTP status code and an `M_UNKNOWN_TOKEN` error code.
This new use case of the `M_UNKNOWN_TOKEN` error code must be reflected in the spec.
As with other endpoints, the server can include an extra `soft_logout` parameter in the response to signify the client it should do a soft logout.

This new API should be rate-limited and does not require authentication since only the `refresh_token` parameter is needed.
Identity assertion via the `user_id` query parameter as defined by the Application Service API specification is disabled on this endpoint.

### Device handling

The current spec states that "Matrix servers should record which device each access token is assigned to".
This must be updated to reflect that devices are bound to a session, which are created during login and stays the same after refreshing the token.

## Potential issues

The refresh token being rotated on each refresh is strongly recommended in the OAuth 2.0 world for unauthenticated clients to avoid token replay attacks.
This can however make the deployment of CLI tools for Matrix a bit harder, since the credentials can't be statically defined anymore.
This is not an issue in OAuth 2.0 because usually CLI tools use the client credentials flow, also known as service accounts.
An alternative would be to make the refresh token non-rotating for now but recommend clients to support rotation of refresh tokens and enforce it later on.

## Alternatives

This MSC defines a new endpoint for token refresh, but it could also be integrated as a new authentication mechanism.

## Security considerations

The time to live (TTL) of access tokens isn't enforced in this MSC but is advised to be kept relatively short.
Servers might choose to have stateless, digitally signed access tokens (JWT are good examples of this), which makes them non-revocable.
The TTL of access tokens should be around 15 minutes if they are revocable and should not exceed 5 minutes if they are not.

## Unstable prefix

While this MSC is not in a released version of the specification, clients should use the `org.matrix.msc2918.refresh_token` field in place of the `refresh_token` field in requests to the login and registration endpoints.
The refresh token endpoint should be served and used using the unstable prefix: `POST /_matrix/client/unstable/org.matrix.msc2918/refresh`.

## Detailed rationale

This MSC does not aim to protect against a completely compromised client.
More specifically, it does not protect against an attacker that managed to distribute an alternate, compromised version of the client to users.
In contrast, it protects against a whole range of attacks where the access token and/or refresh token get leaked but the client isn't completely compromised.

For example, those tokens can leak from user backups (user backs up his device on a NAS, the NAS gets compromised and leaks a backup of the client's secret storage), but one can assume those backups could be at least 5 min old.
If the leak only includes the access token, it is useless to the attacker since it would have expired.
If it also includes the refresh token, it is useless *if* the token was refreshed before (which will happen if the user just opens their Matrix client in between).

Worst case scenario, the leaked refresh token is still valid: in this case, the attacker would consume the refresh token to get a valid access token, but when the original client tries to use the same refresh token, the homeserver can detect it, consider the session has been compromised, end the session and warn the user.

This kind of attack also applies to leakage from the server, which could happen from database backups, for example.

The important thing here is while it does not completely prevent attacks in case of a token leakage, it does make this range of attack a lot more time-sensitive and detectable.
A homeserver will notice if a refresh token is being used twice.

The IETF has interesting [guidelines for refresh tokens](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics#section-4.13.2).
They recommend that either:

 - the refresh tokens are sender-bound and require client authentication (making token leakage completely useless if the client credentials are not leaked at the same time)
 - or make them rotate to make the attack a lot harder, as described just above.

Since all clients are "public" in the Matrix world, there are no client-bound credentials that could be used, hence the rotation of refresh tokens.

---

The other kind of scenario where this change makes sense is to help further changes in the homeservers.
A good, recent example of this, is in Synapse v1.34.0 [they moved away from macaroons for access tokens](https://github.com/matrix-org/synapse/pull/5588) to random, shorter, saved in database tokens, similar to [what GitHub did recently](https://github.blog/2021-04-05-behind-githubs-new-authentication-token-formats/).

Because there is no refresh token mechanism in the C2S API, most Synapse instances now have a mix of the two formats of tokens, and for a long time.
It makes it impossible to enforce the new format of tokens without invalidating all existing sessions, making it impossible to roll out changes like a web-app firewall in front of Synapse that verifies the shape and checksums of tokens even before reaching Synapse.

---

Lastly, expiring tokens already exist in Synapse (via the `session_lifetime` configuration parameter).
Before this MSC, clients had no idea when the session would end and relied on the server replying with a 401 error with `soft_logout: true` in the response on a random request to trigger a soft logout and go through the authentication process again.
A side effect of this MSC (although it could have been introduced separately) is that the login responses can now include a `expires_in_ms` to inform the clients when the token will expire.
