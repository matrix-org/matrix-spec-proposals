# MSC3572: Relation aggregation cleanup

MSC2575 documented how aggregation have been used in the ecosystem in spite of
them not being part of the spec. This MSC addresses some issues that crept into
that MSC because the original design of aggregations didn't receive enough feedback.

## Proposal

### Rename `m.relations` in `unsigned` to `relations`

`m.relations` is inconsistent with the other fields under the
[`unsigned`](https://spec.matrix.org/unstable/client-server-api/#room-event-fields)
field.

the CNSIG is really meant for things that are very likely to be extended by
client/server implementations. Event types are a good example; the contents of
unsigned is not, really (particularly given everything else in unsigned does not
use a prefix).

The thing that is particularly objectionable about m.relations is it means that
a single object (unsigned) contains a mix of namespaced and unnamespaced
identifiers.

For compatibility reasons, we should (temporarily) return both `m.relations`
and `relations`.