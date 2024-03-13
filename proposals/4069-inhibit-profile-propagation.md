# MSC4069: Inhibit profile propagation

The current [`PUT /avatar_url`](https://spec.matrix.org/v1.8/client-server-api/#put_matrixclientv3profileuseridavatar_url)
and [`PUT /displayname`](https://spec.matrix.org/v1.8/client-server-api/#put_matrixclientv3profileuseriddisplayname)
endpoints modify the "global" profile for the user. This profile is typically exposed through the
user directory and other similar room-less places. Servers are additionally
[required to](https://spec.matrix.org/v1.8/client-server-api/#events-on-change-of-profile-information)
update the `m.room.member` (and similar) events for the user with the new profile information.

Some applications prefer to manually manage the profile updates in-room and over presence, as they
may need to enable per-space, per-room, or other sufficiently limited profile updates. Instead of
waiting for the server to update the user's profile everywhere before "fixing" the events, it could
ask the server to not update the events in the first place. This proposal introduces an optional
flag to enable that exact functionality.

A somewhat more niche usage of this MSC might be a project like [matrix-media-repo](https://github.com/turt2live/matrix-media-repo)
aiming to implement [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911): when
the user's avatar URL is changed, the media repo can intercept the request, proxy it forward to the
homeserver as inhibited, then manually copy the media enough times to update all the user's joined
rooms. This approach would reduce the number of custom endpoints required by a homeserver for MMR
integration.

## Proposal

The following two endpoints gain an *optional* new query parameter: `propagate`. The value MUST be a
boolean, and defaults to `true` if not provided. If the value is *not* a boolean, a normal 400 Bad
Request error code is returned.

* [`PUT /avatar_url`](https://spec.matrix.org/v1.8/client-server-api/#put_matrixclientv3profileuseridavatar_url)
* [`PUT /displayname`](https://spec.matrix.org/v1.8/client-server-api/#put_matrixclientv3profileuseriddisplayname)

When `false`, `m.room.member` and `m.presence` events are *not* emitted automatically by the server
during execution of the above two endpoints. Servers should still perform this bit of the spec,
however:

> Additionally, when homeservers emit room membership events for their own users, they should
> include the display name and avatar URL fields in these events so that clients already have these
> details to hand, and do not have to perform extra round trips to query it.

With respect to [MSC3911](https://github.com/matrix-org/matrix-spec-proposals/pull/3911), when the
user updates their profile's avatar with `?propagate=false`, the media they use is *not* cloned nor
used in event updates. The client can manually clone the media if they prefer using MSC3911's copy
API.

Some servers use different rate limits depending on whether the client is using the profile APIs or
state APIs. This proposal suggests no changes to the rate limits, though servers *may* wish to apply
intelligent rate limits to state event changes. For example, detecting that the user is updating their
profile information in a subset of rooms shortly after updating their global profile.

## Potential issues

This adds a bit of API bloat for a relatively uncommon feature, though may enable other features to
be more readily possible. For example, a client *introducing* per-space memberships might use this
new query parameter to make it easier to manually apply `m.room.member` event changes.

## Alternatives

Currently Discord bridges will update the global user profile, wait for that to complete (which can
take minutes), then manually fix all of the `m.room.member` events for the user to accomplish proper
platform bridging. While this does work, it is often slow and unreliable when the server takes an
eternity to complete the profile change request due to a large number of rooms needing updates. Some
servers, like t2bot.io, instead decide to [patch](https://github.com/t2bot/synapse/commit/049cacfc2d9e98fc602b85978c70363ce3c4f52f)
their server software to enforce this MSC's behaviour with a more blunt instrument.

## Security considerations

No major security considerations required. This MSC effectively reduces spam, though may affect a
user's perceivable privacy. Clients should be careful to explain *where* a user's profile updates
will be visible, regardless of this MSC.

## Unstable prefix

While this MSC is not considered stable, clients can use `?org.matrix.msc4069.propagate` instead of
`?propagate`. To ensure the server supports the functionality before a spec release, clients should
look for the unstable feature `org.matrix.msc4069`.

Once this MSC has successfully passed a merge FCP, clients can (and should) send *both* `?propagate`
and `?org.matrix.msc4069.propagate` to ensure backwards compatibility with slightly old servers.

Once released in the specification, clients should be checking for server support through advertised
spec versions instead.

## Dependencies

This MSC has no dependencies.
