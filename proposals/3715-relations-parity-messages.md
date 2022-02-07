# MSC3715: `/relations` parity with `/messages`

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) introduced the
`/relations` API as an endpoint to paginate over the relations of an event. It
is described as behaving like the `/messages` API, but is missing parameters
to fully achieve that.


## Proposal

Two new parameters be added to the `/relations` API for parity with `/messages`,
both [parameters have the same as definition as for `/messages`](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomidmessages),
which are copied below:

* `dir`: The direction to return events from. If this is set to `f`, events will
  be returned in chronological order starting at `from`. If it is set to `b`,
  events will be returned in *reverse* chronological order, again starting at `from`.

  One of: `[b f]`.
* `filter`:  A JSON RoomEventFilter to filter returned events with.

The rationale for both of these is parity between endpoints, which makes the
overall specification easier to reason about. Additionally, these parameters
make it easier to request missing relation information without needed to paginate
through known information -- this is particularly needed for mobile or
low-bandwidth devices where it is desired to keep the round-trips to the server
to a minimum.


## Potential issues

The `dir` parameter needs to be optional (defaulting to `b`) to be backwards
compatible with MSC2675 (and Synapse's legacy implementation).


## Alternatives

None.


## Security considerations

None.

## Unstable prefix

None, assuming that this lands in the same Matrix specification version as MSC2675.
