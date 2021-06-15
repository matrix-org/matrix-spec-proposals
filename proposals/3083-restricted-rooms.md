# Restricting room membership based on space membership

A desirable feature is to give room admins the power to restrict membership of
their room based on the membership of one or more spaces from
[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772), for example:

> members of the #doglovers space can join this room without an invitation<sup id="a1">[1](#f1)</sup>

## Proposal

A new `join_rule` (`restricted`) will be used to reflect a cross between `invite`
and `public` join rules. The content of the join rules would include the rooms
to trust for membership. For example:

```json
{
    "type": "m.room.join_rules",
    "state_key": "",
    "content": {
        "join_rule": "restricted",
        "allow": [
            {
                "type": "m.room_membership",
                "room": "!mods:example.org",
                "via": ["example.org"]
            },
            {
                "type": "m.room_membership",
                "room": "!users:example.org",
                "via": ["example.org"]
            }
        ]
    }
}
```

This means that a user must be a member of the `!mods:example.org` room or
`!users:example.org` room in order to join without an invite<sup id="a2">[2](#f2)</sup>.
Membership in a single room is enough.

If the `allow` key is an empty list (or not a list at all), then no users are
allowed to join without an invite. Each entry is expected to be an object with the
following keys:

* `type`: `"m.room_membership"` to describe that we are allowing access via room
  membership. Future MSCs may define other types.
* `room`: The room ID to check the membership of.
* `via`: A list of servers which may be used to peek for membership of the room.

Any entries in the list which do not match the expected format are ignored. Thus,
if all entries are invalid, the list behaves as if empty and all users without
an invite are rejected.

From the perspective of hee [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules),
the `restricted` join rule has the same behavior as `public`. Additional checks
against the `allow` rules are performed during event generation, as described below.

When a homeserver receives a `/join` request from a client or a `/make_join` / `/send_join`
request from a server, the request should only be permitted if the user has a valid
invite or is in one of the listed rooms.

If the user is not a member of at least one of the rooms, the homeserver should
return an error  response with HTTP status code of 403 and an `errcode` of `M_FORBIDDEN`.

It is possible for a homeserver receiving a `/make_join` / `/send_join` request
to not know if the user is in a particular room (due to not participating in any
of the necessary rooms). In this case the homeserver should reject the join,
the requesting server may wish to attempt to join via other homeservers.

Unlike the `invite` join rule, confirmation that the `allow` rules were properly
checked cannot be enforced over federation by event authorisation, so servers in
the room are trusted not to allow invalid users to join.<sup id="a3">[3](#f3)</sup>

## Summary of the behaviour of join rules

See the [join rules](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-join-rules)
specification for full details, but the summary below should highlight the differences
between `public`, `invite`, and `restricted`.

* `public`: anyone can join, subject to `ban` and `server_acls`, as today.
* `invite`: only people with membership `invite` can join, subject to `ban` and
  `server_acls`, as today.
* `knock`: the same as `invite`, except anyone can knock, subject to `ban` and
  `server_acls`. See [MSC2403](https://github.com/matrix-org/matrix-doc/pull/2403).
* `private`: This is reserved, but unspecified.
* `restricted`: the same as `public` from the perspective of the [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules),
  but with the additional caveat that servers must check the `allow` rules before
  generating a `join` event (whether for a local or a remote user).

## Security considerations

The `allow` feature for `join_rules` places increased trust in the servers in the
room. Any server which is joined to the room will be able to issue join events
for the room, there are situations which no individual server in the room can
verify that the membership event was issued in good faith.

We consider this acceptable: if you don't want evil servers randomly joining
spurious users into your rooms, then:

1. Don't let evil servers in your room in the first place
2. Don't use `allow` lists, given the expansion increases the attack surface anyway
   by letting members in other rooms dictate who's allowed into your room.

## Unstable prefix

The `restricted` join rule will be included in a future room version to allow
servers and clients to opt-into the new functionality.

During development, an unstable room version of `org.matrix.msc3083` will be used.
Since the room version namespaces the behaviour, the `allow` key and value, as well
as the `restricted` join rule value do not need unstable prefixes.

## Alternatives

It may seem that just having the `allow` key with `public` join rules is enough
(as originally suggested in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962)),
but there are concerns that having a `public` join rule that is restricted may
cause issues if an implementation has not been updated to understand the semantics
of the `allow` keyword. This could be solved by introducing a new room version,
but in that case it seems clearer to introduce the `restricted` join rule, as
described above.

Using an `allow` key with `invite` join rules to broaden who can join was rejected
as an option since it requires weakening the [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules).
From the perspective of the auth rules, the `restricted` join rule is identical
to `public` (since the checking of whether a member is in the room is done during
the call to `/join` or `/make_join` / `/send_join` regardless).

It was also considered to limit servers which can issue join membership events
to those in the `via` field (or some other list of trusted servers). This is
undesirable since it would increase centralization (e.g. a server already in the
room couldn't issue membership events for another user on that server). It is
unclear that this would significantly increase the security of the room.

## Future extensions

### Checking room membership over federation

If a server is not in a room (and thus doesn't know the membership of a room) it
cannot enforce membership of a room during a call to `/make_join`, or `/send_join`.
Peeking over federation,  as described in [MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444),
could be used to establish if the user is in any of the proper rooms.

Note that there are additional security considerations with this, namely that
the peek server has significant power. For example, a poorly chosen peek
server could lie about the room membership and add an `@evil_user:example.org`
to a room to gain membership to a room.

As iterated above, this MSC recommends rejecting the join, potentially allowing
the requesting homeserver to retry via another homeserver.

### Kicking users out when they leave the allowed space

In the above example, suppose `@bob:server.example` leaves `!users:example.org`:
should they be removed from the room? Likely not, by analogy with what happens
when you switch the join rules from public to invite. Join rules currently govern
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
help. but it's unclear what the desired semantics are:

* Assuming that users in a given space are *not* kicked when that space is
  removed from `allow`, are those users then given a pass to remain
  in the room indefinitely? What happens if the space is added back to
  `allow` and *then* the user leaves it?
* Suppose a user joins a room via a space (SpaceA). Later, SpaceB is added to
  the `allow` list and SpaceA is removed. What should happen when the
  user leaves SpaceB? Are they exempt from the kick?

It is possible that completely different state should be kept, or a different
`m.room.member` state could be used in a more reasonable way to track this.

### Inheriting join rules

If you make a parent space invite-only, should that (optionally?) cascade into
child rooms? This would have some of the same problems as inheriting power levels,
as discussed in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962).

### Additional allow types

Future MSCs may wish to define additional values for the `type` argument, potentially
restricting access via:

* MXIDs or servers.
* A shared secret (room password).

These are just examples are not fully thought through for this MSC, but it should
be possible to add these behaviors in the future.

## Footnotes

<a id="f1"/>[1]: The converse restriction, "anybody can join, provided they are not members
of the '#catlovers' space" is less useful since:

1. Users in the banned room could simply leave it at any time
2. This functionality is already partially provided by
   [Moderation policy lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists). [↩](#a1)

<a id="f2"/>[2]: Note that there is nothing stopping users sending and
receiving invites in `public` rooms today, and they work as you might expect.
The only difference is that you are not *required* to hold an invite when
joining the room. [↩](#a2)

<a id="f3"/>[3]: This is a marginal decrease in security from the current
situation. Currently, a misbehaving server can allow unauthorised users to join
any room by first issuing an invite to that user. In theory that can be
prevented by raising the PL required to send an invite, but in practice that is
rarely done. [↩](#a3)
