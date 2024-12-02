# MSCXXXX: `server_name` query param for /hierarchy endpoint

To request the hierarchy of a space, clients need to call the
[/hierarchy](https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientv1roomsroomidhierarchy) endpoint. This
endpoint does not require user to join the room before responding with hierarchy details. It instead check whether the
room is potentially joinable (per [MSC3173](https://github.com/matrix-org/matrix-spec-proposals/pull/3173)) before
responding.

Because it doesn't not require space room to be joined before calling this endpoint, It is possible that the requested
room is not locally available on the server and server need to request over federation to respond. In that case this
endpoint does not provide client to express the server name's which server need to request over federation. 

## Proposal

The [/hierarchy](https://spec.matrix.org/v1.9/client-server-api/#get_matrixclientv1roomsroomidhierarchy) endpoint should
include `server_name` as query parameter which server can use in case requested room in not locally available on the
server.

Following change will allow clients to use this endpoint in more efficient manner, like: 
1. Requesting the only part of sub-spaces hierarchy which is unknown the the client.
2. Rendering the preview of space and it's children before joining the space.
3. Since server does not respect [order](https://spec.matrix.org/v1.9/client-server-api/#mspacechild) of the children in
   response, client can divide the work of loading child spaces and figuring out order and re-ordering instead of
   relying on the long paginated response for those action.

## Potential issues
Unknown

## Alternative
Unknown

## Security considerations
Unknown

## Unstable prefix
None