# MSC2965: Usage of OpenID Connect Discovery for authentication server metadata discovery

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/3861).

To be able to initiate an OAuth 2.0 login flow to use a Matrix server, the client needs to know the location of the authentication server in use.

## Proposal

This introduces a new Client-Server API endpoint to discover the authentication server used by the homeserver.

### `GET /auth_issuer`

A request on this endpoint should return a JSON object with one field:

- _REQUIRED_ `issuer`: the OpenID Connect Provider that is trusted by the homeserver

For example:

```http
GET /_matrix/client/v1/auth_issuer
Host: example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "issuer": "https://account.example.com/"
}
```

The Matrix client can then discover the OpenID Connect Provider configuration by using [OpenID Connect Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html).

```http
GET /.well-known/openid-configuration
Host: account.example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "issuer": "https://account.example.com/",
  "authorization_endpoint": "https://account.example.com/oauth2/auth",
  "token_endpoint": "https://account.example.com/oauth2/token",
  "registration_endpoint": "https://account.example.com/oauth2/clients/register",
  "end_session_endpoint": "https://account.example.com/oauth2/logout",
  "jwks_uri": "https://account.example.com/oauth2/keys",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "response_mode_supported": ["query", "fragment"],
  "...": "some fields omitted"
}
```

## Potential issues

Using a separate endpoint for discovery makes the request chain to initiate a login flow longer.
A full discovery flow would be as follows:

- `GET [domain]/.well-known/matrix/client` to discover the homeserver
- `GET [homeserver]/_matrix/client/v1/auth_issuer` to discover the issuer
- `GET [issuer]/.well-known/openid-configuration` to discover the OpenID Connect Provider configuration
- `POST [issuer client registration endpoint]` to register the OAuth 2.0 client
  (see [MSC2966](https://github.com/matrix-org/matrix-spec-proposals/pull/2966))
- Redirect to `[issuer authorization endpoint]` to initiate the login flow

## Alternatives

The authentication server discovery could be done by other mechanisms.

### Discovery via [RFC8414](https://tools.ietf.org/html/rfc8414)

[RFC8414](https://tools.ietf.org/html/rfc8414): OAuth 2.0 Authorization Server Metadata is a standard similar to OpenID Connect Discovery.
The main differences is that the well-known endpoint is under `.well-known/oauth-authorization-server` and this standard is defined by the IETF and not the OpenID Foundation.

### Discovery via the well-known client discovery

A previous version of this proposal suggested using the well-known client discovery mechanism to discover the authentication server.
Clients already discover the homeserver when doing a server discovery via the well-known document.

A new `m.authentication` field is added to this document to support OpenID Connect Provider (OP) discovery.
It is an object containing two fields:

- REQUIRED `issuer` - the OpenID Connect Provider that is trusted by the homeserver
- OPTIONAL `account` - the URL where the user is able to access the account management capabilities of the OpenID Connect Provider

For example:

```http
GET /.well-known/matrix/client
Host: example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "m.homeserver": {
    "base_url": "https://matrix-client.example.com"
  },
  "m.identity_server": {
    "base_url": "https://identity.example.com"
  },
  "m.authentication": {
    "issuer": "https://account.example.com",
    "account": "https://account.example.com/myaccount"
  }
}
```

This proposal, although implemented in some clients and in Synapse, has the downside of making the well-known discovery mandatory.
When implemented in clients, in many circumstances it was hard to go back and use well-known discovery, as they may already know the homeserver URL.
Since the authentication server is always tightly coupled to the homeserver (as opposed to the identity server), it makes sense to discover it via a Client-Server API endpoint.

The account management URL was also part of this proposal, but it was moved to the OpenID Connect Provider metadata because it makes more sense for the provider to advertise it, and not the homeserver.

### Discovery via the `m.login.oauth2` authentication method

The spec already defines a `m.login.oauth2` authentication method, but it was never implemented.
The downside of this approach is that the plan is to deprecate the old login mechanism and it does not make sense to keep it just to discover the issuer.

### Discovery via WebFinger

OIDC already has a standard way to discover OP from an identifier: WebFinger.
This is already adopted by Mastodon, and might help solve logging in via 3PIDs like emails.

Sample exchange:

```
GET /.well-known/webfinger?
    resource= mxid:@john:example.com &
    rel= http://openid.net/specs/connect/1.0/issuer
Host: example.com
```

```json
{
  "subject": "mxid:@john:matrix.org",
  "links": [
    {
      "rel": "http://openid.net/specs/connect/1.0/issuer",
      "href": "https://account.example.com"
    }
  ]
}
```

The `mxid` scheme is a bit arbitrary here.
The parameters in the URL should be percent-encoded, this was left unencoded for clarity.

The benefits of this approach are that it is standard and decouples the authentication server from the Matrix server:
different authentication servers could be used by different accounts on the server.

The downsides of this approach are:

- the `.well-known` resource is dynamic, which can be harder to host/delegate & might conflict with other services like Mastodon
- this does not cover discovering the authentication server for user registration

## Security considerations

None relevant.

## Unstable prefix

While this MSC is not in a released version of the specification,
clients should use the `org.matrix.msc2965` unstable prefix for the endpoint,
e.g. `GET /_matrix/client/unstable/org.matrix.msc2965/auth_issuer`.
