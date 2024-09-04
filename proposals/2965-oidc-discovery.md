# MSC2965: Usage of OpenID Connect Discovery for authentication server metadata discovery

This proposal is part of the broader [MSC3861: Next-generation auth for Matrix, based on OAuth 2.0/OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/3861).

To be able to initiate an OAuth 2.0 login flow to use a Matrix server, the client needs to know the location of the authentication server in use.

## Proposal

This introduces a new Client-Server API endpoint to discover the authentication server used by the homeserver.
It also introduces new OpenID Connect Provider metadata to allow clients to deep-link to the account management capabilities of the authentication server.

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

```json5
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
  "account_management_uri": "https://account.example.com/myaccount",
  "account_management_actions_supported": ["org.matrix.profile", "org.matrix.sessions_list", 
                                           "org.matrix.session_view", "org.matrix.session_end"],
  // some fields omitted
}
```

### Account management deep-linking

This also adds the capability to deep-link to the account management capabilities of the authentication server.
To do so, OpenID Connect Providers advertise a URL where the user is able to access the account management capabilities of the OpenID Connect Provider, as well as a list of actions that the URL supports.
The client can then redirect their user to this URL to perform account management actions.

#### Possible actions

The following actions are defined by this MSC:

- `org.matrix.profile` - The user wishes to view their profile (name, avatar, contact details).
- `org.matrix.sessions_list` - The user wishes to view a list of their sessions.
- `org.matrix.session_view` - The user wishes to view the details of a specific session.
- `org.matrix.session_end` - The user wishes to end/logout a specific session.
- `org.matrix.account_deactivate` - The user wishes to deactivate their account.
- `org.matrix.cross_signing_reset` - The user wishes to reset their cross-signing keys.

Subsequent MSCs may extend this list.

#### OpenID Connect Provider metadata

In the OpenID Connect Provider metadata, the following fields are added:

- `account_management_uri`: the URL where the user is able to access the account management capabilities of the OpenID Connect Provider
- `account_management_actions_supported`: a JSON array of actions that the account management URL supports

Note that the intent of this proposal is to potentially end up in a standard OpenID Connect specifications, or at least formally registered in the [IANA Registry for Server Metadata](https://www.iana.org/assignments/oauth-parameters/oauth-parameters.xhtml#authorization-server-metadata).
This is why the metadata fields are not prefixed with `org.matrix.`, as this proposal can make sense outside of Matrix, but the actions themselves are.

#### Account management URL parameters

The account management URL may accept the following additional query parameters:

- `id_token_hint` - An ID Token that was previously issued to the client; the issuer uses it as a hint for which user is requesting to manage their account.
  If the requesting user is not logged in then it is used as a login hint; if a different user/identity is already logged in then warn the user that they are accessing a different account.
- `action` - Can be used to indicate the action that the user wishes to take, as defined above.
- `device_id` - This can be used to identify a particular session for `session_view` and `session_end`. This is the Matrix device ID.

For example, if a user wishes to sign out a session for the device `ABCDEFGH` where the advertised account management URL was `https://account.example.com/myaccount` the client could open a link to `https://account.example.com/myaccount?action=org.matrix.session_end&device_id=ABCDEFGH`.

Not all actions need to be supported by the account management URL, and the client should only use the actions advertised in the `account_management_actions_supported` server metadata field.

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

### Account management URL

There is no current OIDC standard for account management URLs.
If one gets defined, this proposal could be extended to use it instead of defining a new one.

## Security considerations

None relevant.

## Unstable prefix

While this MSC is not in a released version of the specification,
clients should use the `org.matrix.msc2965` unstable prefix for the endpoint,
e.g. `GET /_matrix/client/unstable/org.matrix.msc2965/auth_issuer`.
