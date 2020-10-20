# Proposal for groups as rooms (take 2)

This obsoletes [MSC1215](https://github.com/matrix-org/matrix-doc/issues/1215).

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
 * Groups are centralised, rather than being replicated across all
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

XXX: alternatively, perhaps all the rooms and subgroups should be their own
state event with a unique state key, ensuring that this can scale to large
groups and doesn't have to be edited atomically. A key like `present: true`
would be needed to distinguish from a deleted state event. Something like:

```json
{
    "type": "m.room.group",
    "state_key": "#room1:example.com",
    "contents": {
        "present": true
    }
}

{
    "type": "m.room.group",
    "state_key": "#room2:example.com",
    "contents": {
        "present": true,
        "autojoin": true
    }
}

{
    "type": "m.room.subgroup",
    "state_key": "+something:example.com",
    "contents": {
        "present": true
    }
}
{
    "type": "m.room.subgroup",
    "state_key": "+otherthing:example.com",
    "contents": {
        "present": true
    }
}
```

Name, Topic, Membership etc share the same events as a normal room.

The flair image for a group is given by the room avatar. (In future it might
preferable to use hand-crafted small resolution images: see
[matrix-doc#1778](https://github.com/matrix-org/matrix-doc/issues/1778).

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
for the private members - e.g. have `+sensitive:matrix.org` and
`+sensitive-private:matrix.org`.  The membership of
`+sensitive-private:matrix.org` is set up with `m.room.join_rules` to not to
allow peeking; you have to be joined to see the members, and users who don't
want to be seen by the public to be member of the group are added to the
subgroup.

XXX: is there a use case today for having a group where users are unaware of the
other users' membership?  e.g. if I am a member of `+scandalous:matrix.org`
should i have a way to stop other members knowing that I am?  One solution here
could be "auditorium mode", where users cannot see other users' identities
(unless they speak).   This could be added later, however, and would also be
useful for normal rooms.

## Flair

A proposal for how to safely determine user flair is:

 * User publishes the groups they wish to announce on their profile
   ([MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)
   as a m.flair state event: it lists the groups which they are advertising.

 * When a client wants to know the current flair for a set of users (i.e.
   those which it is currently displaying in the timeline), it peeks the
   profile rooms of those users.  However, we can't trust the flair which the
   users advertise on the profile - it has to be cross-referenced from the
   memberships of the groups in question.

To do this cross-referencing, options are:

 1. The client checks the group membership (very inefficient, given the server
    could/should do it for them), or...
 2. The server checks the group membership by peeking the group and somehow
    decorates the `m.flair` event as validated before sending it to the client.
    This is also inefficient, as it forces the server to peek a potentially large
    group (unless we extend federation to allow peeking specific state events)
 3. The origin `m.flair` event includes the event_id of the user's
    `m.room.membership` event in the group.  The server performing the check can
    then query this specific event from one of the servers hosting the group-room,
    and we perhaps extend the S2S API to say whether a given state event is current
    considered current_state or not.  If the `m.room.membership` event is confirmed
    as current, then the `m.flair` is decorated as being confirmed.

Of these, option 3 feels best?

## Dependencies

This needs peeking to work effectively over the CS API
([MSC1776](https://github.com/matrix-org/matrix-doc/issues/1776)).

This needs peeking to work effectively over federation (e.g. by having servers
join remote rooms as `@null:example.com` in order to participate in them for
peeking purposes - [MSC1777](https://github.com/matrix-org/matrix-doc/issues/1777)).

These dependencies are shared with profiles-as-rooms
([MSC1769](https://github.com/matrix-org/matrix-doc/issues/1769)).

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
group membership as room membership (nesting if required).

## Issues

How does this work with
[MSC1228](https://github.com/matrix-org/matrix-doc/issues/1228) (removing MXIDs)?

## Unstable prefix

While this proposal is not in a published version of the specification,
implementations should use `org.matrix.msc1772` to represent the `m`
namespace. For example, `m.room.subgroup` becomes
`org.matrix.msc1772.room.subgroup`.


## History

 * This replaces MSC1215: https://docs.google.com/document/d/1ZnAuA_zti-K2-RnheXII1F1-oyVziT4tJffdw1-SHrE
 * Other thoughts that led into this are at: https://docs.google.com/document/d/1hljmD-ytdCRL37t-D_LvGDA3a0_2MwowSPIiZRxcabs
