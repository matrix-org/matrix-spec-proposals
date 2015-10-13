Room History Visibility
=======================

.. _module:history-visibility:

This module adds support for controlling the visibility of previous events in a
room. Whether a member of a room can see the events that happened in a room from
before they joined the room is controlled by the ``m.room.history_visibility``
event outlined below. In all cases, the member still needs to be joined to the
room to receive events for that room. The visibility option simply determines
which subset of events in the room are presented to the client. Visibility can
take the form of one of three options:

- ``shared`` - Previous events are always shown to newly joined members. All
  events in the room are shown, even those sent when the member was not a part
  of the room.
- ``invited`` - Previous events are shown to newly joined members from the point
  they were invited onwards. Events stop being shown when the member's state
  changes to something other than ``invite`` or ``join``.
- ``joined`` - Previous events are shown to newly joined members from the point
  they joined the room onwards. Events stop being shown when the members state
  changes to something other than ``join``.

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

Server behaviour
----------------

By default if no ``history_visibility`` is set the visibility is assumed to be
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

