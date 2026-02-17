# MSC4423: Undefine order of room directory

The room directory in Matrix is defined by the following endpoints:

* [`GET /_matrix/client/v3/publicRooms`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3publicrooms)
* [`POST /_matrix/client/v3/publicRooms`](https://spec.matrix.org/v1.17/client-server-api/#post_matrixclientv3publicrooms)
* [`GET /_matrix/federation/v1/publicRooms`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1publicrooms)
* [`POST /_matrix/federation/v1/publicRooms`](https://spec.matrix.org/v1.17/server-server-api/#post_matrixfederationv1publicrooms)

All of these endpoints order the returned rooms by joined member count, largest first. This explicit
ordering can cause rooms to appear at the top of the list when the server admin/directory curator
wants specific rooms at the top instead.

As a concrete example, matrix.org is interested in pinning Matrix HQ to the top of the list. Due to
a recent upgrade though, the room is "small" and appears further down the list than some not-yet-upgraded
rooms. Ideally, matrix.org could instruct its server to use a specific ordering that causes HQ to be
at the top of the list.

t2bot.io, another community on Matrix, would similarly like to do something similar. As would a number
of other communities which have a "(near-)general chat" for users to visit.

This proposal removes the strict ordering requirements, leaving the order as an implementation-specific
concern.


## Proposal

Per the intro, the "largest rooms first" requirement is dropped from the above-listed endpoints. No
ordering is defined by the specification. Implementations will need to consider using stable ordering
to ensure pagination responses are sane, though.


## Potential issues

None are forseen. There's been instances in the past where the ordering requirements have been violated
and both servers and clients processing those responses performed normally.


## Alternatives

The alternatives largely amount to picking an ordering mechanism or defining a pinning system. This
is an area of the spec which feels it can benefit from more implementation-specific behaviour rather
than mandated consistency.

Using [Spaces](https://spec.matrix.org/v1.17/client-server-api/#spaces) instead of a room directory
is desirable, but doesn't solve the concern of ordering. Existing implementations which use Spaces
to back their room directories can potentially make use of the "suggested" feature to pin specific
rooms at the top.


## Security considerations

None relevant.


## Unstable prefix

None applicable. "Implementation" of this proposal largely amounts to doing *some* ordering, which
is naturally achieved by existing implementations following the existing spec.


## Dependencies

This proposal has no direct dependencies.
