# MSC4254: Usage of [RFC7009] Token Revocation for Matrix client logout

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC][MSC3861].

This MSC specifies how Matrix clients should use OAuth 2.0 Token Revocation as defined in [RFC7009] to implement client logout.

## Proposal

### Prerequisites

This proposal requires the client to know the following authorization server metadata about the homeserver:

- `revocation_endpoint`: the URL where the client is able to revoke tokens

The discovery of the above metadata is out of scope for this MSC, and is currently covered by [MSC2965].

### Token revocation

When a user wants to log out from a client, the client should revoke either its access token or refresh token by making a POST request to the revocation endpoint as described in [RFC7009].

The server must revoke both the access token and refresh token associated with the token provided in the request.

The request includes:
- The `token` parameter containing either the access token or refresh token to revoke
- Optionally, the `token_type_hint` parameter, with either the `access_token` or `refresh_token` value. If provided, the server can use this value to determine the kind of token which was provided in the request
- The `client_id` obtained during client registration

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

The server may return an error response as defined in [RFC7009]. The client should handle these errors appropriately:

- If the token is already revoked, the server returns a 200 OK response
- If the client is not authorized to revoke the token, the server returns a 401 Unauthorized response
- For other errors, the server returns a 400 Bad Request response with error details

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
