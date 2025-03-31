# MSC4254: Usage of [RFC7009] Token Revocation for Matrix client logout

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC][MSC3861].

This MSC specifies how Matrix clients should use OAuth 2.0 Token Revocation as defined in [RFC7009] to implement client logout.

## Proposal

### Prerequisites

This proposal requires the client to know the following authorization server metadata about the homeserver:

- `revocation_endpoint`: the URL where the client is able to revoke tokens

The discovery of the above metadata is out of scope for this MSC, and is currently covered by [MSC2965].

### Token revocation

When a user wants to log out from a client, the client SHOULD revoke either its access token or refresh token by making a POST request to the revocation endpoint as described in [RFC7009].

The server MUST revoke both the access token and refresh token associated with the token provided in the request.

The request includes the following parameters, encoded as `application/x-www-form-urlencoded`:

- `token`: This parameter MUST contain either the access token or the refresh token to be revoked.
- `token_type_hint`: This parameter is OPTIONAL, and if present, MUST have a value of either `access_token` or `refresh_token`.  The server MAY use this value to optimize the token lookup process
- `client_id`: The client identifier obtained during client registration. This parameter is OPTIONAL.

If the `client_id` is not provided, or does not match the client associated with the token, the server SHOULD still revoke the token.
This behavior is meant to help good actors like secret scanning tools to proactively revoke leaked tokens.
The server MAY also warn the user that one of their sessions may be compromised in this scenario.

#### Sample flow

Revoking using the access token:

```http
POST /oauth2/revoke HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

token=mat_ooreiPhei2wequu9fohkai3AeBaec9oo&
token_type_hint=access_token&
client_id=s6BhdRkqt3
```

```http
HTTP/1.1 200 OK
```

Or equivalently, using the refresh token:

```http
POST /oauth2/revoke HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded

token=mar_Pieyiev3aenahm4atah7aip3eiveizah&
token_type_hint=refresh_token&
client_id=s6BhdRkqt3
```

```http
HTTP/1.1 200 OK
```

### Handling errors

The server may return an error response as defined in [RFC7009]. Note that RFC7009 mandates a [RFC6749 error response](https://datatracker.ietf.org/doc/html/rfc6749#section-5.2) rather than a Matrix standard error response.

The client should handle these errors appropriately:

- If the token is already revoked or invalid, the server returns a 200 OK response
- If the client is not authorized to revoke the token, the server returns a 401 Unauthorized response
- For other errors, the server returns a 400 Bad Request response with error details

### Replacement of existing APIs

This proposal replaces the existing [`/_matrix/client/v3/logout`] endpoint for [MSC3861]-compatible clients.
Those clients MUST use this mechanism to logout, and clients using the [`/_matrix/client/v3/login`] endpoint to login MUST keep using the existing [`/_matrix/client/v3/logout`] endpoint.

Note that this proposal does not itself provide alternatives to endpoints like [`POST /_matrix/client/v3/logout/all`], [`DELETE /_matrix/client/v3/devices/{deviceId}`] or [`POST /_matrix/client/v3/delete_devices`].
Under the [MSC3861] proposal, management of other devices is not the responsibility of the client, and should instead be provided in a separate user interface by the homeserver.


## Potential issues

The main consideration around token revocation is ensuring proper cleanup of all related tokens and state. The server must:

1. Track the relationship between access tokens and refresh tokens
2. Properly revoke both tokens when either one is provided
3. Clean up any Matrix device associated with the session

## Alternatives

### OpenID Connect RP-Initiated Logout

OpenID Connect defines a [RP-Initiated Logout](https://openid.net/specs/openid-connect-rpinitiated-1_0.html) specification that allows clients to initiate a logout through a browser redirect. This would:

1. Allow the server to clear browser session state
2. Support single logout across multiple clients
3. Give visual feedback to the user about the logout process

However, this approach requires a browser redirect which may not be desirable for all clients, especially mobile platforms.

## Security considerations

Token revocation is a critical security feature that allows users to terminate access when needed. Some key security aspects:

- Servers must revoke both the access token and refresh token when either is revoked
- The server should consider revoking other related sessions, like browser cookie sessions used during authentication
- Revoking a token should be effective immediately, and not be usable for any further requests

[RFC7009]: https://tools.ietf.org/html/rfc7009
[MSC2965]: https://github.com/matrix-org/matrix-spec-proposals/pull/2965
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
[`/_matrix/client/v3/login`]: https://spec.matrix.org/v1.13/client-server-api/#login
[`/_matrix/client/v3/logout`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3logout
[`POST /_matrix/client/v3/logout/all`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3logoutall
[`DELETE /_matrix/client/v3/devices/{deviceId}`]: https://spec.matrix.org/v1.13/client-server-api/#delete_matrixclientv3devicesdeviceid
[`POST /_matrix/client/v3/delete_devices`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3delete_devices
