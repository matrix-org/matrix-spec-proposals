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

### Inheritance of power-levels

XXX: this section still in progress

XXX: make it clear that "child rooms" here are not necessarily actually children...

One use-case for spaces is to help manage power levels across a group of
rooms. For example: "Jim has just joined the management team at my company. He
should have moderator rights across all of the company rooms."

Since the event-authorisation rules cannot easily be changed, we must map any
changes in space membership onto real `m.room.power_levels` events in the child
rooms.

There are two parts to this: one, indicating the relationship, and second, the
mechanics of propagating changes into real `m.room.power_levels` events.

#### Representing the mapping from spaces to power levels

 * Option 1: list the PLs which should apply in all child rooms in an event in
   the parent. For example:

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

 * Option 2: Express the desired PLs as state in the child rooms

   This will need to be an ordered list, so that overlaps have defined behaviour:

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

   The intention would be that an automated process would peek into
   `!mods:example.org` and `!users:example.org` and generate a new
   `m.room.power_levels` event whenever the membership of either space
   changes. If a user is in both spaces, `!mods` takes priority because that is
   listed first.

   Problem 1: possibly hard to map onto a comprehensible UI?

   Problem 2: scope for getting wildly out of sync?

   XXX Question: currently there are restrictions which stop users assigning PLs
   above their own current power level. Do we need to replicate these
   restrictions? If so, that probably necessitates changes to event auth? (Does
   anyone actually make use of allowing non-admins to send PL events today?)

#### Propagating changes into rooms

Several options:

 * Push-based options:

   * We require any user who is an admin in the space (ie, anyone who has
     permission to change the access rights in the space) to also be admins
     and members of any child rooms.

     Say Bob is an admin in #doglovers and makes a change that should be
     propagated to all children of that space. His server is then responsible
     for generating a power-levels event on his behalf for each room.

     Problem: Bob may not want to be a member of all such rooms.

   * We nominate a non-human "group admin" which is responsible for propagating
     the changes into child rooms. It observes changes made in the parent space
     and performs the necessary copying actions.

     Problem: Control is now centralised on the homeserver of the admin bot. If
     that server goes down, changes are no longer propagated correctly.

   * We make it possible to specify several "group admin bot" users as above,
     on different servers. All of them must have membership and admin in all
     child rooms. Between them, they keep the child rooms in sync.

     Problem: How do the bots decide which will actually make the changes?
       * Maybe a random delay is good enough to avoid too much glare?
       * Or the humans nominate an "active" bot, with the others acting as
         standbys until they are promoted?

 * Pull-based: the user that created the relationship (or rather, their
   homeserver) is responsible for copying access controls into the room.

   This has the advantage that users can set up their own rooms to mirror a
   space, without having any particular control in that space. (XXX: Is that
   actually a useful feature, at least as far as PLs are concerned?)

   Problem: What do you do if the admin who sets up the PL relationship
   disappears?  Again, either the humans have to step in and create a new
   admin, or maybe we can have multiple admins with random backoff?

   Problem 2: What if the group server you are peeking to to maintain state is
   unreachable? You could specify multiple vias for different servers via which
   you can peek?

All of the above solutions share the common problem that if the admin user
(human or virtual) loses membership or admin rights in the child room, then
the room will get out of sync.

#### Supporting traditional PL assignments in addition to those derived from spaces

When a user departs from a space, we expect the automated mapper process to
remove any power-levels that were granted to that user by virtue of being a
member of the space. The question arises of how the mapper can distinguish
between power-levels that were granted manually using the traditional
mechanism (so should not be changed) and those that were inherited from the
space and should be removed.

Options:

 * Add a new field to `power_levels` for automatically-maintained power
   levels. For example:

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

   This would require changes to the event authorization rules, and hence
   require a new room version.

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

### Membership restrictions

A desirable feature is to give room admins the power to restrict membership of
their room based on the membership of spaces (for example, "only members of the
#doglovers space can join this room"<sup id="a1">[1](#f1)</sup>).

XXX can we maybe do this with invites generated on demand? If not, we probably
need some sort of "silent invite" state for each user,

By implication, when a user leaves the required space, they should be ejected
from the room.

XXX: how do we implement the ejection? We could leave it up to the ejectee's
server, but what happens if it doesn't play the game? So we probably need to
enact a ban... but then, which server has responisiblity, and which user is used?


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

While this proposal is not in a published version of the specification,
implementations should use `org.matrix.msc1772` to represent the `m`
namespace. For example, `m.space.child` becomes
`org.matrix.msc1772.space.child`.

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
