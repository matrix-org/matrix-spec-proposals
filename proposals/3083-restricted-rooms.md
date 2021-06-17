# Restricting room membership based on space membership

A desirable feature is to give room admins the power to restrict membership of
their room based on the membership of one or more spaces from
[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772), for example:

> members of the #doglovers space can join this room without an invitation<sup id="a1">[1](#f1)</sup>

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
        ],
        "authorised_servers": ["example.org"]
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

The `authorised_servers` key lists servers which are trusted to verify the above
allow rules. It must be a list of string server name, a special value of `"*"`
can be used to allow any server with a member in the room. Any non-string entries
are discarded, if the list is non-existent or empty then no users may join without
an invite.<sup id="a3">[3](#f3)</sup>

From the perspective of the [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules),
the `restricted` join rule has the same behavior as `public`, with the additional
caveat that servers must ensure that:

* The user's current membership is `invite` or `join`, or
* The `m.room.member` event has a valid signature from one of the servers listed
  in `authorised_servers`.

The above check must also be performed against the current room state to potentially
soft-fail the event. This is the primary mechanism for guarding against state
changes when old events are referenced. (E.g. if an authorised server is removed
it should not be able to issue new membership events by referencing an old event
in the room.)

When an authorised homeserver receives a `/join` request from a client or a
`/make_join` / `/send_join` request from another homeserver, the request should
only be  permitted if the user has a valid invite or is in one of the listed rooms.
If the user is not a member of at least one of the rooms, the authorised homeserver
should return an error response with HTTP status code of 403 and an `errcode` of
`M_FORBIDDEN`.

It is possible for a homeserver receiving a `/make_join` / `/send_join` request
to not know if the user is in a particular room (due to not participating in any
of the necessary rooms). In this case the homeserver should reject the join,
the requesting server may wish to attempt to join via another authorised homeserver.
If no authorised servers are in an allowed room its membership cannot be checked
(and this is a misconfiguration).

Note that the authorised homeservers have significant power, as they are trusted
to confirm that the `allow` rules were properly checked (since this cannot
easily be enforced over federation by event authorisation).<sup id="a4">[4](#f4)</sup>

## Summary of the behaviour of join rules

See the [join rules](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-join-rules)
specification for full details, the summary below is meant to highlight the differences
between `public`, `invite`, and `restricted`.

* `public`: anyone can join, subject to `ban` and `server_acls`, as today.
* `invite`: only people with membership `invite` can join, subject to `ban` and
  `server_acls`, as today.
* `knock`: the same as `invite`, except anyone can knock, subject to `ban` and
  `server_acls`. See [MSC2403](https://github.com/matrix-org/matrix-doc/pull/2403).
* `private`: This is reserved, but unspecified.
* `restricted`: the same as `public`, with the additional caveat that servers must
  verify the `m.room.member` event is signed by one of the `authorised_servers` if
  a member is not yet invited or joined to the room.

## Security considerations

The `allow` feature for `join_rules` places increased trust in the authorised
servers. Any authorised server which is joined to the room will be able to issue
join events for the room which no individual server in the room could verify was
issued in good faith.

The increased trust in authorised servers is considered an acceptable trade-off
between increased centralisation and increased security.

## Unstable prefix

The `restricted` join rule will be included in a future room version to allow
servers and clients to opt-into the new functionality.

During development, an unstable room version of `org.matrix.msc3083` will be used.
Since the room version namespaces the behaviour, the `allow` key and value, as well
as the `restricted` join rule value do not need unstable prefixes.

## Alternatives

It may seem that just having the `allow` key with `public` join rules is enough
(as originally suggested in [MSC2962](https://github.com/matrix-org/matrix-doc/pull/2962)),
but there are concerns that changing the behaviour of a pre-existing a `public`
join rule may cause security issues in older implementations (that do not yet
understand the new behaviour). This could be solved by introducing a new room
version, thus it seems clearer to introduce a new join rule -- `restricted`.

Using an `allow` key with the `invite` join rules to broaden who can join was rejected
as an option since it requires weakening the [auth rules](https://spec.matrix.org/unstable/rooms/v1/#authorization-rules).
From the perspective of the auth rules, the `restricted` join rule is identical
to `public` with additional checks on the signature to ensure it was issued by
an authorised server.

## Future extensions

### Checking room membership over federation

If an authorised server is not in an allowed room (and thus doesn't know the
membership of it) then the server cannot enforce the membership checks while
generating a join event. Peeking over federation, as described in
[MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444),
could be used to establish if the user is in any of the proper rooms.

This would then delegate power out to a (potentially) untrusted server, giving that
the peek server significant power. For example, a poorly chosen peek
server could lie about the room membership and add an `@evil_user:example.org`
to an allowed room to gain membership to a room.

As iterated above, this MSC recommends rejecting the join, potentially allowing
the requesting homeserver to retry via another homeserver.

### Kicking users out when they leave the allowed room

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

<a id="f3"/>[3]: This unfortunately introduces another piece of data which must be
maintained by room administrators. It is recommended that clients initially set
this to the homeserver of the creator or the special value `"*"`. [↩](#a3)

<a id="f4"/>[4]: This has the downside of increased centralisation, as a homeserver
that is not an authorised server but is already in the room may not issue a join
event for another user on that server. (It must go through the `/make_join` /
`/send_join` flow of an authorised server.) This is considered a reasonable
trade-off. [↩](#a4)
