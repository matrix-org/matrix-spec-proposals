# MSC4437: Endpoint to replace entire profile
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
introduced extensible profiles, allowing users to store arbitrary information in
their global profile. Profiles can also be used by bots and bridges to signal
information like which network a bridge ghost user is from. Such use cases often
want to set multiple profile fields at once, which currently requires multiple
requests.

## Proposal
This proposal introduces a `PUT` variant of the existing
`/_matrix/client/v3/profile/{userId}` endpoint, which will replace the user's
entire profile.

Servers MUST apply the same validation rules to this endpoint as they do for the
individual field editing `PUT /_matrix/client/v3/profile/{userId}/{keyName}`. If
any field in the request fails the validation, the entire request MUST be
rejected with the same error code as setting that field in an individual request
would. The endpoint does not have any unique error cases that aren't already
returned by the existing profile update endpoint.

In addition to validation, the same `m.room.member` updating rules apply, i.e.
if `displayname` or `avatar_url` have different values than in the old profile,
new `m.room.member` events are sent to all rooms. If both fields are modified,
servers SHOULD only send one member event to each room.

Like the individual field editing endpoint, this endpoint returns an empty
object on success.

The endpoint requires authentication and is ratelimited the same way as the
`PUT /{keyName}` endpoint. Guest access is not allowed, as guests can only
update their displayname and therefore don't need a mass update endpoint.

## Potential issues
If a server stores profile fields in separate database fields, it will need to
run multiple queries to store all the fields.

## Alternatives
A `PATCH` variant could also be added. However, there are no patch endpoints in
the spec yet, and the exact behavior of them is subject to debate (e.g. can
fields be removed using patch?). Therefore, this MSC only defines a `PUT` method
that replaces the entire profile.

## Security considerations
None. The existing size limits for profiles are still enforced, and are in fact
easier to enforce in an overwrite endpoint. Updating `m.room.member` events is
not meaningfully different than the existing `PUT /displayname` and `/avatar_url`
endpoints either.

## Unstable prefix
Implementations can use `PUT /_matrix/client/unstable/com.beeper.msc4437/profile/{userId}`
instead of `PUT /_matrix/client/v3/profile/{userId}` as the endpoint until this
MSC is accepted. `com.beeper.msc4437` is used as the unstable feature flag to
advertise support for the unstable endpoint.

Once the MSC is accepted, `com.beeper.msc4437.stable` can be used to advertise
support for the stable endpoint until support for the spec release is advertised.

The request content has no unstable prefixes specific to this MSC.

## Dependencies
None, as MSC4133 is already in the spec.
