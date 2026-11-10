# MSC4502: Targeted and unrestricted room member queries

Matrix allows users to query room members via either [/rooms/{roomId}/joined_members] or
[/rooms/{roomId}/members]. Both endpoints require the user to be joined to the room themselves. In
some cases though, users can have a legitimate reason to query room members for rooms that they are
not joined to. This can, for instance, apply to admin users or to privileged application services
such as moderation tooling.

Another problem of the existing endpoints is that they require loading all members. This is wasteful
in cases where only a specific user's or server's membership in a room is required.

The present proposal addresses these issues by introducing a new endpoint for querying a single
subject's membership in a room and guarding the endpoint behind a dedicated OAuth scope token
available to both users and application services.

## Proposal

A new Client-Server endpoint `GET /_matrix/client/v3/rooms/{roomId}/is_joined` is introduced. The
endpoint accepts the following query parameters:

- `mxid` (string): A [user identifier].
- `server_name` (string): A [server name].

Exactly one of these parameters can be supplied at the same time. If both or none are given, the
server MUST respond with HTTP 400 / `M_MISSING_PARAM`. If either `roomId`, `mxid` or `server_name`
contain invalid values, the server MUST respond with HTTP 400 / `M_INVALID_PARAM`.

If all parameters are valid, the server checks whether the supplied user identifier or server name
is joined to the room and returns the following response:

``` json5
{
  "joined": true
}
```

- `joined` (required, boolean): `true` if the subject is joined to the room. `false` otherwise
  including when the server cannot verify membership because it doesn't know the subject or the
  room.

Access to the endpoint is guarded by a new OAuth scope token `urn:matrix:client:rooms:is_joined`.
Usage of this scope SHOULD be reserved to admins and application services.

In order for application services to request the scope, a new optional property `scopes` is added at
the top level of the service [registration file]. `scopes` is an array of strings.

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
scopes: [ "urn:matrix:client:rooms:is_joined" ]
```

## Potential issues

The server will only be able to determine room membership for rooms that the server itself is joined
to. Depending on the use case, this property might be sufficient but callers of the new endpoint
should be aware of its limitations.

## Alternatives

Application services have the ability to [masquerade] as a local user when making requests to the
Client-Server API. This mechanism could be used to verify a local user's membership in a room. It
doesn't help when the service needs to verify a remote user's room membership, however.

## Security considerations

The `urn:matrix:client:rooms:is_joined` scope allows bearers to query room memberships for any room
known to the homeserver. This is a significant level of privilege that could be abused. Server
administrators should carefully evaluate whom to grant the scope to.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
|----|----|----|
| `/_matrix/client/v3/rooms/{roomId}/is_joined` | Endpoint | `/_matrix/client/unstable/io.element.msc4502/rooms/{roomId}/is_joined` |
| `urn:matrix:client:rooms:is_joined` | Scope token | `urn:matrix:client:io.element.msc4502:rooms:is_joined` |
| `scopes` | Registration file property | `io.element.msc4502.scopes` |

Servers may advertise support for the unstable feature by setting `io.element.msc4502` to `true` in
the `unstable_features` map in the response to `GET /_matrix/client/versions`.

``` json
{
    "versions": ["..."],
    "unstable_features": {
        "io.element.msc4502": true
    }
}
```

Once this MSC is accepted, but before the server advertises the spec version that includes the MSC,
the server may advertise `io.element.msc4502.stable` as an unstable feature flag to let clients know
that they can use the stable identifiers.

## Dependencies

None.

  [/rooms/{roomId}/joined_members]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3roomsroomidjoined_members
  [/rooms/{roomId}/members]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3roomsroomidmembers
  [user identifier]: https://spec.matrix.org/v1.19/appendices/#user-identifiers
  [server name]: https://spec.matrix.org/v1.19/appendices/#server-name
  [registration file]: https://spec.matrix.org/v1.18/application-service-api/#registration
  [masquerade]: https://spec.matrix.org/v1.18/application-service-api/#identity-assertion
