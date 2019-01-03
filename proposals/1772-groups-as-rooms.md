# Proposal for groups as rooms (take 2)

This obsoletes MSC1215.

## Problem

The current groups API has some serious issues:
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
 * It doesn't support third party invites.
 * Groups could benefit from other features which already exist today for rooms
   * e.g. Room Directories
 * Groups are centralised, rather than being existing across multiple
   participating servers.

## Solution

Represent groups by rooms rather than a custom first-class entity.

We reserve aliases which begin with a `+` to represent groups - e.g. the room
for group `+test:example.com` is `#+test:example.com`.

We introduce a `m.room.groups` state event which defines how a room should
behave as a group - i.e. the rooms which it groups together, and any subgroups
nested within it.

```json
{
    "type": "m.room.groups",
    "contents": {
        "rooms": [
            {
                "room": "#room1:example.com",
            },
            {
                "room": "#room2:example.com",
                "autojoin": true
            },
            {
                "room": "#room3:example.com",
            },
        ],
        "subgroups": [
            {
                "group": "+something:example.com",
            },
            {
                "group": "+otherthing:example.com",
            },
        ]
    },
}
```

Name, Topic, Membership etc share the same events as a normal room.

The flair for a group is given by the room avatar.

Long description requires a new event: `m.room.description`.  This can also be
used for rooms as well as groups.

Groups may be nested, and membership of groups is defined as the union of the
members of the group room and its subgroups.  If `+top:example.com` has two
subgroups, the user membership of `+top:example.com` is the union of the
subgroups and the group itself.  This allows hierarchies of groups & users to be
defined.

Clients peek in rooms (recursing into subgroups as needed) in order to determine
group membership.

Invites, 3PID invites, Power Levels etc all work as for a normal room.

Normal messages within the room could be showed and used as a 'lobby' area for
the given group.

This requires no server changes at all, other than better support for peeking
(see Dependencies below), and could allow the existing /groups API to be
deprecated and removed outright.

## ACLs

Currently the group server has total control over specifying the list of users
who may be present in a group, as seen by a given querying user. In other words,
arbitrary users can see entirely different views of a group at the server's
discretion.

Whilst this is very powerful for mapping arbitrary group structures into Matrix,
it may be overengineered.

Instead, the common case is wanting to define a group where some users are
publicly visible as members, and others are not.  This is what the current use
cases require today.  A simple way of achieving would be to create a subgroup
for the private members - e.g. have +sensitive:matrix.org and +sensitive-
private:matrix.org.  The membership of `+sensitive-private:matrix.org` is set up
with `m.room.join_rules` to not to allow peeking; you have to be joined to see
the members, and users who don't want to be seen by the public to be member of
the group are added to the subgroup.

XXX: is there a use case today for having a group where users are unaware of the
other users' membership?  e.g. if I am a member of `+scandalous:matrix.org`
should i have a way to stop other members knowing that I am?  One solution here
could be "auditorium mode", where users cannot see other users' identities
(unless they speak).   This could be added later, however, and would also be
useful for normal rooms.

## Flair

TODO: We need to establish how users should safely advertise their flair.
Perhaps they can claim whatever flair they like on their profile (MSC1769) and
clients need to then doublecheck whether the assertion is true by peeking in the
room in question to check it's true?

## Dependencies

This needs peeking to work effectively on CS API.

This needs peeking to work effectively over federation (e.g. by having servers
join remote rooms as @null:example.com in order to participate in them for
peeking purposes).

These dependencies are shared with profiles-as-rooms (MSC1769).

## Security considerations

XXX: how do we stop cycles & recursion abuse of the subgroups?

## Tradeoffs

This consciously sacrifices the ability to delegate group lookups through
to a centralised group server.  However, group data can already be stale as we
rely on cached attestations from federated servers to apply ACLs even if the
remote server is not available.  So this isn’t much worse than eventually
consistent group membership as you’d find in a room.

It also means that large groups have to be bridged in their entirety into the
room, rather than querying/searching incrementally.  This is something we should
fix for bridged rooms in general too, however.

This also consciously sacrifices the ability for a group server to provide
different 'views' of groups to different querying users, as being
overengineered.  Instead, all common use cases should be modellable by modelling
group memnbership as room membership (nesting if required).

## Issues

How does this work with MSC1229 (removing MXIDs)?

## History

This replaces MSC1215: https://docs.google.com/document/d/1ZnAuA_zti-K2-RnheXII1F1-oyVziT4tJffdw1-SHrE
Other thoughts that led into this are at: https://docs.google.com/document/d/1hljmD-ytdCRL37t-D_LvGDA3a0_2MwowSPIiZRxcabs