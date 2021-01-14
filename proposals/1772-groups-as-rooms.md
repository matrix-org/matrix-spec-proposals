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
[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840)). This allows
clients to offer slightly customised user experience depending on the purpose
of the room.

Space-rooms may have `m.room.name` and `m.room.topic` state events in the same
way as a normal room.

Normal messages within a space-room are discouraged (but not blocked by the
server): user interfaces are not expected to have a way to enter or display
such messages.  Space-rooms should be created with a power level for
`events_default` of 100, to prevent the rooms accidentally/maliciously
clogging up with messages from random members of the space.

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

Join rules, invites and 3PID invites work as for a normal room, with the
exception that `invite_state` sent along with invites should be amended to
include the event containing the type `m.space`, to allow clients to discern
whether an invite is to a space-room or not.

XXX: Should we also include a MSC2946 summary of the space in the invite too?

### Relationship between rooms and spaces

The intention is that rooms and spaces form a hierarchy, which clients can use
to structure the user's room list into a tree view. The parent/child
relationship can be expressed in one of two ways:

 1. The admins of a space can advertise rooms and subspaces for their space by
    setting `m.space.child` state events. The `state_key` is the ID of a child
    room or space, and the content should contain a `via` key which gives a list
    of candidate servers that can be used to join the room. Something like:

    ```js
    {
        "type": "m.space.child",
        "state_key": "!abcd:example.com",
        "content": {
            "via": ["example.com", "test.org"]
        }
    }

    {
        "type": "m.space.child",
        "state_key": "!efgh:example.com",
        "content": {
            "via": ["example.com"],
            "order": "abcd",
            "auto_join": true
        }
    }

    // no longer a child room
    {
        "type": "m.space.child",
        "state_key": "!jklm:example.com",
        "content": {}
    }
    ```

    Children where `via` is not present are ignored.

    The `order` key is a string which is used to provide a default ordering of
    siblings in the room list. (Rooms are sorted based on a lexicographic
    ordering of `order` values; rooms with no `order` come last. `order`s which
    are not strings, or do not consist solely of ascii characters in the range
    `\x20` (space) to `\x7F` (`~`), or consist of more than 50 characters, are
    forbidden and should be ignored if received.)

    If `auto_join` is set to `true`, that indicates that the child should be
    automatically joined by members of the space: see
    [below](#auto-joined-children).

 2. Separately, rooms can claim parents via the `m.space.parent` state
    event.

    Similar to `m.space.child`, the `state_key` is the ID of the parent space,
    and the content should contain a `via` key which gives a list of candidate
    servers that can be used to join the parent.

    ```js
    {
        "type": "m.space.parent",
        "state_key": "!space:example.com",
        "content": {
            "via": ["example.com"],
            "present": true,
            "canonical": true,
        }
    }
    ```

    Parents where `via` is not present are ignored.

    `canonical` determines whether this is the main parent for the space. When
    a user joins a room with a canonical parent, clients may switch to view
    the room in the context of that space, peeking into it in order to find
    other rooms and group them together.  In practice, well behaved rooms
    should only have one `canonical` parent, but given this is not enforced:
    if multiple are present the client should select the one with the lowest
    room ID, as determined via a lexicographic utf-8 ordering.

    To avoid abuse where a room admin falsely claims that a room is part of a
    space that it should not be, clients could ignore such `m.space.parent`
    events unless their sender has a sufficient power-level to send an
    `m.space.child` event in the parent. The rationale for checking the power
    level, rather than the *actual* presence of an `m.space.child` event in the
    parent, is to accommodate "secret" rooms (see below).

    Where the parent space also claims a parent, clients can recursively peek
    into the grandparent space, and so on.

This structure means that rooms can end up appearing multiple times in the
room list hierarchy, given they can be children of multiple different spaces
(or have multiple parents in different spaces).

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

XXX: we need to deterministically specify where the cycles get cut.
I think kegan found a solution for this when implementing MSC2946 in Dendrite.

XXX: we need to specify how vias are updated as time goes on (perhaps servers
with sufficient permission could automatically add themselves into the via event
via the bot from MSC2962?)

### Auto-joined children

The `auto_join` flag on a child listing allows a space admin to list the
sub-spaces and rooms in that space which should be automatically joined by
members of that space.  (This is not a force-join, which are descoped for
a future MSC; the user can subsequently part these room if they desire.)

Joining should be performed by the client.  This can optionally be sped up by
using [MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946) to get a
summary of the spacetree to be joined, and then using a batch join API (when
available) to join whichever subset of it makes most sense for the client's
UX.

Obviously auto-joining can be a DoS vector, and we consider it to be antisocial
for a space to try to autojoin its members to more than 100 children (in total).

Clients could display the auto-joined children in the room list whenever the
space appears in the list - thus helping users discover other rooms in a space
even if they're not joined to that space.  For instance, if you join
`#matrix:matrix.org`, your client could show that room in the context of its
parent space, with that space's autojoined children shown alongside it as
siblings.

It may also be useful to have a way to "suggest" that members of a space
should join certain children (but without actually autojoining them) - to
advertise particular rooms more prominently than in the room directory.
However, this can be added in a later MSC if it's found to be needed in
practice.

### Long description

We would like to allow spaces to have a long description using rich
formatting. This will use a new state event type `m.room.description` (with
empty `state_key`) whose content is the same format as `m.room.message` (ie,
contains a `msgtype` and possibly `formatted_body`).

TODO: this could also be done via pinned messages. Failing that
`m.room.description` should probably be a separate MSC.

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

## Dependencies

 * [MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) for room
   types.

 * [MSC2753](https://github.com/matrix-org/matrix-doc/issues/2753) for
   effective peeking over the C/S API.

 * [MSC2444](https://github.com/matrix-org/matrix-doc/issues/2444) (or similar)
   for effective peeking over Federation.

These dependencies are shared with profiles-as-rooms
([MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)).

## Security considerations

* The peek server has significant power. For example, a poorly chosen peek
  server could lie about the space membership and add an
  `@evil_user:example.org`.

## Tradeoffs

* If the membership of a space would be large (for example: an organisation of
  several thousand people), this membership has to be copied entirely into the
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
`m.space` | room type | `org.matrix.msc1772.space`
`m.space.child` | event type | `org.matrix.msc1772.space.child`
`m.space.parent` | event type | `org.matrix.msc1772.room.parent`

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
