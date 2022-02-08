# MSC3715: `/relations` parity with `/messages`

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) introduced the
`/relations` API as an endpoint to paginate over the relations of an event. It
is described as behaving like the `/messages` API, but is missing parameters
to fully achieve that.


## Proposal

It is proposed to add the `dir`to the `/relations` API for parity with `/messages`,
it will [have the same as definition as for `/messages`](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomidmessages),
which is copied below:

> The direction to return events from. If this is set to `f`, events will
> be returned in chronological order starting at `from`. If it is set to `b`,
> events will be returned in *reverse* chronological order, again starting at `from`.
>
> One of: `[b f]`.

Including the `dir` parameter will make it easier to request missing relation
information without needed to paginate through known information -- this is
particularly needed for mobile or low-bandwidth devices where it is desired to
keep the round-trips to the server to a minimum.

It is additionally useful to unify similar endpoints as much as possible to avoid
surprises for developers.


## Potential issues

Unlike for `/messages`, the `dir` parameter for `/relations` needs to be optional
(defaulting to `b`) to be backwards  compatible with MSC2675 (and Synapse's
legacy implementation).

`/messages` does have one additional parameter (`filter`) which would still not
be implemented for `/relations`. It is unclear if this parameter is useful here.


## Alternatives

The endpoint could be replaced with the `/event_relationships` API proposed in
[MSC2836](https://github.com/matrix-org/matrix-doc/pull/2836). That API would
add significant complexity over the current `/relations` API (e.g. arbitrary
of relations) and is not necessary to simply iterate events in the reverse ordering.


## Security considerations

None.

## Unstable prefix

None, assuming that this lands in the same Matrix specification version as MSC2675.
