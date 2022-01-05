---
type: module
---

### Room History Visibility

This module adds support for controlling the visibility of previous
events in a room.

In all cases except `world_readable`, a user needs to join a room to
view events in that room. Once they have joined a room, they will gain
access to a subset of events in the room. How this subset is chosen is
controlled by the `m.room.history_visibility` event outlined below.
After a user has left a room, they may see any events which they were
allowed to see before they left the room, but no events received after
they left.

The four options for the `m.room.history_visibility` event are:

-   `world_readable` - All events while this is the
    `m.room.history_visibility` value may be shared by any participating
    homeserver with anyone, regardless of whether they have ever joined
    the room.
-   `shared` - Previous events are always accessible to newly joined
    members. All events in the room are accessible, even those sent when
    the member was not a part of the room.
-   `invited` - Events are accessible to newly joined members from the
    point they were invited onwards. Events stop being accessible when
    the member's state changes to something other than `invite` or
    `join`.
-   `joined` - Events are accessible to newly joined members from the
    point they joined the room onwards. Events stop being accessible
    when the member's state changes to something other than `join`.

{{% boxes/warning %}}
These options are applied at the point an event is *sent*. Checks are
performed with the state of the `m.room.history_visibility` event when
the event in question is added to the DAG. This means clients cannot
retrospectively choose to show or hide history to new users if the
setting at that time was more restrictive.
{{% /boxes/warning %}}

#### Events

{{% event event="m.room.history_visibility" %}}

#### Client behaviour

Clients that implement this module MUST present to the user the possible
options for setting history visibility when creating a room.

Clients may want to display a notice that their events may be read by
non-joined people if the value is set to `world_readable`.

#### Server behaviour

By default if no `history_visibility` is set, or if the value is not
understood, the visibility is assumed to be `shared`. The rules
governing whether a user is allowed to see an event depend on the state
of the room *at that event*.

1.  If the `history_visibility` was set to `world_readable`, allow.
2.  If the user's `membership` was `join`, allow.
3.  If `history_visibility` was set to `shared`, and the user joined the
    room at any point after the event was sent, allow.
4.  If the user's `membership` was `invite`, and the
    `history_visibility` was set to `invited`, allow.
5.  Otherwise, deny.

For `m.room.history_visibility` events themselves, the user should be
allowed to see the event if the `history_visibility` before *or* after
the event would allow them to see it. (For example, a user should be
able to see `m.room.history_visibility` events which change the
`history_visibility` from `world_readable` to `joined` *or* from
`joined` to `world_readable`, even if that user was not a member of the
room.)

Likewise, for the user's own `m.room.member` events, the user should be
allowed to see the event if their `membership` before *or* after the
event would allow them to see it. (For example, a user can always see
`m.room.member` events which set their membership to `join`, or which
change their membership from `join` to any other value, even if
`history_visibility` is `joined`.)

#### Security considerations

The default value for `history_visibility` is `shared` for
backwards-compatibility reasons. Clients need to be aware that by not
setting this event they are exposing all of their room history to anyone
in the room.
