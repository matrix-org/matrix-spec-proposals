Room History Visibility
=======================

.. _module:history-visibility:

This module adds support for controlling the visibility of previous events in a
room.

In all cases except ``world_readable``, a user needs to join a room to view events in that room. Once they
have joined a room, they will gain access to a subset of events in the room. How
this subset is chosen is controlled by the ``m.room.history_visibility`` event
outlined below. After a user has left a room, they may seen any events which they
were allowed to see before they left the room, but no events received after they
left.

The four options for the ``m.room.history_visibility`` event are:

- ``shared`` - Previous events are always accessible to newly joined members. All
  events in the room are accessible, even those sent when the member was not a part
  of the room.
- ``invited`` - Previous events are accessible to newly joined members from the point
  they were invited onwards. Events stop being accessible when the member's state
  changes to something other than ``invite`` or ``join``.
- ``joined`` - Previous events are accessible to newly joined members from the point
  they joined the room onwards. Events stop being accessible when the member's state
  changes to something other than ``join``.
- ``world_readable`` - All events while this is the ``m.room.history_visibility`` value
  may be shared by any participating homeserver with anyone, regardless of whether
  they have ever joined the room.

.. WARNING::
  These options are applied at the point an event is *sent*. Checks are
  performed with the state of the ``m.room.history_visibility`` event when the
  event in question is added to the DAG. This means clients cannot
  retrospectively choose to show or hide history to new users if the setting at
  that time was more restrictive.

Events
------

{{m_room_history_visibility_event}}

Client behaviour
----------------

Clients that implement this module MUST present to the user the possible options
for setting history visibility when creating a room. 

Clients may want to display a notice that their events may be read by non-joined
people if the value is set to ``world_readable``.

Server behaviour
----------------

By default if no ``history_visibility`` is set, or if the value is not understood, the visibility is assumed to be
``shared``. The rules governing whether a user is allowed to see an event depend
solely on the state of the room *at that event*:

1. If the user was joined, allow.
2. If the user was invited and the ``history_visibility`` was set to
   ``invited`` or ``shared``, allow.
3. If the user was neither invited nor joined but the ``history_visibility``
   was set to ``shared``, allow.
4. Otherwise, deny.

Security considerations
-----------------------

The default value for ``history_visibility`` is ``shared`` for
backwards-compatibility reasons. Clients need to be aware that by not setting
this event they are exposing all of their room history to anyone in the room.

