# MSC2967: API scope restriction

When a user signs in with a Matrix client, it currently gives this client full access to their Matrix account.

This proposal introduces access scopes to allow restricting client access to only part(s) of the Matrix client API.

## Proposal

[MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) introduces the usage of OAuth 2.0 for a client to authenticate against a Matrix homeserver.

OAuth 2.0 grants have scopes associated to them and provides a framework for obtaining user consent.

The framework encourages the practise of obtaining additional use consent when a client asks for a new scope that was not granted previously.

This MSC does not attempt to define all the scopes necessary to cover all Matrix APIs and use cases, but proposes the structure of a namespace and some specific scopes to cover existing use cases.

Additionally it is proposed that a standard approach to error response representation is adopted across the API. This could replace the UIA based responses that exist on some API endpoints today.

### Scope format

All scopes related to Matrix should start with `urn:matrix:`.

Calls to the Matrix client API, excluding calls that need UIA, must be restricted by scopes prefixed by `urn:matrix:api:`.
Calls to endpoints that currently need User-Interactive Authentication (UIA) must be restricted by scopes prefixed by `urn:matrix:sudo:`.

Protected resource can have both `read` and `write` operations.
`write` access to a resource implies `read` access to it.
Access to those operations are specified as the scope suffix, e.g. `urn:matrix:api:[resource]:read`.

#### Globs

Scopes used by the Matrix client API support wildcard globs.
`urn:matrix:api:*` gives full access to the API (excluding UIA).
`urn:matrix:api:*:read` gives read-only access to the API.
Access to the `urn:matrix:sudo:*` can be time-restricted and require user re-authentication for sensitive operations.

Top-level wildcards (`urn:matrix:*` or `*`) are not valid and must be rejected by the authentication server.
Wildcards can only replace URN segments, e.g. `urn:matrix:a*` is invalid.

#### Device handling

With the pre-MSC2964 authentication mechanism, a `device_id` was associated with a specific access token. In OAuth 2.0 there is no such thing as a session and so a mapping cannot be handled using the same mechanism.

MSC2964 proposes that the client is responsible for generating/allocating a `device_id`. A client can adopt and rehydrate an existing client by asking for its scope on login.

The client can then bind the `device_id` to the grant by requesting a scope with the format: `urn:matrix:device:<device_id>`.

This also has a nice side-effect: if the device asked was never used by the client making the request, the authorization server will ask for explicit consent from the user.

The authentication server must only grant exactly one device scope for a token.

Wildcards are not allowed under the `urn:matrix:device:` prefix.

### Exact scopes

Exact scopes for the whole API are intentionally not specified in this MSC.

The glob mechanism allows to the existing behaviour during a transition period while allowing further MSCs that introduces those exact scopes.

### Insufficient privilege response

It is proposed that a [RFC6750](https://datatracker.ietf.org/doc/html/rfc6750) formatted `WWW-Authenticate` response header is used to provide feedback to the client with `error="insufficent_scope"`.

```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="insufficient_scope", scope="urn:matrix:api:something"
```

On receipt of such a response the client can then request a new authorization from the issuer as per [MSC2964](https://github.com/matrix-org/matrix-doc/pull/2964) requesting the additional scope be granted.

For non-UIA API endpoints the rest of the response would be as per the [standard error respponse](https://spec.matrix.org/v1.2/client-server-api/#standard-error-response) spec.

For example:

```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="insufficient_scope", scope="urn:matrix:api:something"
Content-Type: application/json

{
  "errcode": "M_FORBIDDEN",
  "error": "Insufficient privilege"
}
```

## Potential issues

The Device ID handling involves some custom logic on the authorization server side to handle the dynamic scope format.

The addition of the `WWW-Authenticate` header could cause issue with some clients.

## Alternatives

### Scopes
Scope format could also have an URL format, e.g. `https://matrix.org/api/*/read`.
The URL prefix could either be static (`https://matrix.org`) or dependant on the homeserver (`https://matrix.example.com`).
In both cases, the URL could be confused with API endpoints and in the second case it would require discovery to know what scopes to ask.

The actual prefix as well as the `:api:`, `:sudo:` and `:device:` URN parts are open to debate.

### Insufficient privilege response
The [standard error response](https://spec.matrix.org/v1.2/client-server-api/#standard-error-response) could be used, however this wouldn't work on UIA endpoints which already have a different format response.

A custom HTTP header could be used instead.

## Security considerations

TBD

## Unstable prefix

None relevant.
