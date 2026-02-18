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


### Rendering the space hierarchy before joining
  1. Client may have an alias of space room.
  2. Client need to get `roomId` and `via` using [/directory/room/roomAlias](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv3directoryroomroomalias)
  3. Client renders [/hierarchy](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy) with `roomId` and `via` params found by previous step.

### Rendering subspaces hierarchy independently
  1. Client have data about subspaces. i.e `m.space.child` state events of parent space
     1. If parent space is joined, `m.space.child` is retrievable from room state maintained by client.
     2. If parent space is fetched using [/hierarchy](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy), `m.space.child` is
        retrievable from `children_state` of [/hierarchy](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy) response.
  2. Client can get `roomId` from `m.space.child` event's `state_key` and `via` from the content.
  3. Client renders [/hierarchy](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv1roomsroomidhierarchy) using `roomId` and `via` found by previous step.
  4. Client can iterate the same procedure for child subspaces.


## Potential issues
Unknown

## Alternative
Unknown

## Security considerations
Unknown

## Unstable prefix
Until this proposal is accepted into the spec, implementations SHOULD refer to via as `org.matrix.msc4235.via`.
