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

Synapse and Element-Web currently implement an unspecced "groups" API which
attempts to provide this functionality (see
[matrix-doc#1513](https://github.com/matrix-org/matrix-doc/issues/1513)). This
API has some serious issues:
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

In this document, the existing implementation will be referred to as
"`/r0/groups`".

This proposal suggests a new approach where spaces are themselves represented
by rooms, rather than a custom first-class entity.  This requires few server
changes, other than better support for peeking (see Dependencies below). The
existing `/r0/groups` API would be deprecated in Synapse and remain
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

We introduce an `m.space.child` state event type, which defines the rooms
within the space. The `state_key` is an alias for a child room, and `present:
true` key is included to distinguish from a deleted state event. Something
like:

```js
{
    "type": "m.space.child",
    "state_key": "#room1:example.com",
    "contents": {
        "present": true
    }
}

{
    "type": "m.space.child",
    "state_key": "#room2:example.com",
    "contents": {
        "present": true,
        "autojoin": true  // TODO: what does this mean?
    }
}

// no longer a child room
{
    "type": "m.space.child",
    "state_key": "#oldroom:example.com",
    "contents": {}
}
```

XXX if we use aliases here, and we are using it to maintain a tree of rooms in
the room list, what happens when the alias gets repointed and we don't know
about it? Maybe room IDs would be better, though the interaction with room
upgrades would need considering.

XXX Rooms also need to be able to advertise related spaces, so that users can
discover other, related, rooms.

XXX We also want to be have "secret" rooms within a heirarchy: do this with
either a "parent" state in the child, or possibly by hashing the room id?

Space-rooms may have `m.room.name` and `m.room.topic` state events in the same
way as a normal room.

Normal messages within a space-room are discouraged (but not blocked by the
server): user interfaces are not expected to have a way to enter or display
such messages.

### Membership of spaces

Users can be members of spaces (represented by `m.room.member` state events as
normal). Depending on the configuration of the space (in particular whether
`m.room.history_visibility` is set to `world_readable` or otherwise),
membership of the space may be required to view the room list, membership list,
etc.

"Public" or "community" spaces would be set to `world_readable` to allow clients
to see the directory of rooms within the space by peeking into the space-room
(thus avoiding the need to add `m.room.member` events to the event graph within
the room).

Join rules, invites and 3PID invites work as for a normal room.

### Long description

We would like to allow spaces to have a long description using rich
formatting. This will use a new state event type `m.room.description` (with
empty `state_key`) whose content is the same format as `m.room.message` (ie,
contains a `msgtype` and possibly `formatted_body`).

TODO: this could also be done via pinned messages. Failing that
`m.room.description` should probably be a separate MSC.

### Inheritance of power-levels

XXX: this section still in progress

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
                   "users": ["@superuser:matrix.org"],
                   "power_level": 100,
               },
               {
                   "spaces": ["#mods:example.org"],
                   "power_level": 50,
               }
           ]
       }
   }
   ```

   The intention would be that an automated process would peek into
   `#mods:example.org` and

   Problem 1: possibly hard to map onto a comprehensible UI?

   Problem 2: scope for getting wildly out of sync?

   Question: is it safe to use an alias to refer to a space here? What happens
   if the alias gets repointed and we don't notice?

#### Propagating changes into rooms

 * Push-based:

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

   This has the advantage that users can set up their own spaces to mirror a
   space, without having any particular control in that group. (XXX: Is that
   actually a useful feature, at least as far as PLs are concerned?)

   Problem: What do you do if the admin who sets ip the PL relationship
   disappears?  Again, either the humans have to step in and create a new
   admin, or maybe we can have multiple admins with random backoff?

   Problem 2: What if the group server you are peeking to to maintain state is
   unreachable? You could specify multiple vias for different servers via which
   you can peek?

All of the above solutions share the common problem that if the admin user
(human or virtual) loses membership or admin rights in the child room, then
the room will get out of sync.

### Membership restrictions

XXX: this section still in progress

Another desirable feature is to give room admins the power to restrict
membership of their room based on the membership of spaces<sup
id="a1">[1](#f1)</sup> (and by implication, when a user leaves the required
space, they should be ejected from the room). For example, "Any members of the
#doglovers space can join this room".

### Automated joins

XXX: this section still in progress

A related feature is: "all members of the company should automatically join the
#general room", and by extension "all users should automatically join the
#brainwashing room and may not leave".

## Future extensions

The following sections are not blocking parts of this proposal, but are
included as a useful reference for how we imagine it will be extended in future.

### Sub-spaces

Questions to be answered here include:

 * Should membership of a sub-space grant any particular access to the parent
   space, or vice-versa? We might need to extend `m.room.history_visibility` to
   support more flexibility; fortunately this is not involved in event auth so
   does not require new room versions.

 * What happens if somebody defines a cycle? (It's probably fine, but anything
   interpreting the relationships needs to be careful to limit recursion.)

XXX seems we need to un-de-scope this.

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


## Footnotes

<a id="f1"/>[1]: The converse, "anybody can join, provided they are not members
of the '#catlovers' space" is less useful since (a) users in the banned space
could simply leave it at any time; (b) this functionality is already somewhat
provided by [Moderation policy
lists](https://matrix.org/docs/spec/client_server/r0.6.1#moderation-policy-lists).  [↩](#a1)
