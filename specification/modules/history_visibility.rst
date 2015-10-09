Room History Visibility
=======================

.. _module:history-visibility:

This module adds support for controlling the visibility of previous events in a
room. Whether a member of a room can see the events that happened in a room from
before they joined the room is controlled by the ``m.room.history_visibility``
event outlined below. Visibility can take the form of one of three options:

- ``shared`` - Previous events are always shown to newly joined members.
- ``invited`` - Previous events are shown to newly joined members from the point
  they were invited onwards.
- ``joined`` - Previous events are shown to newly joined members from the point
  they joined the room onwards.

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

