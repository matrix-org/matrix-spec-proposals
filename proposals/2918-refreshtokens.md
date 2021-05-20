# MSC2918: Refresh tokens

Requests are currently authenticated using non-expiring, revocable access tokens.
This goes against security best practices known in the OAuth 2.0 world.
This MSC make the access tokens expiring and introduces refresh tokens to renew them to fight against token replay attacks.

## Proposal

The access token returned by the login endpoint expires after a short amount of time, forcing the client to renew it with a refresh token.
A refresh token is issued on login and rotates on each usage.

Homeservers can choose to make the access tokens signed and non-revocable for performance reasons if the expiration is short enough (less than 5 minutes).

### Login API changes

The login API returns two additional fields:

- `expires_in_ms`: The lifetime in milliseconds of the access token.
- `refresh_token`: The refresh token, which can be used to obtain new access tokens.


### Account registration API changes

Unless `inhibit_login` is `true`, the account registration API returns two additional fields:

- `expires_in_ms`: The lifetime in milliseconds of the access token.
- `refresh_token`: The refresh token, which can be used to obtain new access tokens.

### Token refresh API

This API lets the client refresh the access token.
A new refresh token is also issued, and the existing one is revoked.
The Matrix server doesn't have to make the old access token invalid, since its lifetime is short enough.

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
  "expires_in_ms": 60,
  "refresh_token": "eeeeffffgggghhhh"
}
```

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
The TTL of access tokens should not exceed 15 minutes if they are revocable and 5 minutes if they are not.

## Unstable prefix

While this MSC is not in a released version of the specification, clients should add a `org.matrix.msc2918.refresh_token=true` query parameter on the login endpoint, e.g. `/_matrix/client/r0/login?org.matrix.msc2918.refresh_token=true`.
The refresh token endpoint should be served and used using the unstable prefix: `POST /_matrix/client/unstable/org.matrix.msc2918/refresh`.
