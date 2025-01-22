# MSC4235: `via` query param for /hierarchy endpoint

To request the hierarchy of a space, clients need to call the
[/hierarchy](https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientv1roomsroomidhierarchy) endpoint. This
endpoint does not require user to join the room before responding with hierarchy details. It instead check whether the
room is potentially joinable (per [MSC3173](https://github.com/matrix-org/matrix-spec-proposals/pull/3173)) before
responding.

Because it does not require a space room to be joined before calling this endpoint, it's possible that the requested
room may not be locally available on the server. The server might need to request information over federation to
respond. In such a case, this endpoint doesn't provide a mechanism for the client to specify the server name from which
the server should request information.

## Proposal

The [/hierarchy](https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientv1roomsroomidhierarchy) endpoint should
include `via` as query parameter which server can use in case requested room in not locally available on the server.

This change will stabilize the endpoint and allows clients to use this endpoint in more efficient manner, like: 
1. Requesting the only part of sub-spaces hierarchy which is unknown the the client.
2. Rendering the preview of space and it's children before joining the space.
3. Since depth-first hierarchy responses can be costly, especially when reaching the end of the hierarchy, clients can
   optimize the process by loading subspaces independently. This approach can improve efficiency by loading the
   hierarchy of individual subspaces only when the user views them.

## Potential issues
Unknown

## Alternative
Unknown

## Security considerations
Unknown

## Unstable prefix
None
