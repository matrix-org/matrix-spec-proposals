# Restricting room membership based on space membership

A desirable feature is to give room admins the power to restrict membership of
their room based on the membership of one or more spaces from
[MSC1772: spaces](https://github.com/matrix-org/matrix-doc/pull/1772),
for example:

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
                "space": "!mods:example.org",
                "via": ["example.org"]
            },
            {
                "space": "!users:example.org",
                "via": ["example.org"]
            }
        ]
    }
}
```

This means that a user must be a member of the `!mods:example.org` space or
`!users:example.org` space in order to join without an invite<sup id="a2">[2](#f2)</sup>.
Membership in a single space is enough.

If the `allow` key is an empty list (or not a list at all), then no users are
allowed to join without an invite. Each entry is expected to be an object with the
following keys, or a string representing the MXID of the user exempted:

* `space`: The room ID of the space to check the membership of.
* `via`: A list of servers which may be used to peek for membership of the space.

Any entries in the list which do not match the expected format are ignored.

When a homeserver receives a `/join` request from a client or a `/make_join` / `/send_join`
request from a server, the request should only be permitted if the user has a valid
invite or is in one of the listed spaces. Note that the server may not know if the user
is in a particular space, this is left to a future MSC to solve.

If the user is not part of the proper space, the homeserver should return an error
response with HTTP status code of 403 and an `errcode` of `M_FORBIDDEN`.

Unlike the `invite` join rule, confirmation that the `allow` rules were properly
checked cannot be enforced over federation by event authorization, so servers in
the room are trusted not to allow invalid users to join.<sup id="a3">[3](#f3)</sup>
However, user IDs listed as strings can be properly checked over federation.

### Discovery of restricted rooms

The discovery of rooms in a space, as discussed in
[MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946): spaces summary,
must be updated to allow for discovery of restricted rooms.

MSC2946 defines that a room should be included in the spaces summary if it is
accessible (world-readable or if the user is already in the room). [MSC3173](https://github.com/matrix-org/matrix-doc/pull/3173)
declares that if a user can view the stripped state of a room if they are *able*
to join the room. Combining these two MSCs, the spaces summary should include
rooms with restricted join rule which a user is able to join (i.e. they're a
member of one of the spaces declared in the join rule).

The server-server API discussed in [MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946)
does not know the user who is requesting a summary of the space, but should divulge
the above information if any member of a server could see it. It is up to the
calling server to properly filter this information.

Trust is placed in the calling server: if there are any users on the calling
server in the correct space, that calling server has a right to know about the
rooms in that space and should return the relevant summaries, along with enough
information that the calling server can then do some filtering, thus an
additional field is added to the server-server response of the spaces summary:

* `allowed_spaces`: A list of space IDs which give access to this room.

This would modify the example response given to:

```jsonc
{
    "rooms": [
        {
            "room_id": "!ol19s:bleecker.street",
            "avatar_url": "mxc://bleecker.street/CHEDDARandBRIE",
            "guest_can_join": false,
            "name": "CHEESE",
            "num_joined_members": 37,
            "topic": "Tasty tasty cheese",
            "world_readable": true,
            "room_type": "m.space",
            "allowed_spaces": ["!mods:example.org", "!users:example.org"]
        },
        { ... }
    ],
    "events": [
        {
            "type": "m.space.child",
            "state_key": "!efgh:example.com",
            "content": {
                "via": ["example.com"],
                "suggested": true
            },
            "room_id": "!ol19s:bleecker.street",
            "sender": "@alice:bleecker.street"
        },
        { ... }
    ]
}
```

Consider that Alice and Bob share a server; Alice is a member of a space, but Bob
is not. The remote server will not know whether the request is on behalf of Alice
or Bob (and hence whether it should share details of restricted rooms within that
space).

Consider the above with a restricted room on a different server which defers
access to the above space. When summarizing the space, the homeserver must make
a request over federation for information on the room. The response would include
the room (since Alice is able to join it), but the calling server does not know
*why* they received the room, without additional information the server cannot
properly filter the returned results.

(The alternative, where the calling server sends the requesting `user_id`, and
the target server does the filtering, is unattractive because it rules out a
future world where the calling server can cache the result.)

This does not decrease security since a server could lie and make a request on
behalf of a user in the proper space to see the given information. I.e. the
calling server must be trusted anyway.

## Summary of the behaviour of join rules

See the [join rules](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-join-rules)
specification for full details, but the summary below should highlight the differences
between `public`, `invite`, and `restricted`.

* `public`: anyone can join, subject to `ban` and `server_acls`, as today.
* `invite`: only people with membership `invite` can join, as today.
* `knock`: the same as `invite`, except anyone can knock, subject to `ban` and
  `server_acls`. See [MSC2403](https://github.com/matrix-org/matrix-doc/pull/2403).
* `private`: This is reserved and not implemented.
* `restricted`: the same as `public` from the perspective of the auth rules, but
  with the additional caveat that servers are expected to check the `allow` rules
  before generating a `join` event (whether for a local or a remote user).

## Security considerations

The `allow` feature for `join_rules` places increased trust in the servers in the
room. We consider this acceptable: if you don't want evil servers randomly
joining spurious users into your rooms, then:

1. Don't let evil servers in your room in the first place
2. Don't use `allow` lists, given the expansion increases the attack surface anyway
   by letting members in other rooms dictate who's allowed into your room.

## Unstable prefix

The `restricted` join rule will be included in a future room version to ensure
that servers and clients opt-into the new functionality.

During development it is expected that an unstable room version of
`org.matrix.msc3083` is used. Since the room version namespaces the behaviour,
the `allow` key and the `restricted` value do not need unstable prefixes.

## History / Rationale

Note that this replaces the second half of an older version of
[MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962).

It may seem that just having the `allow` key with `public` join rules is enough,
as suggested in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962),
but there are concerns that having a `public` join rule that is restricted may
cause issues if an implementation does not understand the semantics of the `allow`
keyword. Using an `allow` key with `invite` join rules also does not make sense as
from the perspective of the auth rules, this is akin to `public` (since the checking
of whether a member is in the space is done during the call to `/join`
or `/make_join` / `/send_join`).

The above concerns about an implementation not understanding the semantics of `allow`
could be solved by introducing a new room version, but if this is done it seems clearer
to just introduce a a new join rule - `restricted` - as described above.

## Future extensions

Potential future extensions which should not be designed out include, but are not
included in this MSC.

### Checking space membership over federation

If a server is not in a space (and thus doesn't know the membership of a space) it
cannot enforce membership of a space during a join. Peeking over federation,
as described in [MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444),
could be used to establish if the user is in any of the proper spaces.

Note that there are additional security considerations with this, namely that
the peek server has significant power. For example, a poorly chosen peek
server could lie about the space membership and add an `@evil_user:example.org`
to a space to gain membership to a room.

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
access through a space.

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
child rooms? Seems to have some of the same problems as inheriting power levels,
as discussed in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962).

## Footnotes

<a id="f1"/>[1]: The converse restriction, "anybody can join, provided they are not members
of the '#catlovers' space" is less useful since:

1. Users in the banned space could simply leave it at any time
2. This functionality is already somewhat provided by [Moderation policy lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists). [↩](#a1)

<a id="f2"/>[2]: Note that there is nothing stopping users sending and
receiving invites in `public` rooms today, and they work as you might expect.
The only difference is that you are not *required* to hold an invite when
joining the room. [↩](#a2)

<a id="f3"/>[3]: This is a marginal decrease in security from the current
situation. Currently, a misbehaving server can allow unauthorized users to join
any room by first issuing an invite to that user. In theory that can be
prevented by raising the PL required to send an invite, but in practice that is
rarely done. [↩](#a2)
