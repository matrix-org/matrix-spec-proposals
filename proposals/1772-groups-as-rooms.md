# Proposal for Matrix "spaces" (formerly known as "groups as rooms (take 2)")

This obsoletes [MSC1215](https://github.com/matrix-org/matrix-doc/issues/1215).

## Background and objectives

Collecting rooms together into groups is useful for a number of
purposes. Examples include:

 * Allowing users to discover different rooms related to a particular topic:
   for example "official matrix.org rooms".
 * Allowing administrators to manage permissions across a number of rooms: for
   example "a new employee has joined my company and needs access to all of our
   rooms".
 * Letting users classify their rooms: for example, separating "work" from
   "personal" rooms.

We refer to such collections of rooms as "spaces".

Synapse and Element-Web currently implement an unspecced "groups" API (referred
to as "`/r0/groups`" in this document) which attempts to provide this
functionality (see
[matrix-doc#971](https://github.com/matrix-org/matrix-doc/issues/971)). However,
this is a complex API which has various problems (see
[appendix](#appendix-problems-with-the-r0groups-api)).

This proposal suggests a new approach where spaces are themselves represented
by rooms, rather than a custom first-class entity.  This requires few server
changes, other than better support for peeking (see Dependencies below).

The existing `/r0/groups` API would be deprecated in Synapse and remain
unspecified.

## Proposal

Each space is represented by its own room, known as a "space-room". The rooms
within the space are determined by state events within the space-room.

Spaces are referred to primarily by their alias, for example
`#foo:matrix.org`.

Space-rooms are distinguished from regular messaging rooms by the `m.room.type`
of `m.space` (see
[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840)). XXX nobody has
convinced me this is actually required.

Space-rooms may have `m.room.name` and `m.room.topic` state events in the same
way as a normal room.

Normal messages within a space-room are discouraged (but not blocked by the
server): user interfaces are not expected to have a way to enter or display
such messages.

### Membership of spaces

Users can be members of spaces (represented by `m.room.member` state events as
normal). The existing [`m.room.history_visibility`
mechanism](https://matrix.org/docs/spec/client_server/r0.6.1#room-history-visibility)
controls whether membership of the space is required to view the room list,
membership list, etc.

"Public" or "community" spaces would be set to `world_readable` to allow clients
to see the directory of rooms within the space by peeking into the space-room
(thus avoiding the need to add `m.room.member` events to the event graph within
the room).

Join rules, invites and 3PID invites work as for a normal room.

### Relationship between rooms and spaces

The intention is that rooms and spaces form a hierarchy, which clients can use
to structure the user's room list into a tree view. The parent/child
relationship can be expressed in one of two ways:

 1. The admins of a space can advertise rooms and subspaces for their space by
    setting `m.space.child` state events. The `state_key` is the ID of a child
    room or space, and the content should ontain a `via` key which gives a list
    of candidate servers that can be used to join the room. `present: true` key
    is included to distinguish from a deleted state event. Something like:

    ```js
    {
        "type": "m.space.child",
        "state_key": "!abcd:example.com",
        "content": {
            "via": ["example.com", "test.org"],
            "present": true
        }
    }

    {
        "type": "m.space.child",
        "state_key": "!efgh:example.com",
        "content": {
            "via": ["example.com"],
            "present": true,
            "order": "abcd",
            "default": true
        }
    }

    // no longer a child room
    {
        "type": "m.space.child",
        "state_key": "!jklm:example.com",
        "content": {}
    }
    ```

    Children where `present` is not present or is not set to `true` are ignored.

    The `order` key is a string which is used to provide a default ordering of
    siblings in the room list. (Rooms are sorted based on a lexicographic
    ordering of `order` values; rooms with no `order` come last. `order`s
    which are not strings, or do not consist solely of ascii characters in the
    range `\x20` (space) to `\x7F` (`~`) are forbidden and should be ignored if
    received.)

    If `default` is set to `true`, that indicates a "default child": see [below](#default-children).

 2. Separately, rooms can claim parents via `m.room.parent` state
    events, where the `state_key` is the room ID of the parent space:

    ```js
    {
        "type": "m.room.parent",
        "state_key": "!space:example.com",
        "content": {
            "via": ["example.com"]
            "present": true
        }
    }
    ```

    In this case, after a user joins such a room, the client could optionally
    start peeking into the parent space, enabling it to find other rooms in
    that space and group them together.

    To avoid abuse where a room admin falsely claims that a room is part of a
    space that it should not be, clients could ignore such `m.room.parent`
    events unless their sender has a sufficient power-level to send an
    `m.room.child` event in the parent.

    Where the parent space also claims a parent, clients can recursively peek
    into the grandparent space, and so on.

This structure means that rooms can end up with multiple parents. This implies
that the room will appear multiple times in the room list hierarchy.

In a typical hierarchy, we expect *both* parent->child and child->parent
relationships to exist, so that the space can be discovered from the room, and
vice versa. Occasions when the relationship only exists in one direction
include:

 * User-curated lists of rooms: in this case the space will not be listed as a
   parent of the room.

 * "Secret" rooms: rooms where the admin does not want the room to be
   advertised as part of a given space, but *does* want the room to form part
   of the hierarchy of that space for those in the know.

Cycles in the parent->child and child->parent relationships are *not*
permitted, but clients (and servers) should be aware that they may be
encountered, and ignore the relationship rather than recursing infinitely.

### Default children

The `default` flag on a child listing allows a space admin to list the
"default" sub-spaces and rooms in that space. This means that when a user joins
the parent space, they will automatically be joined to those default
children.

XXX implement this on the client or server?

Clients could display the default children in the room list whenever the space
appears in the list.

### Long description

We would like to allow spaces to have a long description using rich
formatting. This will use a new state event type `m.room.description` (with
empty `state_key`) whose content is the same format as `m.room.message` (ie,
contains a `msgtype` and possibly `formatted_body`).

TODO: this could also be done via pinned messages. Failing that
`m.room.description` should probably be a separate MSC.

### Managing power levels via spaces

TODO: much of this is orthogonal to the headline feature of "spaces", and
should be moved to a separate MSC.

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

`auto_users` is subject to all of the same authorization checks as the existing
`users` key (see https://matrix.org/docs/spec/rooms/v1#authorization-rules,
paragraphs 10a, 10d, 10e).

This change necessitates a new room version.

#### Representing the mapping from spaces to power levels

The desired mapping from spaces to power levels is defined in a new state event
type, `m.room.power_level_mappings`. The content should contain a `mappings`
key which is an ordered list, for example:

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

#### Implementing the mapping

When a new room is created, the server implicitly adds a "room admin bot" to
the room, with the maximum power-level of any of the initial users.
(Homeservers should implement this "bot" internally, rather than requiring
separate software to be installed.)

It is proposed that this "admin bot" use the special user ID with empty
localpart `@:example.com`.

This bot is then responsible for monitoring the `power_level_mappings` state,
and peeking into any spaces mentioned in the content. It can then issue new
`m.room.power_levels` events whenever the membership of the spaces in question
changes.

It is possible that the admin bot is unable to perform the mapping (for
example, the space cannot be peeked; or the membership of the space is so large
that it cannot be expanded into a single `m.room.power_levels` event). It is
proposed that the bot could notify the room of any problems via
`m.room.message` messages of type `m.msgtype`.

Clearly, updating this event type is extremely powerful. It is expected that
access to it is itself restricted via `power_levels`. This could be enforced by
the admin bot so that no `m.room.power_levels` events are generated unless
`power_level_mappings` is appropriately restricted.

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
        "allowed_spaces": [
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

XXX: would it be better to put it in a separate event? Doing so would probably
require us to come up with a new `join_rule` state to tell servers to go and
look for the allowed spaces.

The `allowed_spaces` key applies a restriction to the `public` join rule, so
that only users in those spaces should be allowed to join. Additionally, users
who have received an explicit `invite` event are allowed to join<sup
id="a2">[2](#f2)</sup>. If the `allowed_spaces` key is an empty list (or not a
list at all), no users are allowed to join without an invite.

Unlike the regular `invite` join rule, the restriction cannot be enforced over
federation by event authorization, so servers in the room are trusted not to
allow invalid users to join.<sup id="a3">[3](#f3)</sup>

When a server receives a `/join` request from a client or a
`/make_join`/`/send_join` request from a server, the request should only be
permitted if the user has a valid invite or is in one of the listed spaces
(established by peeking).

XXX: redacting the join_rules above will reset the room to public, which feels dangerous?

A new room version is not absolutely required here, but may be advisable to
ensure that servers that do not support `allowed_spaces` do not join the room
(and would also allow us to tweak the redaction rules to avoid the foot-gun).

#### Kicking users out when they leave the allowed_space

In the above example, suppose `@bob:server.example` leaves `!users:example.org`:
they should be removed from the room. One option is to leave the departure up
to Bob's server `server.example`, but this places a relatively high level of trust
in that server. Additionally, if `server.example` were offline, other users in
the room would still see Bob in the room (and their servers would attempt to
send message traffic to it).

Instead, we make the removal the responsibility of the room's admin bot (see
above): the bot is expected to peek into any `allowed_spaces` and kick any
users who are members of the room and leave the union of the allowed
spaces.

(XXX: should users in a space be kicked when that space is removed from the
`allowed_spaces` list? We think not, by analogy with what happens when you
switch the join rules from `public` to `invite`.)

One problem here is that it will lead to users who joined via an invite being
kicked. For example:
 * `@bob:server.example` creates an invite-only room.
 * Later, the `join_rules` are switched to `public`, with an `allowed_space` of
   `!users:example.org`, of which Bob happens to be a member.
 * Later still, Bob leaves `!users:example.org`.
 * Bob is kicked from his own room.

Fixing this is thorny. Some sort of annotation on the membership events might
help. but it's unclear what the desired semantics are:

 * Assuming that users in a given space are *not* kicked when that space is
   removed from `allowed_spaces`, are those users then given a pass to remain
   in the room indefinitely? What happens if the space is added back to
   `allowed_spaces` and *then* the user leaves it?

 * Suppose a user joins a room via a space (SpaceA). Later, SpaceB is added to
   the `allowed_spaces` list and SpaceA is removed. What should happen when the
   user leaves SpaceB? Are they exempt from the kick?

## Future extensions

The following sections are not blocking parts of this proposal, but are
included as a useful reference for how we imagine it will be extended in future.

### Restricting access to the spaces membership list

In the existing `/r0/groups` API, the group server has total control over the
visibility of group membership, as seen by a given querying user. In other
words, arbitrary users can see entirely different views of a group at the
server's discretion.

Whilst this is very powerful for mapping arbitrary organisational structures
into Matrix, it may be overengineered. Instead, the common case is (we believe)
a space where some users are publicly visible as members, and others are not.

One way to of achieving this would be to create a separate space for the
private members - e.g. have `#foo:matrix.org` and `#foo-private:matrix.org`.
`#foo-private:matrix.org` is set up with `m.room.history_visibility` to not to
allow peeking; you have to be joined to see the members.

### Flair

("Flair" is a term we use to describe a small badge which appears next to a
user's displayname to advertise their membership of a space.)

The flair image for a group is given by the room avatar. (In future it might
preferable to use hand-crafted small resolution images: see
[matrix-doc#1778](https://github.com/matrix-org/matrix-doc/issues/1778).

One way this might be implemented is:

 * User publishes the spaces they wish to announce on their profile
   ([MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)
   as an `m.flair` state event: it lists the spaces which they are advertising.

 * When a client wants to know the current flair for a set of users (i.e.
   those which it is currently displaying in the timeline), it peeks the
   profile rooms of those users. (Ideally there would be an API to support
   peeking multiple rooms at once to facilitate this.)

 * The client must check that the user is *actually* a member of the advertised
   spaces. Nominally it can do this by peeking the membership list of the
   space; however for efficiency we could expose a dedicated Client-Server API
   to do this check (and both servers and clients can cache the results fairly
   aggressively.)

### Inheriting join rules

If you make a parent space invite-only, should that (optionally?) cascade into
child rooms? Seems to have some of the same problems as inheriting PLs.

## Dependencies

 * [MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) for room
   types.

 * [MSC1776](https://github.com/matrix-org/matrix-doc/issues/1776) for
   effective peeking over the C/S API.

 * [MSC1777](https://github.com/matrix-org/matrix-doc/issues/1777) (or similar)
   for effective peeking over Federation.

These dependencies are shared with profiles-as-rooms
([MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)).

## Security considerations

* The peek server has significant power. TODO: expand.

* The `allowed_spaces` feature places increased trust in the servers in the
  room. We consider this acceptable: if you don't want evil servers randomly
  joining spurious users into your rooms, then a) don't let evil servers in
  your room in the first place, b) don't use `allowed_spaces` lists, given the
  expansion increases the attack surface anyway by letting members in other
  rooms dictate who's allowed into your room".

## Tradeoffs

* If the membership of a space would be large (for example: an organisation of
  several thousand people), this membership has to copied entirely into the
  room, rather than querying/searching incrementally.

* If the membership list is based on an external service such as LDAP, it is
  hard to keep the space membership in sync with the LDAP directory. In
  practice, it might be possible to do so via a nightly "synchronisation" job
  which searches the LDAP directory, or via "AD auditing".

* No allowance is made for exposing different 'views' of the membership list to
  different querying users. (It may be possible to simulate this behaviour
  using smaller spaces).

## Unstable prefix


The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`m.space.child` | event type | `org.matrix.msc1772.space.child`
`m.space.parent` | event type | `org.matrix.msc1772.space.parent`
`m.room.power_level_mappings` | event type | `org.matrix.msc1772.room.power_level_mappings`
`auto_users` | key in `m.room.power_levels` event | `org.matrix.msc1772.auto_users`


## History

 * This replaces MSC1215: https://docs.google.com/document/d/1ZnAuA_zti-K2-RnheXII1F1-oyVziT4tJffdw1-SHrE
 * Other thoughts that led into this are at: https://docs.google.com/document/d/1hljmD-ytdCRL37t-D_LvGDA3a0_2MwowSPIiZRxcabs

## Appendix: problems with the `/r0/groups` API

The existing `/r0/groups` API, as proposed in
[MSC971](https://github.com/matrix-org/matrix-doc/issues/971), has various
problems, including:

 * It is a large API surface to implement, maintain and spec - particularly for
   all the different clients out there.
 * Much of the API overlaps significantly with mechanisms we already have for
   managing rooms:
   * Tracking membership identity
   * Tracking membership hierarchy
   * Inviting/kicking/banning user
   * Tracking key/value metadata
 * There are membership management features which could benefit rooms which
   would also benefit groups and vice versa (e.g. "auditorium mode")
 * The current implementations on Riot Web/iOS/Android all suffer bugs and
   issues which have been solved previously for rooms.
   * no local-echo of invites
   * failures to set group avatars
   * ability to specify multiple admins
 * It doesn't support pushing updates to clients (particularly for flair
   membership): https://github.com/vector-im/riot-web/issues/5235
 * It doesn't support third-party invites.
 * Groups could benefit from other features which already exist today for rooms
   * e.g. Room Directories
 * Groups are centralised, rather than being replicated across all
   participating servers.



## Footnotes

<a id="f1"/>[1]: The converse, "anybody can join, provided they are not members
of the '#catlovers' space" is less useful since (a) users in the banned space
could simply leave it at any time; (b) this functionality is already somewhat
provided by [Moderation policy
lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists).  [↩](#a1)

<a id="f2"/>[2]: Note that there is nothing stopping users sending and
receiving invites in `public` rooms today, and they work as you might
expect. The only difference is that you are not *required* to hold an `invite`
when joining the room. [↩](#a2)

<a id="f3"/>[3]: This is a marginal decrease in security from the current
situation with invite-only rooms. Currently, a misbehaving server can allow
unauthorized users to join an invite-only room by first issuing an invite to
that user. In theory that can be prevented by raising the PL required to send
an invite, but in practice that is rarely done.  [↩](#a2)
