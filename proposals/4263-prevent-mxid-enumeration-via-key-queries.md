# MSC4263: Preventing MXID enumeration via key queries

The client-server API allows searching users and querying their profiles via
[`/_matrix/client/v3/user_directory/search`] and
[`/_matrix/client/v3/profile/{userId}`], respectively. Both of these APIs can
among others be abused to enumerate MXIDs. Servers are, therefore, only required
to return results for users who either share a room with the requesting user or
are a member of a public room known to the server. In all other cases,
homeservers can respond with 403 or simply omit the user from the response.

Similarly, on the server-server API, servers are generally permitted to deny
requests to [`/_matrix/federation/v1/query/profile`] with 403.

The [`/_matrix/client/v3/keys/query`] and
[`/_matrix/federation/v1/user/keys/query`] endpoints have a similar problem but
do not currently permit server admins to restrict their responses to conceal
users.

This proposal carries the behaviour of the user directory and profile APIs over
to the key query APIs.

## Proposal

When processing [`/_matrix/client/v3/keys/query`] requests, homeservers MUST at
a minimum consider users who share a room with the requesting user or are a
member of a public room. This is regardless of the concrete membership value of
the queried users in those room.

In all other cases, homeservers MAY ignore the queried MXIDs and omit them from
the response.

Servers MAY deny key queries over federation by responding with 403 and an error
code of `M_FORBIDDEN` on [`/_matrix/federation/v1/user/keys/query`].

## Potential issues

None.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.

  [`/_matrix/client/v3/user_directory/search`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3user_directorysearch
  [`/_matrix/client/v3/profile/{userId}`]: https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv3profileuserid
  [`/_matrix/federation/v1/query/profile`]: https://spec.matrix.org/v1.13/server-server-api/#get_matrixfederationv1queryprofile
  [`/_matrix/client/v3/keys/query`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3keysquery
  [`/_matrix/federation/v1/user/keys/query`]: https://spec.matrix.org/v1.13/server-server-api/#post_matrixfederationv1userkeysquery
