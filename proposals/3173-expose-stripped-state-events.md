# MSC3173: Expose stripped state events to any potential joiner

It is currently possible to inspect the state of rooms in some circumstances:

* If the room has `history_visibility: world_readable`, then anyone can inspect it (by calling `/state` on it).
* Rooms in the room directory expose some of their state publicly.
* [Invited users](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid) (and [knocking users](https://github.com/matrix-org/matrix-doc/pull/2403)) receive stripped state events.

This MSC proposes exposing the stripped state events that are currently available
to invited and knocking users to any user who could potentially join a room. It
also consolidates the recommendation on which states events are available to
potential joiners.

## Background

When creating an invite it is [currently recommended](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
to include stripped state events which are useful for displaying the invite to a user:

> An optional list of simplified events to help the receiver of the invite identify
> the room. The recommended events to include are the join rules, canonical alias,
> avatar, and name of the room.

The invited user receives these [stripped state events](https://spec.matrix.org/unstable/client-server-api/#get_matrixclientr0sync)
as part of the `/sync` response:

> The state of a room that the user has been invited to. These state events may
> only have the `sender`, `type`, `state_key` and `content` keys present. These
> events do not replace any state that the client already has for the room, for
> example if the client has archived the room.

These are sent as part of the [`unsigned` content of the `m.room.member` event](https://spec.matrix.org/unstable/client-server-api/#mroommember)
containing the invite.

[MSC2403: Add "knock" feature](https://github.com/matrix-org/matrix-doc/pull/2403)
extends this concept to also include the stripped state events in the `/sync` response
for knocking users:

> It is proposed to add a fourth possible key to rooms, called `knock`. Its value
> is a mapping from room ID to room information. The room information is a mapping
> from a key `knock_state` to another mapping with key events being a list of
> `StrippedStateEvent`.

It is also provides an extended rationale of why this is useful:

> These stripped state events contain information about the room, most notably the
> room's name and avatar. A client will need this information to show a nice
> representation of pending knocked rooms. The recommended events to include are the
> join rules, canonical alias, avatar, name and encryption state of the room, rather
> than all room state. This behaviour matches the information sent to remote
> homeservers when remote users are invited to a room.

[MSC1772: Spaces](https://github.com/matrix-org/matrix-doc/pull/1772) additionally
recommends including the `m.room.create` event as one of the stripped state events:

> Join rules, invites and 3PID invites work as for a normal room, with the exception
> that `invite_state` sent along with invites should be amended to include the
> `m.room.create` event, to allow clients to discern whether an invite is to a
> space-room or not.

## Proposal

Any user who is able to join a room can access the stripped state events of that room.

Potential ways that a user might be able to join include, but are not limited to,
the following mechanisms:

* A room that has `join_rules` set to `public` or `knock`.<sup id="a1">[1](#f1)</sup>
* A room that the user is in possession of an invite to (regardless of the `join_rules`).

Future MSCs might include additional mechanism for a user to join a room and
should consider this MSC, for example:

* [MSC3083: Restricting room membership based on space membership](https://github.com/matrix-org/matrix-doc/pull/3083) proposes allowing users to join a room based on their membership in a space (as defined in [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772)).

Additionally, it is recommended, but not required, that homeserver implementations
include the following as stripped state events:

* Create event (`m.room.create`)<sup id="a2">[2](#f2)</sup>
* Join rules (`m.room.join_rules`)
* Canonical alias (`m.room.canonical_alias`)
* Room avatar (`m.room.avatar`)
* Room name (`m.room.name`)
* Encrypted status (`m.room.encryption`)<sup id="a3">[3](#f3)</sup>

This also implies that the above information is available to any potential joiner
in the API proposed in [MSC2946: Spaces summary](https://github.com/matrix-org/matrix-doc/pull/2946).
E.g. rooms which could be joined due to [MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083)
can expose the information available in stripped state events.

## Potential issues

This is a generalization of current behavior and shouldn't introduce any new issues.

## Alternatives

A different approach to this would be to separately specify each situation in which
a user is allowed to see stripped state events, as we do currently for invites and
knocking.

## Security considerations

## Future extensions

Dedicated client-server and server-server APIs could be added to request the
stripped state events, but that is considered out-of-scope for the current
proposal.

## Unstable prefix

N/A

## Footnotes

<a id="f1"/>[1]: The rationale for including `knock` is that the user can
trivially get this state already by knocking on the room.[↩](#a1)

<a id="f2"/>[2]: As updated in [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772).[↩](#a2)

<a id="f3"/>[3]: This is already sent from Synapse and generally seems useful for
a user to know before joining a room.[↩](#a3)
