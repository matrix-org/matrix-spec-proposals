# MSC4502: Unrestricted room member access for application services

Application services have the ability to [masquerade] as a local user when making requests to the
Client-Server API. This can, among others, be used to verify a user's membership in a room. This
only works for local users, however. In some cases an application service might need to verify that
a remote user is joined to a room known to the local homeserver.

One example for this is the Matrix RTC Authentication Service from [MSC4195: MatrixRTC Transport
Using LiveKit Backend]. A remote user hits this service to get access to a local user's RTC media
stream. A precondition for this is that both users share a room where a MatrixRTC session is
established. In order to verify this, the service needs to check if the remote user is actually
joined to that room.

This proposal extends the [Application Service API] with a new scope to permit services to look up
room memberships on any room known to the homeserver.

## Proposal

A new optional property `scopes` is added at the top level of the service [registration file].
`scopes` is an array of strings. The only permitted value is `unrestricted_member_access`.

``` yaml
id: "My Service"
url: null # No traffic required
as_token: "..."
hs_token: "..."
sender_localpart: "_my_service"
namespaces: # No namespaces required
  users: []
  aliases: []
  rooms: []
scopes: [ "unrestricted_member_access" ]
```

When an application service has the `unrestricted_member_access` scope, the homeserver MUST allow
the service to access [`GET /_matrix/client/v3/rooms/{roomId}/joined_members`] regardless of whether
the service's own user or any of the users in the service's namespaces is a member of the room.

## Potential issues

Application services that have the `unrestricted_member_access` scope won't be able to query joined
members of rooms that the homeserver isn't joined to.

## Alternatives

None apparent.

## Security considerations

The `unrestricted_member_access` scope gives an application service access to the room memberships
of every local user which is a significant level of privilege that could be abused by the service.
Homeservers and application services already have a high-trust relationship, however.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
|----|----|----|
| `scopes` | Registration file property | `org.matrix.msc4502.scopes` |
| `unrestricted_member_access` | Scope | `org.matrix.msc4502.unrestricted_member_access` |

## Dependencies

None.

  [masquerade]: https://spec.matrix.org/v1.18/application-service-api/#identity-assertion
  [MSC4195: MatrixRTC Transport Using LiveKit Backend]: https://github.com/matrix-org/matrix-spec-proposals/pull/4195
  [Application Service API]: https://spec.matrix.org/v1.18/application-service-api
  [registration file]: https://spec.matrix.org/v1.18/application-service-api/#registration
  [`GET /_matrix/client/v3/rooms/{roomId}/joined_members`]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3roomsroomidjoined_members
