# MSC3173: Expose stripped state events to any potential joiner

It can be useful to view the partial state of a room before joining to allow a user
to know *what* they're joining. For example, it improves the user experience to
show the user the room name and avatar before joining.

It is already allowed to partially view the room state without being joined to
the room in some situations:

* If the room has `history_visibility: world_readable`, then anyone can inspect
  it (by calling `/state` on it).
* Rooms in the [room directory](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-publicrooms)
  expose some of their state publicly.
* [Invited users](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
  and [knocking users](https://github.com/matrix-org/matrix-doc/pull/2403)
  receive stripped state events to display metadata to users.

This MSC proposes formalizing that the stripped state that is currently available
to invited and knocking users is available to any user who could potentially join
a room. It also defines "stripped state" and consolidates the recommendation on
which events to include in the stripped state.

## Background

When creating an invite it is [currently recommended](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
to include stripped state events which are useful for displaying the invite to a user:

> An optional list of simplified events to help the receiver of the invite identify
> the room. The recommended events to include are the join rules, canonical alias,
> avatar, and name of the room.

The invited user receives these [stripped state events](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-sync)
as part of the `/sync` response:

> The state of a room that the user has been invited to. These state events may
> only have the `sender`, `type`, `state_key` and `content` keys present. These
> events do not replace any state that the client already has for the room, for
> example if the client has archived the room.

These are sent as part of the [`unsigned` content of the `m.room.member` event](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-member)
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

The specification does not currently define what "stripped state" is or formally
describe who can access it, instead it is specified that certain situations (e.g.
an invite or knock) provide a potential joiner with the stripped state of a room.

This MSC clarifies what "stripped state" is and formalizes who can access the
stripped state of a room in future cases.

Potential ways that a user might be able to join a room include, but are not
limited to, the following mechanisms:

* A room that has `join_rules` set to `public` or `knock`.
* A room that the user is in possession of an invite to (regardless of the `join_rules`).

This MSC proposes a formal definition for the stripped state of a room<sup id="a1">[1](#f1)</sup>:

> The stripped state of a room is a list of simplified state events to help a
> potential joiner identify the room. These state events may only have the
> `sender`, `type`, `state_key` and `content` keys present.

### Client behavior

These events do not replace any state that the client already has for the room,
for example if the client has archived the room. Instead the client should keep
two separate copies of the state: the one from the stripped state and one from the
archived state. If the client joins the room then the current state will be given
as a delta against the archived state not the stripped state.

### Server behavior

It is recommended (although not required<sup id="a2">[2](#f2)</sup>) that
homeserver implementations include the following events as part of the stripped
state of a room:

* Create event (`m.room.create`)<sup id="a3">[3](#f3)</sup>
* Join rules (`m.room.join_rules`)
* Canonical alias (`m.room.canonical_alias`)
* Room avatar (`m.room.avatar`)
* Room name (`m.room.name`)
* Encryption information (`m.room.encryption`)<sup id="a4">[4](#f4)</sup>
* Room topic (`m.room.topic`)<sup id="a5">[5](#f5)</sup>

## Potential issues

This is a formalization of current behavior and should not introduce new issues.

## Alternatives

A different approach would be to continue with what is done today for invites,
knocking, the room directory: separately specify that a user is allowed to see
the stripped state (and what events the stripped state should contain).

## Security considerations

This would allow for invisibly accessing the stripped state of a room with `public`
or `knock` join rules.

In the case of a public room, if the room has `history_visibility` set to `world_readable`
then this is no change. Additionally, this information is already provided by the
room directory (if the room is listed there). Otherwise, it is trivial to access
the state of the room by joining, but currently users in the room would know
that the join occurred.

Similarly, in the case of knocking, a user is able to trivially access the
stripped state of the room by knocking, but users in the room would know that
the knock occurred.

This does not seem to weaken the security expectations of either join rule.

## Future extensions

### Revisions to the room directory

A future MSC could include additional information from the stripped state events
in the [room directory](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-publicrooms).
The main missing piece seems to be the encryption information, but there may also
be other pieces of information to include.

### Additional ways to access the stripped state

[MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946) proposes including
the stripped state in the spaces summary. Not needing to rationalize what state
can be included for a potential joiner would simplify this (and future) MSCs.

### Additional ways to join a room

[MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083) proposes a new
join rule due to membership in a space. This MSC would clarify that the stripped
state of a room is available to those joiners.

### Dedicated API for accessing the stripped state

Dedicated client-server and server-server APIs could be added to request the
stripped state events, but that is considered out-of-scope for the current
proposal.

This API would allow any potential joiner to query for the stripped state. If
the server does not know the room's state it would need to query other servers
for it.

## Unstable prefix

N/A

## Footnotes

<a id="f1"/>[1]: No changes are proposed to
[the definition of `history_visibility`](https://matrix.org/docs/spec/client_server/r0.6.1#room-history-visibility).
The state of a room which is `world_readable` is available to anyone. This somewhat
implies that the stripped state is also available to anyone, regardless of the join
rules, but having a `world_readable`, `invite` room does not seem valuable. [↩](#a1)

<a id="f2"/>[2]: Privacy conscious deployments may wish to limit the metadata
available to users who are not in a room as the trade-off against user experience.
There seems to be no reason to not allow this. [↩](#a2)

<a id="f3"/>[3]: As updated in [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772). [↩](#a3)

<a id="f4"/>[4]: The encryption information (`m.room.encryption`) is already sent
from Synapse and generally seems useful for  a user to know before joining a room.
[↩](#a4)

<a id="f5"/>[5]: The room topic (`m.room.topic`) is included as part of the
[room directory](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-publicrooms)
response for public rooms. It is also planned to be included as part of [MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946)
in the spaces summary response. [↩](#a5)
