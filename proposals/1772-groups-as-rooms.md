# Proposal for Matrix "spaces" (formerly known as "groups as rooms (take 2)")

This MSC, and related proposals, supersede
[MSC1215](https://github.com/matrix-org/matrix-doc/issues/1215).

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
[MSC971](https://github.com/matrix-org/matrix-doc/issues/971)). However,
this is a complex API which has various problems (see
[appendix](#appendix-problems-with-the-r0groups-api)).

This proposal suggests a new approach where spaces are themselves represented
by rooms, rather than a custom first-class entity.  This requires minimal
server changes.

The existing `/r0/groups` API would be deprecated in Synapse and remain
unspecified.

## Proposal

Each space is represented by its own room, known as a "space-room". The rooms
within the space are determined by state events within the space-room.

Space-rooms are distinguished from regular messaging rooms by the presence of
a `'type': 'm.space'` property in the content of the `m.room.create` event.
The value of the `type` property uses the Standardised Identifier Grammar from
[MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758). This allows clients to offer slightly customised user experience
depending on the purpose of the room. Currently, no server-side behaviour is
expected to depend on this property.  A `type` property on the `m.room.create`
event is used to ensure that a room cannot change between being a space-room
and a non-space room. For more information, see the "Rejected Alternatives"
section below. Additionally, no client behaviour is recommended for handling
unknown room types given the potential for legacy data: clients are free to
make their own decisions about hiding unknown room types from users, though
should note that a future conversation-like type (for example) might be
introduced and could be considered "unknown" by older versions of their client.

As with regular rooms, public spaces are expected to have an alias, for example
`#foo:matrix.org`, which can be used to refer to the space.

Space-rooms may have `m.room.name`, `m.room.avatar` and `m.room.topic` state
events in the same way as a normal room.

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
membership list, etc. "Public" or "community" spaces would be set to
`world_readable` to allow clients to see the directory of rooms within the
space by peeking into the space-room (thus avoiding the need to add
`m.room.member` events to the event graph within the room).

Join rules, invites and 3PID invites work as for a normal room.  In order for
clients to distinguish space invites from room invites, all invites must now
include the `m.room.create` event in their `invite_state` and `knock_state`.

### Relationship between rooms and spaces

The intention is that rooms and spaces form a hierarchy, which clients can use
to structure the user's room list into a tree view. The parent/child
relationship can be expressed in one of two ways:

 1. The admins of a space can advertise rooms and subspaces for their space by
    setting `m.space.child` state events. The `state_key` is the ID of a child
    room or space, and the content must contain a `via` key which gives a list
    of candidate servers that can be used to join the room. Something like:

    ```jsonc
    // a child room
    {
        "type": "m.space.child",
        "state_key": "!abcd:example.com",
        "content": {
            "via": ["example.com", "test.org"]
        }
    }

    // a child room with an ordering.
    {
        "type": "m.space.child",
        "state_key": "!efgh:example.com",
        "content": {
            "via": ["example.com"],
            "order": "abcd"
        }
    }

    // no longer a child room
    {
        "type": "m.space.child",
        "state_key": "!jklm:example.com",
        "content": {}
    }
    ```

    Children where `via` is not present or invalid (not an array) are ignored.

    The `order` key is a string which is used to provide a default ordering of
    siblings in the room list. (Rooms are sorted based on a lexicographic
    ordering of the Unicode codepoints of the characters in `order` values.
    Rooms with no `order` come last with no effective `order`. When the `order`
    (or lack thereof) is the same, the rooms are sorted in ascending numeric
    order of the `origin_server_ts` of their `m.room.create` events, or ascending
    lexicographic order of their `room_id`s in case of equal
    `origin_server_ts`.  `order`s which are not strings, or do not consist
    solely of ascii characters in the range `\x20` (space) to `\x7E` (`~`), or
    consist of more than 50 characters, are forbidden and the field should be
    ignored if received.)

 2. Separately, rooms can claim parents via the `m.space.parent` state
    event.

    Similar to `m.space.child`, the `state_key` is the ID of the parent space,
    and the content must contain a `via` key which gives a list of candidate
    servers that can be used to join the parent.

    ```jsonc
    {
        "type": "m.space.parent",
        "state_key": "!space:example.com",
        "content": {
            "via": ["example.com"],
            "canonical": true
        }
    }
    ```

    Parents where `via` is not present or invalid (not an array) are ignored.

    `canonical` determines whether this is the main parent for the space. When
    a user joins a room with a canonical parent, clients may switch to view the
    room in the context of that space, peeking into it in order to find other
    rooms and group them together.  In practice, well behaved rooms should only
    have one `canonical` parent, but given this is not enforced: if multiple
    are present the client should select the one with the lowest room ID, as
    determined via a lexicographic ordering of the Unicode code-points.

    To avoid abuse where a room admin falsely claims that a room is part of a
    space that it should not be, clients could ignore such `m.space.parent`
    events unless either (a) there is a corresponding `m.space.child` event in
    the claimed parent, or (b) the sender of the `m.space.parent` event has a
    sufficient power-level to send such an `m.space.child` event in the
    parent. (It is not necessarily required that that user currently be a
    member of the parent room - only the `m.room.power_levels` event is
    inspected.) [Checking the power-level rather than requiring an *actual*
    `m.space.child` event in the parent allows for "secret" rooms (see below).]

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
encountered, and MUST spot and break cycles rather than infinitely looping.

### Suggested children

Space admins can mark particular children of a space as "suggested". This
mainly serves as a hint to clients that that they can be displayed differently
(for example by showing them eagerly in the room list), though future
server-side interfaces (such as the summary API proposed in
[MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946)) might also
make use of it.

A suggested child is identified by a `"suggested": true` property in the
`m.space.child` event:


```jsonc
{
    "type": "m.space.child",
    "state_key": "!abcd:example.com",
    "content": {
        "via": ["example.com", "test.org"],
        "suggested": true
    }
}
```

A child which is missing the `suggested` property is treated identically to a
child with `"suggested": false`. A suggested child may be a room or a subspace.

### Extended "room invite state"

The specification is currently vague about what room state should be available
to users that have been invited to a room, though the Federation API spec does
recommend that the `invite_room_state` sent over federation via [PUT
`/_matrix/federation/v2/invite`](https://matrix.org/docs/spec/server_server/r0.1.4#put-matrix-federation-v2-invite-roomid-eventid)
should include "the join rules, canonical alias, avatar, and name of the room".

This MSC proposes adding `m.room.create` to that list, so that the recipient of
an invite can distinguish invites to spaces from other invites.

## Future extensions

The following sections are not blocking parts of this proposal, but are
included as a useful reference for how we imagine it will be extended in future.

### Auto-joined children

We could add an `auto_join` flag to `m.space.child` events to allow a space
admin to list the sub-spaces and rooms in that space which should be
automatically joined by members of that space.

This would be distinct from a force-join: the user could subsequently part any
auto-joined room if they desire.

Joining would be performed by the client.  This could possibly be sped up by
using a summary API (such as that proposed in
[MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946)) to get a summary
of the spacetree to be joined, and then using a batch join API to join
whichever subset of it makes most sense for the client's UX.

Obviously auto-joining can be a DoS vector, and we consider it to be antisocial
for a space to try to autojoin its members to more than 100 children (in total).

Clients could display the auto-joined children in the room list whenever the
space appears in the list - thus helping users discover other rooms in a space
even if they're not joined to that space.  For instance, if you join
`#matrix:matrix.org`, your client could show that room in the context of its
parent space, with that space's auto-joined children shown alongside it as
siblings.

### Restricting access to the spaces membership list

In the existing `/r0/groups` API, the group server has total control over the
visibility of group membership, as seen by a given querying user. In other
words, arbitrary users can see entirely different views of a group at the
server's discretion.

Whilst this is very powerful for mapping arbitrary organisational structures
into Matrix, it may be overengineered. Instead, the common case is (we believe)
a space where some users are publicly visible as members, and others are not.

One way of achieving this would be to create a separate space for the
private members - e.g. have `#foo:matrix.org` and `#foo-private:matrix.org`.
`#foo-private:matrix.org` is set up with `m.room.history_visibility` to not to
allow peeking; you have to be joined to see the members.

It's worth noting that any member of a space can currently see who else is a
member of that space, which might pose privacy problems for sensitive spaces.
While the server itself will inevitably track the space membership in state
events, a future MSC could restrict the membership from being sent to clients.
This is essentially the same as
[matrix-doc#1653](https://github.com/matrix-org/matrix-doc/issues/1653).

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

## Related MSCs

 * [MSC2946](https://github.com/matrix-org/matrix-doc/issues/2946): Spaces
   Summary API.

 * [MSC2962](https://github.com/matrix-org/matrix-doc/issues/2962): Managing
   power levels via Spaces.

 * [MSC3083](https://github.com/matrix-org/matrix-doc/issues/3083): Restricting
   room membership based on space membership.

 * [MSC2753](https://github.com/matrix-org/matrix-doc/issues/2753) for
   effective peeking over the C/S API.

 * [MSC2444](https://github.com/matrix-org/matrix-doc/issues/2444) (or similar)
   for effective peeking over Federation.

## Security considerations

None at present.

## Potential issues

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

* The requirement that `m.space.parent` links be ignored unless the sender has a
  high PL in the parent room could lead to surprising effects where a parent
  link suddenly ceases to take effect because a user loses their PL in the
  parent room. This is mitigated in the general case by honouring the parent
  link when there is a corresponding `m.space.child` event, however it remains
  a problem for "secret" rooms.

* The `via` servers listed in the `m.space.child` and `m.space.parent` events
  could get out of date, and will need to be updated from time to time. This
  remains an unsolved problem.

## Rejected alternatives

### Use a separate state event for type of room

[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) proposes the use
of a separate `m.room.type` state event to distinguish different room types.
This implies that rooms can dynamically switch between being a Space, and
being a regular non-Space room. That is not a usecase we consider useful, and
allowing it would impose significant complexity on client and server
implementations. Specifically, client and server implementations who store
spaces separately from rooms would have to support migrating back and forth
between them and dealing with the ambiguities of `room_id`s no longer pointing
to valid spaces, etc.

### Use a different sigil/twigil for spaces

Groups used + as a sigil to differentiate them from rooms (e.g. +matrix:matrix.org).
We considered doing similar for Spaces, e.g. a #+ twigil or reuse the + sigil,
but concluded that the resulting complexity and exoticism is not worth it.
This means that clients such as matrix.to have to peek into rooms to find out their
`type` before being able to display an appropriate UI, and users will not know
whether #matrix:matrix.org is a room or a space without using a client (e.g. if
reading an advert).  It also means that if the client UI requires a space alias the
client will need to validate the entered data serverside.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during
development:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`type` | property in `m.room.create` | `org.matrix.msc1772.type`
`m.space` | value of `type` in `m.room.create` | `org.matrix.msc1772.space`
`m.space.child` | event type | `org.matrix.msc1772.space.child`
`m.space.parent` | event type | `org.matrix.msc1772.space.parent`

## History

 * This replaces [MSC1215](https://docs.google.com/document/d/1ZnAuA_zti-K2-RnheXII1F1-oyVziT4tJffdw1-SHrE).
 * Other thoughts that led into this are [documented](https://docs.google.com/document/d/1hljmD-ytdCRL37t-D_LvGDA3a0_2MwowSPIiZRxcabs).

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
