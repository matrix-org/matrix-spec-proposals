# MSC4449: Updated /members filtering

Currently, [`GET /_matrix/client/v3/rooms/{roomId}/members`][s1] only allows filtering up to one
kind of membership per filter.
This means clients can only request members who match a specific membership, or do not match a
specific membership. This proposal aims to make this endpoint more intuitive and useful by allowing
the filters to match against multiple memberships.

[s1]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3roomsroomidmembers

## Proposal

Building on the art of [MSC2895](https://github.com/matrix-org/matrix-spec-proposals/pull/2895),
this proposal will move spearhead one of the options proposed.

As it appears to be the least complex change, the `membership` and `not_membership` query parameters
are updated to allow being provided multiple times, to specify multiple matches. For example,
specifying `?membership=join&membership=invite` will yield all memberships of kinds `join`, *or*
`invite`. Specifying `?not_membership=leave&not_membership=ban` will yield all memberships that are
NOT of kinds `leave` or `ban` (so, at the time of writing, `join`, `invite`, or `knock`).

As part of this change, they are also made *mutually exclusive*. Specifying both `membership` and
`not_membership` in the same query is explicitly forbidden, and will return `400 / M_INVALID_PARAM`.

## Potential issues

This change re-uses existing parameter names and may confuse older servers if newer clients try to
request data with the updated filter behaviour. In order to attempt to reduce this collision,
clients should check for the unstable feature or relevant spec version (if merged) in `/versions`
before using the updated behaviour.

## Alternatives

As mentioned, [MSC2895](https://github.com/matrix-org/matrix-spec-proposals/pull/2895) provides some
ideas for further changes to the members endpoint, alongside some other ones.

## Security considerations

None

## Unstable prefix

Implementations should use `uk.timedout.msc4449.membership` and `uk.timedout.msc4449.not_membership`
as query parameters for the duration of the proposal's unstable period. Servers *SHOULD* advertise
`uk.timedout.msc4449` in `/_matrix/client/versions` too, so that clients will know they can use the
new parameters.

## Dependencies

None
