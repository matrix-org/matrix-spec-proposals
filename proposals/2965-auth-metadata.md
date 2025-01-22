# MSC2965: OAuth 2.0 Authorization Server Metadata discovery

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC][MSC3861].

To be able to initiate an OAuth 2.0 login flow to use a Matrix server, the client needs to know the authorization server metadata, as defined in [RFC8414].

## Proposal

This introduces a new Client-Server API endpoint to discover the authorization server metadata used by the homeserver.

### `GET /auth_metadata`

A request on this endpoint should return a JSON object containing the authorization server metadata as defined in [RFC8414].
This endpoint does *not* require authentication, and MAY be rate limited per usual. 

For example:

```http
GET /_matrix/client/v1/auth_metadata
Host: example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: public, max-age=3600
```

```json
{
  "authorization_endpoint": "https://account.example.com/oauth2/auth",
  "token_endpoint": "https://account.example.com/oauth2/token",
  "registration_endpoint": "https://account.example.com/oauth2/clients/register",
  "revocation_endpoint": "https://account.example.com/oauth2/revoke",
  "jwks_uri": "https://account.example.com/oauth2/keys",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "response_modes_supported": ["query", "fragment"],
  "code_challenge_methods_supported": ["S256"],
  "...": "some fields omitted"
}
```

**Note**: The fields required for the main flow outlined by [MSC3861] and its sub-proposals are:

 - `authorization_endpoint` ([MSC2964])
 - `token_endpoint` ([MSC2964])
 - `revocation_endpoint` ([MSC4254])
 - `registration_endpoint` ([MSC2966])
 - `response_types_supported` including the value `code` ([MSC2964])
 - `grant_types_supported` including the values `authorization_code` and `refresh_token` ([MSC2964])
 - `response_modes_supported` including the values `query` and `fragment` ([MSC2964])
 - `code_challenge_methods_supported` including the value `S256` ([MSC2964])

See individual proposals for more details on each field.

### Fallback

If the homeserver does not offer next-generation authentication as described in [MSC3861], this endpoint should return a 404 with the `M_UNRECOGNIZED` error code.

In this case, clients should fall back to using the User-Interactive Authentication flows instead to authenticate the user.

## Potential issues

The authorization server metadata is relatively large and may change over time. The client should:

- Cache the metadata appropriately based on HTTP caching headers
- Refetch the metadata if it is stale

## Alternatives

### Discovery via OpenID Connect Discovery

Instead of directly exposing the metadata through a Client-Server API endpoint, the homeserver could expose only the issuer URL and let clients discover the metadata using OpenID Connect Discovery.

In this approach, a new endpoint `/_matrix/client/v1/auth_issuer` would return just the issuer URL:

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

The Matrix client would then discover the OpenID Connect Provider configuration by using [OpenID Connect Discovery].

The downside of this approach is that it requires an extra roundtrip to get the metadata.
It also introduces a dependency on an OpenID Connect specification: [MSC3861] proposals tries to build on OAuth 2.0/IETF standards as much as possible.

### Discovery via [RFC8414] well-known endpoint

[RFC8414] OAuth 2.0 Authorization Server Metadata already defines a standard well-known endpoint, under `.well-known/oauth-authorization-server`.
However, the RFC states that an application leveraging this standard should define its own application-specific endpoint, e.g. `/.well-known/matrix-authorization-server`, and *not* use the `.well-known/oauth-authorization-server` endpoint.
To avoid confusion with the existing `.well-known/matrix/*` documents, this proposal suggests defining a new C-S API endpoint instead.

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

- the `.well-known/webfinger` resource is dynamic, which can be harder to host/delegate & might conflict with other services leveraging it like Mastodon
- this does not cover discovering the authentication server for user registration

## Security considerations

None relevant.

## Unstable prefix

While this MSC is not in a released version of the specification,
clients should use the `org.matrix.msc2965` unstable prefix for the endpoint,
e.g. `GET /_matrix/client/unstable/org.matrix.msc2965/auth_metadata`.

[RFC8414]: https://tools.ietf.org/html/rfc8414
[MSC2964]: https://github.com/matrix-org/matrix-spec-proposals/pull/2964
[MSC2966]: https://github.com/matrix-org/matrix-spec-proposals/pull/2966
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
[MSC4254]: https://github.com/matrix-org/matrix-spec-proposals/pull/4254
[OpenID Connect Discovery]: https://openid.net/specs/openid-connect-discovery-1_0.html
