# MSC2475: API versioning

Currently we have the `/r0` style of versioning defined in the spec for how it behaves, but
have no similar definition for the `/v1` APIs. This MSC is an attempt to formalize the scheme
and reduce confusion - it strictly does not propose changing what scheme the APIs currently
use, nor does it propose a complete refactoring of the versioning systems.

## Proposal

When using the `/v1` style of versioning in APIs, it is a per-endpoint version. The first
version of an endpoint should be `v1` in most cases, though for ease of understanding it is
accetable to use a higher version when making large/sweeping changes to the API. For example,
adding a new requirement to all existing endpoints which bumps them to `v2` would allow an
endpoint which has never been seen before to also start at `v2`.

The version number is monotonically increasing integer. The `v1` style versioning has no
relation to the API's release version (`r0.1.0` has no meaning towards `v1`, unlike in the
`r0` style versioning).

Some worked examples of this (using fake endpoints) follow:

1. The spec currently has `/v1/profile`, `/v1/get_event`, and `/v2/send_message`.
2. An MSC to add a new endpoint, `/delete_message` is made. It would be `/v1/delete_message` because
   it's the first time we've seen it.
   

1. The spec currently has `/v1/profile`, `/v1/get_event`, and `/v2/send_message`.
2. An MSC is opened which adds authentication to all the endpoints. Some `/login` and
   `/register` endpoints are added too. These endpoints can be `/v3/login` and `/v3/register`
   for clarity and consistency with the bumps to the other endpoints.


1. The spec currently has `/v1/profile`, `/v1/get_event`, and `/v2/send_message`.
2. An MSC is opened to change `/profile` to return different information which is backwards
   incompatible. It gets bumped to `/v2/profile` without changes to other endpoints.
   

## Alternative solutions

We instead could use some heuristics to determine when the whole API has been bumped by a
version. This would mean that endpoints added later on down the road would start at a higher
number.

Either system is fine, we just need to make a decision.
