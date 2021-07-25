# Restricting room membership based on membership in other rooms

A desirable feature is to give room admins the power to restrict membership of
their room based on the membership of one or more rooms.

Potential usecases include:

* Private spaces (allowing any member of a [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772)
  space to join child rooms in that space), for example:

  > members of the #doglovers:example.com space can join this room without an invitation<sup id="a1">[1](#f1)</sup>
* Room upgrades for private rooms (instead of issuing invites to each user).
* Allowing all users in a private room to be able to join a private breakout room.

This does not preclude members from being directly invited to the room, which is
still a useful discovery feature.

## Proposal

In a future room version a new `join_rule` (`restricted`) will be used to reflect
a cross between `invite` and `public` join rules. The content of the join rules
would include the rooms to trust for membership. For example:

```json
{
    "type": "m.room.join_rules",
    "state_key": "",
    "content": {
        "join_rule": "restricted",
        "allow": [
            {
                "type": "m.room_membership",
                "room_id": "!mods:example.org"
            },
            {
                "type": "m.room_membership",
                "room_id": "!users:example.org"
            }
        ]
    }
}
```

This means that a user must be a member of the `!mods:example.org` room or
`!users:example.org` room in order to join without an invite<sup id="a2">[2](#f2)</sup>.
Membership in a single allowed room is enough.

If the `allow` key is an empty list (or not a list at all), then no users are
allowed to join without an invite. Each entry is expected to be an object with the
following keys:

* `type`: `"m.room_membership"` to describe that we are allowing access via room
  membership. Future MSCs may define other types.
* `room_id`: The room ID to check the membership of.

Any entries in the list which do not match the expected format are ignored. Thus,
if all entries are invalid, the list behaves as if empty and all users without
an invite are rejected.

When a homeserver receives a `/join` request from a client or a `/make_join` /
`/send_join` request from another homeserver, the request should only be permitted
if the user is invited to this room, or is joined to one of the listed rooms. If
the user is not a member of at least one of the rooms, the homeserver should return
an error response with HTTP status code of 403 and an `errcode` of `M_FORBIDDEN`.

It is possible for a resident homeserver (one which receives a `/make_join` /
`/send_join` request) to not know if the user is in some of the allowed rooms (due
to not participating in them). If the user is not in any of the allowed rooms that
are known to the homeserver, and the homeserver is not participating in all listed
rooms, then it should return an error response with HTTP status code of 400 with an `errcode` of `M_UNABLE_TO_AUTHORISE_JOIN`. The joining server should
attempt to join via another resident homeserver. If the resident homeserver knows
that the user is not in *any* of the allowed rooms it should return an error response
with HTTP status code of 403 and an `errcode` of `M_FORBIDDEN`. Note that it is a
configuration error if there are allowed rooms with no participating authorised
servers.

A chosen resident homeserver might also be unable to issue invites (which, as below,
is a pre-requisite for generating a correctly-signed join event). In this case
it should return an error response with HTTP status code of 400 and an `errcode`
of `M_UNABLE_TO_GRANT_JOIN`. The joining server should attempt to join via another
resident homeserver.

From the perspective of the [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules),
the `restricted` join rule has the same behavior as `public`, with the additional
caveat that servers must ensure that, for `m.room.member` events with a `membership` of `join`:

* The user's previous membership was `invite` or `join`, or
* The join event has a valid signature from a homeserver whose users have the
  power to issue invites.

  When generating a join event for `/join` or `/make_join`, the server should
  include the MXID of a local user who could issue an invite in the content with
  the key `join_authorised_via_users_server`. The actual user chosen is arbitrary.

The changes to the auth rules imply that:

* A join event issued via `/send_join` is signed by not just the requesting
  server, but also the resident server.<sup id="a3">[3](#f3)</sup>

  In order for the joining server to receive the proper signatures the join
  event will be returned via `/send_join` in the `event` field.
* The auth chain of the join event needs to include events which prove
  the homeserver can be issuing the join. This can be done by including:

  * The `m.room.power_levels` event.
  * The join event of the user specified in `join_authorised_via_users_server`.

  It should be confirmed that the authorising user is in the room. (This
  prevents situations where any homeserver could process the join, even if
  they weren't in the room, under certain power level conditions.)

The above creates a new restriction on the relationship between the resident
servers used for `/make_join` and `/send_join` -- they must now both go to
the same server (since the `join_authorised_via_users_server` is added in
the call to `/make_join`, while the final signature is added during
the call to `/send_join`). If a request to `/send_join` is received that includes
an event from a different resident server it should return an error response with
HTTP status code of 400.

Note that the homeservers whose users can issue invites are trusted to confirm
that the `allow` rules were properly checked (since this cannot easily be
enforced over federation by event authorisation).<sup id="a4">[4](#f4)</sup>

To better cope with joining via aliases, homeservers should use the list of
authorised servers (not the list of candidate servers) when a user attempts to
join a room.

## Summary of the behaviour of join rules

See the [join rules](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-join-rules)
specification for full details; the summary below is meant to highlight the differences
between `public`, `invite`, and `restricted` from a user perspective. Note that
all join rules are subject to `ban` and `server_acls`.

* `public`: anyone can join, as today.
* `invite`: only people with membership `invite` can join, as today.
* `knock`: the same as `invite`, except anyone can knock. See
  [MSC2403](https://github.com/matrix-org/matrix-doc/pull/2403).
* `private`: This is reserved, but unspecified.
* `restricted`: the same as `invite`, except users may also join if they are a
  member of a room listed in the `allow` rules.

## Security considerations

Increased trust to enforce the join rules during calls to `/join`, `/make_join`,
and `/send_join` is placed in the homeservers whose users can issue invites.
Although it is possible for those homeservers to issue a join event in bad faith,
there is no real-world benefit to doing this as those homeservers could easily
side-step the restriction by issuing an invite first anyway.

## Unstable prefix

The `restricted` join rule will be included in a future room version to allow
servers and clients to opt-into the new functionality.

During development, an unstable room version of `org.matrix.msc3083.v2` will be used.
Since the room version namespaces the behaviour, the `allow` key and value, as well
as the `restricted` join rule value do not need unstable prefixes.

An unstable key of `org.matrix.msc3083.v2.event` will be used in the response
from `/send_join` in place of `event` during development.

## Alternatives

It may seem that just having the `allow` key with `public` join rules is enough
(as originally suggested in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962)),
but there are concerns that changing the behaviour of a pre-existing `public`
join rule may cause security issues in older implementations (that do not yet
understand the new behaviour). This could be solved by introducing a new room
version, thus it seems clearer to introduce a new join rule -- `restricted`.

Using an `allow` key with the `invite` join rules to broaden who can join was rejected
as an option since it requires weakening the [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules).
From the perspective of the auth rules, the `restricted` join rule is identical
to `public` with additional checks on the signature of the event.

## Future extensions

### Checking room membership over federation

If a homeserver is not in an allowed room (and thus doesn't know the
membership of it) then the server cannot enforce the membership checks while
generating a join event. Peeking over federation, as described in
[MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444),
could be used to establish if the user is in any of the proper rooms.

This would then delegate power out to a (potentially) untrusted server, giving that
peek server significant power. For example, a poorly chosen peek
server could lie about the room membership and add an `@evil_user:example.org`
to an allowed room to gain membership to a room.

As iterated above, this MSC recommends rejecting the join, potentially allowing
the requesting homeserver to retry via another homeserver.

### Kicking users out when they leave the allowed room

In the above example, suppose `@bob:server.example` leaves `!users:example.org`:
should they be removed from the room? Likely not, by analogy with what happens
when you switch the join rules from `public` to `invite`. Join rules currently govern
joins, not existing room membership.

It is left to a future MSC to consider this, but some potential thoughts are
given below.

If you assume that a user *should* be removed in this case, one option is to
leave the departure up to Bob's server `server.example`, but this places a
relatively high level of trust in that server. Additionally, if `server.example`
were offline, other users in the room would still see Bob in the room (and their
servers would attempt to send message traffic to it).

Another consideration is that users may have joined via a direct invite, not via
access through a room.

Fixing this is thorny. Some sort of annotation on the membership events might
help, but it's unclear what the desired semantics are:

* Assuming that users in an allowed room are *not* kicked when that room is
  removed from `allow`, are those users then given a pass to remain
  in the room indefinitely? What happens if the room is added back to
  `allow` and *then* the user leaves it?
* Suppose a user joins a room via an allowed room (RoomA). Later, RoomB is added
  to the `allow` list and RoomA is removed. What should happen when the
  user leaves RoomB? Are they exempt from the kick?

It is possible that completely different state should be kept, or a different
`m.room.member` state could be used in a more reasonable way to track this.

### Inheriting join rules

If an allowed room is a space and you make a parent space invite-only, should that
(optionally?) cascade into child rooms? This would have some of the same problems
as inheriting power levels, as discussed in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962).

### Additional allow types

Future MSCs may wish to define additional values for the `type` argument, potentially
restricting access via:

* MXIDs or servers.
* A shared secret (room password).

These are just examples and are not fully thought through for this MSC, but it should
be possible to add these behaviors in the future.

### Client considerations

[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) defines a `via`
key in the content of `m.space.child` events:

> the content must contain a via `key` which gives a list of candidate servers
> that can be used to join the room.

It is possible for the list of candidate servers and the list of authorised
servers to diverge. It may not be possible for a user to join a room if there's
no overlap between these lists.

If there is some overlap between the lists of servers the join request should
complete successfully.

Clients should also consider the authorised servers when generating candidate
servers to embed in links to the room, e.g. via matrix.to.

A future MSC may define a way to override or update the `via` key in a coherent
manner.

## Footnotes

<a id="f1"/>[1]: The converse restriction, "anybody can join, provided they are not members
of the #catlovers:example.com space" is less useful since:

1. Users in the banned room could simply leave it at any time
2. This functionality is already partially provided by
   [Moderation policy lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists). [↩](#a1)

<a id="f2"/>[2]: Note that there is nothing stopping users sending and
receiving invites in `public` rooms today, and they work as you might expect.
The only difference is that you are not *required* to hold an invite when
joining the room. [↩](#a2)

<a id="f3"/>[3]: This seems like an improvement regardless since the resident server
is accepting the event on behalf of the joining server and ideally this should be
verifiable after the fact, even for current room versions. Requiring all events
to be signed and verified in this way is left to a future MSC. [↩](#a3)

<a id="f4"/>[4]: This has the downside of increased centralisation, as some
homeservers that are already in the room may not issue a join event for another
user on that server. (It must go through the `/make_join` / `/send_join` flow of
a server whose users may issue invites.) This is considered a reasonable
trade-off. [↩](#a4)
