# Proposal for Group Access Control via Spaces in Matrix

MSC1772 defines Spaces: a new way to define groups of users and rooms in
Matrix by describing them as a room.  Originally MSC1772 attempted to define
how you could apply permissions to Matrix rooms based on the membership of a
space. However, this is effectively a separate concern from how you model spaces
themselves, and so has been split out into a this separate MSC.

## Goals:

 * Set the power levels in a room based on membership of a space
 * Restrict access to a room based on membership of a space
 * Kick users from a room if they leave a space

### Managing power levels via spaces

One use-case for spaces is to help manage power levels across a group of
rooms. For example: "Jim has just joined the management team at my company. He
should have moderator rights across all of the company rooms."

Since the event-authorisation rules cannot easily be extended to consider
membership in other rooms, we must map any changes in space membership onto
real `m.room.power_levels` events.

#### Extending the power_levels event

We now have a mix of manually- and automatically- maintained power-level
data. To support this, we extend the existing `m.room.power_levels` event to
add an `auto_users` key:

```js
{
    "type": "m.room.power_levels",
    "content": {
        "users": {
            "@roomadmin:example.com": 100
        },
        "auto_users": {
            "@spaceuser1:example.org": 50
        }
    }
}
```

A user's power level is then specified by an entry in *either* `users` or
`auto_users`. Where a user appears in both sections, `users` takes precedence.

The new `auto_users` key is maintained by a bot user, as described below.

`auto_users` is subject to all of the same authorization checks as the existing
`users` key (see https://matrix.org/docs/spec/rooms/v1#authorization-rules,
paragraphs 10a, 10d, 10e).

This change necessitates a new room version.

#### Representing the mapping from spaces to power levels

The desired mapping from spaces to power levels is defined in a new state
event type, `m.room.power_level_mappings`, set in the room whose PLs are being
manipulated. The content should contain a `mappings` key which is an
ordered list, for example:

```js
{
    "type": "m.room.power_level_mappings",
    "state_key": "",
    "content": {
        "mappings": [
            {
                "space": "!mods:example.org",
                "via": ["example.org"],
                "power_level": 50
            },
            {
                "space": "!users:example.org",
                "via": ["example.org"],
                "power_level": 1
            }
        ]
    }
}
```

This means that a new `m.room.power_levels` event would be generated whenever
the membership of either `!mods` or `!users` changes. If a user is in both
spaces, `!mods` takes priority because that is listed first.

If `mappings` is not a list, the whole event is ignored. Any entries in the list
which do not match the expected format are ignored.

#### Implementing the mapping

When a new room is created, the server implicitly adds a "room admin bot" to
the room, with the maximum power-level of any of the initial users.
(Homeservers should implement this "bot" internally, rather than requiring
separate software to be installed.)

It is proposed that this "admin bot" use the special user ID with empty
localpart `@:example.com`.

This bot is then responsible for monitoring the `power_level_mappings` state,
and peeking into any spaces mentioned in the content. It can then issue new
`m.room.power_levels` events, updating the value of `auto_users`, whenever the
membership of the spaces in question changes.

It is possible that the admin bot is unable to perform the mapping (for
example, the space cannot be peeked; or the membership of the space is so large
that it cannot be expanded into a single `m.room.power_levels` event). It is
proposed that the bot could notify the room of any problems via
`m.room.message` messages of type `m.msgtype`.

Clearly, updating this event type is extremely powerful. It is expected that
access to it is itself restricted via `power_levels`. This could be enforced by
the admin bot so that no `m.room.power_levels` events are generated unless
`power_level_mappings` is appropriately restricted.

Some sort of rate-limiting may be required to handle the case where the mapped
space has a high rate of membership churn.

#### Alternatives

Things that were considered and dismissed:

* Extend the auth rules to include state from other rooms. Although this feels
  cleaner, a robust implementation would be a hugely complicated
  undertaking. In particular, room state resolution is closely linked to event
  authorisation, and is already highly complex and hard to reason about, and
  yet is fundamental to the security of Matrix.

  In short, we believe such a change would require significant research and
  modelling. A solution based on such a foundation could not practically be
  implemented in the near future.

* Rather than defining the mapping in the room, define a template power-levels
  event in a parent space, which will be inherited by all child rooms. For example:

  ```js
  {
      "type": "m.space.child_power_levels",
      "state_key": "",
      "content": {
          // content as per regular power_levels event
      }
  }
  ```

  Problem 1: No automated mapping from space membership to user list, so the
  user list would have to be maintained manually. On the other hand, this
  could be fine in some situations, where we're just using the space to group
  together rooms, rather than as a user list.

  Problem 2: No scope for nuance, where different rooms have slightly
  different PLs.

  Problem 3: what happens to rooms where several spaces claim it as a child?
  They end up fighting?

  Problem 4: Doesn't allow for random room admins to delegate their PLs to a
  space without being admins in that space.

* To implement the mapping, we require any user who is an admin in the
  space (ie, anyone who has permission to change the access rights in the
  space) to also be admins and members of any child rooms.

  Say Bob is an admin in #doglovers and makes a change that should be
  propagated to all children of that space. His server is then responsible
  for generating a power-levels event on his behalf for each room.

  Problem 1: Bob may not want to be a member of all such rooms.

  Problem 2: It will feel odd that Bob's user is seen to be generating PL
  events every time someone comes and goes from the space.

  Problem 3: It doesn't allow users to set up their own rooms to mirror a
  space, without having any particular control in that space (though it is
  questionable if that is actually a useful feature, at least as far as PLs are
  concerned.)

* Another alternative for implementing the mapping: the user that created the
  relationship event (or rather, their homeserver, using the user's ID) is
  responsible for copying access controls into the room.

  Problem 1: What do you do if the admin who sets up the PL relationship
  disappears? The humans have to step in and create a new admin?

  Problem 2: Again it seems odd that these PL changes come from a single user.

* Is it possible to implement the mappings from multiple users, some of which
  may not have PL 100? After all it's possible to set rooms up so that you can
  change PL events without having PL 100.

  It gets horribly messy very quickly, where some admin users can make some
  changes. So some get supressed and then get made later anyway by a different
  admin user?

* Is it possble to apply finer-grained control to the
  `m.room.power_level_mappings` event than "you must be max(PL)"? Applying
  restrictions post-hoc (ie, having the admin bot ignore settings which were
  set by underpriviledged users) is an absolute minefield. It might be possible
  to apply restrictions at the point that the event is set, but it sounds
  fiddly and it's not clear there is a real use-case.

* This solution smells a bit funny because of the expansions (causing all the
  redundant mxids everywhere as the groups constantly get expanded every time
  something happens).

  * Could we could put a hash of the space membership in the PL instead of
    expanding the whole list, so that servers have a way to check if they are
    applying the same list as everyone else?

    Feels like it will have bad failure modes: what is a server supposed to do
    when the hash doesn't match?

  * Could version the space memberships, so you can compare with the source of
    the space membership data?

  * PL events just record the delta from the previous one? (So a new server
    would need to get all the PLs ever, but… is that a bad thing?)  ... maybe

  These optimisations can all be punted down the road to a later room version.

* Other ways of handling the merge of automatic and manual PL settings:

  * Add hints to the automated mapper so that it can maintain manually-assigned
    PLs. This could either be another field in `power_levels` which plays no
    part in event auth:

    ```js
    {
        "type": "m.room.power_levels",
        "content": {
            "users": {
                "@roomadmin:example.com": 100,
                "@spaceuser1:example.org": 50
            },
            "manual_users": {
                "@roomadmin:example.com": 100
            }
        }
    }
    ```

    ... or stored in a separate event. Clients would be responsible for updating
    both copies of the manually-assigned PLs on change.

    Problem: Requiring clients to make two changes feels fragile. What if they
    get it wrong? what if they don't know about the second copy because they
    haven't been designed to work in rooms in spaces?

  * Require that even regular PLs go through the automated mapper, by making
    them an explicit input to that mapper, for example with entries in the
    `m.room.power_level_mappings` event suggested above.

    Problem: Requires clients to distinguish between rooms where there is an
    automated mapper, and those where the client should manipulate the PLs
    directly. (Maybe that's not so bad? The presence of the `mappings` event
    should be enough? But still sucks that there are two ways to do the same
    thing, and clients which don't support spaces will get it wrong.)

### Restricting room membership based on space membership

A desirable feature is to give room admins the power to restrict membership of
their room based on the membership of spaces (for example, "members of the
#doglovers space can join this room without an invitation"<sup id="a1">[1](#f1)</sup>).

We could represent the allowed spaces with additional content in the
`m.room.join_rules` event. For example:

```js
{
    "type": "m.room.join_rules",
    "state_key": "",
    "content": {
        "join_rule": "public",
        "allow": [
            {
                "space": "!mods:example.org",
                "via": ["example.org"],
            },
            {
                "space": "!users:example.org",
                "via": ["example.org"],
            }
        ]
    }
}
```

The `allow` key applies a restriction to the `public` join rule, so that
only users satisfying one or more of the requirements should be allowed to
join. Additionally, users who have received an explicit `invite` event are
allowed to join<sup id="a2">[2](#f2)</sup>. If the `allow` key is an
empty list (or not a list at all), no users are allowed to join without an
invite.

Unlike the regular `invite` join rule, the restriction cannot be enforced over
federation by event authorization, so servers in the room are trusted not to
allow invalid users to join.<sup id="a3">[3](#f3)</sup>

When a server receives a `/join` request from a client or a
`/make_join`/`/send_join` request from a server, the request should only be
permitted if the user has a valid invite or is in one of the listed spaces
(established by peeking).

XXX: redacting the join_rules above will reset the room to public, which feels dangerous?

A new room version is not absolutely required here, but may be advisable to
ensure that servers that do not support `allow` do not join the room
(and would also allow us to tweak the redaction rules to avoid the foot-gun).

#### Kicking users out when they leave the allowed space

XXX: this will probably be a future extension, rather than part of the initial
implementation of `allow`.

In the above example, suppose `@bob:server.example` leaves `!users:example.org`:
they should be removed from the room. One option is to leave the departure up
to Bob's server `server.example`, but this places a relatively high level of trust
in that server. Additionally, if `server.example` were offline, other users in
the room would still see Bob in the room (and their servers would attempt to
send message traffic to it).

Instead, we make the removal the responsibility of the room's admin bot (see
above): the bot is expected to peek into any spaces in `allow` and kick
any users who are members of the room and leave the union of the allowed
spaces.

(XXX: should users in a space be kicked when that space is removed from the
`allow` list? We think not, by analogy with what happens when you switch
the join rules from `public` to `invite`.)

One problem here is that it will lead to users who joined via an invite being
kicked. For example:
 * `@bob:server.example` creates an invite-only room.
 * Later, the `join_rules` are switched to `public`, with an `allow` of
   `!users:example.org`, of which Bob happens to be a member.
 * Later still, Bob leaves `!users:example.org`.
 * Bob is kicked from his own room.

Fixing this is thorny. Some sort of annotation on the membership events might
help. but it's unclear what the desired semantics are:

 * Assuming that users in a given space are *not* kicked when that space is
   removed from `allow`, are those users then given a pass to remain
   in the room indefinitely? What happens if the space is added back to
   `allow` and *then* the user leaves it?

 * Suppose a user joins a room via a space (SpaceA). Later, SpaceB is added to
   the `allow` list and SpaceA is removed. What should happen when the
   user leaves SpaceB? Are they exempt from the kick?

#### Alternatives

* Maintain some sort of pre-approved list as the space membership changes in a
  similar way to the PL mapping, possibly via a new membership state.

  Could lead to a lot of membership churn, from a centralised control point.

* Base it on invite-only rooms, and generate invite events on the fly. Kind-of
  ok, except that we'd want the invites to be seen as having a sender of a
  management bot rather than an arbitrary user, which would mean that all joins
  would have to go through that one server (even from servers that were already
  participating in the room), which feels a bit grim. We could have multiple
  admin bots to mitigate this, but it gets a bit messy.

* Change the way that `allow` and invites interact, so that an invite
  does not exempt you from the `allow` requirements. This would be
  simpler to implement, but probably doesn't match the expected UX.

* Put the `allow` rules in a separate event? This is attractive because
  `join_rules` are involved in event auth and hence state resolution, and the
  fewer events that state res has to grapple with the better. However, doing
  this would probably require us to come up with a new `join_rule` state to
  tell servers to go and look for the allowed spaces.

## Future extensions

### Inheriting join rules

If you make a parent space invite-only, should that (optionally?) cascade into
child rooms? Seems to have some of the same problems as inheriting PLs.

## Dependencies

 * [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) for room spaces.

## Security considerations

* The `allow` feature for `join_rules` places increased trust in the servers in the
  room. We consider this acceptable: if you don't want evil servers randomly
  joining spurious users into your rooms, then a) don't let evil servers in
  your room in the first place, b) don't use `allow` lists, given the
  expansion increases the attack surface anyway by letting members in other
  rooms dictate who's allowed into your room.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`m.room.power_level_mappings` | event type | `org.matrix.msc1772.room.power_level_mappings`
`auto_users` | key in `m.room.power_levels` event | `org.matrix.msc1772.auto_users`
`allow` | key in `m.room.join_rules` event | `org.matrix.msc1772.allow`
