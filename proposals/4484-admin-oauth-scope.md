# MSC4484: Server Administration OAuth Scope

Since Matrix 1.18, the [Server Administration](https://spec.matrix.org/v1.18/client-server-api/#server-administration)
API module has provided homeserver-agnostic endpoints to manage suspending and locking user accounts. These endpoints
are prescribed to be accessible to any user who is a "server admin", as defined by the server implementation
in question.

Since Matrix 1.16, [login via OAuth 2.0](https://spec.matrix.org/v1.18/client-server-api/#oauth-20-api) has
been supported and recommended as a replacement for the legacy user-interactive authentication API. OAuth
allows for fine-grained access control using scopes, but currently the Matrix specification only defines the
`urn:matrix:client:api:*` scope, which grants full access to the entire client-server API. Therefore, all OAuth
2.0 clients will be granted access to the endpoints in the Server Administration module by default, potentially
including more dangerous actions as this module is extended. This MSC improves these endpoints' security by
introducing a new OAuth scope that is REQUIRED for OAuth 2.0 clients to use administration endpoints, thereby
ensuring the user can give informed consent to clients that wish to perform administrative actions.

## Proposal

A new scope is added to the specification, which clients using OAuth MAY request:
`urn:matrix:client:api:server_administration` (herein referred to as "the scope" for brevity). Clients using OAuth
MUST request the scope to use any of the endpoints in the Server Administration module (all of which are currently
under the `/_matrix/client/*/admin/` path).

Currently those endpoints are:

- [`GET
/_matrix/client/v1/admin/lock/{userId}`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv1adminlockuserid)
- [`PUT
/_matrix/client/v1/admin/lock/{userId}`](https://spec.matrix.org/v1.18/client-server-api/#put_matrixclientv1adminlockuserid)
- [`GET
/_matrix/client/v1/admin/suspend/{userId}`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv1adminsuspenduserid)
- [`PUT
/_matrix/client/v1/admin/suspend/{userId}`](https://spec.matrix.org/v1.18/client-server-api/#put_matrixclientv1adminsuspenduserid)
- [`GET
/_matrix/client/v3/admin/whois/{userId}`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3adminwhoisuserid)

Requests to these endpoints from clients using OAuth that do not have the scope MUST fail with a `M_FORBIDDEN`
error code.

The `urn:matrix:client:api:*` scope SHALL NOT be required for requests to these endpoints.

The server MUST only grant the scope to clients that are authorizing on behalf of a server administrator, as
defined by the server. If the authorizing user is not a server administrator, the server MUST respond to the
authorization request or device authorization request (depending on the grant being used) with an `access_denied`
error, as described in [RFC 6749 § 4.1.2.1](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.2.1).

The server SHOULD, when a client requests the scope, indicate clearly to the user the dangers of granting a client
this scope in its grant confirmation webpage.

Clients intended for general-purpose use, as opposed to specifically administrative tasks, SHOULD NOT request the
scope during normal use. If the user wishes to perform an administrative action, clients SHOULD attempt to obtain
a new access token with the scope.

Clients using user-interactive authentication SHOULD be handled by the server as before. The server MAY restrict
administration endpoints to only clients using OAuth, and return a `M_FORBIDDEN` error code to clients using
user-interactive authentication.

## Potential issues

This MSC is explicitly not backwards-compatible. Existing clients using OAuth will no longer be able to use the
admin API endpoints unless and until they begin requesting the scope. To the best of the author's knowledge, there
are no clients in widespread use that support OAuth _and_ the Server Administration endpoints, and therefore the
impact of this change is currently minimal.

Currently there is no way for a client to determine if the authenticated user is a "server administrator" as defined
by the server, and therefore whether an attempt to obtain the scope will fail. Solutions to this issue are out of
scope for this MSC; for the time being it should be acceptable for clients to only attempt to obtain the scope if
they need it, and report an error to the user if they fail to obtain it.

## Alternatives

The status quo of allowing the Server Administration endpoints to be used by any client with the
`urn:matrix:client:api:*` scope could be upheld. The perspective of this proposal is that this is undesirable for
the reasons outlined above.

## Security considerations

Servers must be careful to prevent users who are not server administrators from obtaining an access token with
the scope. Servers that have a concept of "revoking" a user's administrator powers may wish to also revoke that
user's extant OAuth sessions that have the scope.

## Unstable prefix

While this proposal is unstable, clients and servers should use the
`urn:matrix:client:cc.c10y.msc4484.server_administration` scope instead of the
`urn:matrix:client:api:server_administration` scope. Servers may use the `org.continuwuity.msc4484.unstable`
unstable feature flag to indicate that clients using OAuth must request the unstable
`urn:matrix:client:cc.c10y.msc4484.server_administration` scope to use the Server Administration endpoints.
