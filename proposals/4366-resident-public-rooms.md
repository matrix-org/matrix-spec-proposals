# MSC4366: Resident servers in and around the room directory

The [published room directory] allows clients to discover rooms on their own or other homeservers.
Naturally, clients will want to join rooms found in the directory which requires knowledge of a
resident server to facilitate the join. The spec doesn't make it clear how to find such a server,
however.

To begin with, it is unclear whether the endpoints for listing a server's directory may return rooms
that the server is not joined to. Additionally, there is no recommendation on what `via` parameter
clients should use when attempting to join rooms found in the directory. As a result, clients can
end up browsing published rooms without being able to join them.[^1]

This proposal addresses the situation by forbidding non-resident rooms in local directory queries
and matching the `server` and `via` query parameters.

## Proposal

When either of the client-server endpoints

- [`GET  /_matrix/client/v3/publicRooms`]
- [`POST /_matrix/client/v3/publicRooms`]

is called with an empty or missing `server` parameter, the server MUST only return rooms listed on
its directory that it has at least one joined member in.

Similarly, the server-server endpoints

- [`GET  /_matrix/federation/v1/publicRooms`]
- [`POST /_matrix/federation/v1/publicRooms`]

MUST only include rooms from the server's local directory if the server has at least one joined
member in them.

Clients that use the `server` parameter on room directory queries and subsequently call
[`POST /_matrix/client/v3/join/{roomIdOrAlias}`] to join a room found in the response, SHOULD
include the same server name in the `via` parameter.

Together, the changes above increase the chances that clients can actually join rooms found in the
directory.

## Potential issues

As per the current [spec], the server-server endpoints are discouraged but not banned from including
rooms listed on *other* homeserver's directories. A client querying `/publicRooms` with a specific
`server` may, therefore, still receive rooms which that server isn't joined to. Matching the
`server` and `via` parameters as described in this proposal would still not allow clients to join
these rooms. This problem already exists today, however, and is deemed out of scope for this
proposal.

## Alternatives

Non-resident rooms could be allowed in room directory responses if the server would accompany them
with suitable `via` values. This approach is covered in [MSC4367].

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.

[^1]: These issues were initially raised in <https://github.com/matrix-org/matrix-spec/issues/1375>.

  [published room directory]: https://spec.matrix.org/v1.16/client-server-api/#published-room-directory
  [`GET  /_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3publicrooms
  [`POST /_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3publicrooms
  [`GET  /_matrix/federation/v1/publicRooms`]: https://spec.matrix.org/v1.16/server-server-api/#get_matrixfederationv1publicrooms
  [`POST /_matrix/federation/v1/publicRooms`]: https://spec.matrix.org/v1.16/server-server-api/#post_matrixfederationv1publicrooms
  [`POST /_matrix/client/v3/join/{roomIdOrAlias}`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3joinroomidoralias
  [spec]: https://spec.matrix.org/v1.16/server-server-api/#published-room-directory
  [MSC4367]: https://github.com/matrix-org/matrix-spec-proposals/pull/4367
