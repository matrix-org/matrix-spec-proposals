# MSC4367: `via` routes in the published room directory

The [published room directory] allows clients to discover rooms on their own or other homeservers.
Naturally, clients will want to join rooms found in the directory which requires knowledge of a
resident server to facilitate the join. The spec doesn't make it clear how to find such a server,
however.

To begin with, it is unclear whether the endpoints for listing a server's directory may return rooms
that the server is not joined to. Additionally, there is no recommendation on what `via` parameter
clients should use when attempting to join rooms found in the directory. As a result, clients can
end up browsing published rooms without being able to join them.[^1]

This proposal addresses the situation by adding `via` values in the room directory responses.

## Proposal

Servers MAY include rooms that they are not joined to in responses returned by the following
endpoints:

- [`GET  /_matrix/client/v3/publicRooms`]
- [`POST /_matrix/client/v3/publicRooms`]
- [`GET  /_matrix/federation/v1/publicRooms`]
- [`POST /_matrix/federation/v1/publicRooms`]

To help clients join such rooms, a new required property `via` is added on the `PublishedRoomsChunk`
returned by the above endpoints.

``` json5
{
  "chunk": [
    {
      "avatar_url": "mxc://bleecker.street/CHEDDARandBRIE",
      "room_id": "!ol19s:bleecker.street",
      "via": [ "bleecker.street" ],
      ...
    }
  ]
}
```

Servers MUST populate `via` with at least one resident server of the room or, if they cannot
determine any, omit the room from their response.

Clients SHOULD include the values provided in `via` when subsequently joining rooms with
[`POST /_matrix/client/v3/join/{roomIdOrAlias}`].

Together, the changes above increase the chances that clients can actually join rooms found in the
directory.

## Potential issues

None.

## Alternatives

[MSC4366] deals with the same problem by forbidding unroutable rooms from the local directory. This
is only a partial solution, however.

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable, `via` should be referred to as `org.matrix.msc4367.via`.

## Dependencies

None.

[^1]: These issues were initially raised in <https://github.com/matrix-org/matrix-spec/issues/1375>.

  [published room directory]: https://spec.matrix.org/v1.16/client-server-api/#published-room-directory
  [`GET  /_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3publicrooms
  [`POST /_matrix/client/v3/publicRooms`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3publicrooms
  [`GET  /_matrix/federation/v1/publicRooms`]: https://spec.matrix.org/v1.16/server-server-api/#get_matrixfederationv1publicrooms
  [`POST /_matrix/federation/v1/publicRooms`]: https://spec.matrix.org/v1.16/server-server-api/#post_matrixfederationv1publicrooms
  [`POST /_matrix/client/v3/join/{roomIdOrAlias}`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3joinroomidoralias
  [MSC4366]: https://github.com/matrix-org/matrix-spec-proposals/pull/4366
