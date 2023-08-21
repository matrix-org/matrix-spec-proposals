# MSC2965: OIDC Provider discovery

This proposal is part of the broader [MSC3861: Matrix architecture change to delegate authentication via OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/3861).

To be able to initiate an OAuth 2.0 login flow to use a Matrix server, the client needs to know the location of the authentication server in use.

## Proposal

Clients already discover the homeserver when doing a server discovery via the well-known document.

A new `m.authentication` field is added to this document to support OIDC Provider discovery.
It is an object containing two fields:

- REQUIRED `issuer` - the OIDC Provider that is trusted by the homeserver
- OPTIONAL `account` - the URL where the user is able to access the account management capabilities of the OIDC Provider

For example:

```
GET /.well-known/matrix/client
Host: example.com
Accept: application/json
```

```
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

The authentication server metadata can then be discovered by the client using [OpenID Connect Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) against the `issuer` field.

```
GET /.well-known/openid-configuration
Host: account.example.com
Accept: application/json
```

```
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "issuer": "https://account.example.com/",
  "authorization_endpoint": "https://account.example.com/oauth2/auth",
  "token_endpoint": "https://account.example.com/oauth2/token",
  "registration_endpoint": "https://account.example.com/oauth2/clients/register",
  "end_session_edntpoint": "https://account.example.com/oauth2/logout",
  "jwks_uri": "https://account.example.com/.well-known/jwks.json",
  "response_types_supported": ["code"],
  "grant_types_sypported": ["authorization_code", "refresh_token"],
  "response_mode_sypported": ["query", "fragment"],
  "//": "some fields omitted"
}
```

The account management URL may accept the following additional query parameters:

- RECOMMENDED `id_token_hint` - ID Token (as previously issued by the issuer to the client) as a hint about the current authenticated user that is requesting to be able to manage their account. This may be used by the issuer to: if not logged in then used as a login hint; if already logged in, but for a different user/identity then warn the user that they are accessing account.


## Potential issues

Not all Matrix servers have the well-known client discovery mechanism setup.
Unlike the identity server, the authentication server is necessary to login against a Matrix server.
Being unable to discover the authorization server from the Matrix Client API might be an issue in some cases.

## Alternatives

The authorization server discovery could be done by other mechanisms.

### Discovery via a new client API endpoint

The Matrix Client API could have a new endpoint to discover the issuer, e.g. `/_matrix/client/r0/auth_issuer`.

### Discovery via the `m.login.oauth2` authentication method

The spec already defines a `m.login.oauth2` authentication method, but it was never implemented.
The downside of this approach is that the plan is to deprecate the old login mechanism and it does not make sense to keep it just to discover the issuer.

### Discovery via WebFinger

OIDC already has a standard way to discover OP from an identifier: WebFinger. This is already adopted by Mastodon, and might help solving logging in via 3PIDs like emails.

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

The benefits of this approach are that it is standard and decouples the authentication server from the Matrix server: different authentication servers could be used by accounts on the server.

The downsides of this approach are:

- the `.well-known` resource is dynamic, which can be harder to host/delegate & might conflict with other services like Mastodon
- this does not cover discovering the authentication server for user registration

### Account management URL

There is no standard in OIDC for the `account` field. If one was to be standardised in future then it would make sense to use that instead.

## Security considerations

None relevant.

## Unstable prefix

While this MSC is not in a released version of the specification, clients should use the `org.matrix.msc2965.authentication` field in the client well-known discovery document instead of `m.authentication`.
