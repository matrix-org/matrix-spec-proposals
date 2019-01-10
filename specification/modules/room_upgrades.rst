.. Copyright 2019 New Vector Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Room Upgrades
=============

.. _module:room-upgrades:

From time to time, a room may need to be upgraded to a different room version for a
variety for reasons. This module defines a way for rooms to upgrade to a different
room version when needed.

Events
------

{{m_room_tombstone_event}}

Client behaviour
----------------

Clients which understand ``m.room.tombstone`` events MUST:

* Hide the old room from the user's list of rooms. Permalinks, backlinks, etc should
  still be accessible to this room, however.
* At the very bottom of the old room's timeline/message view, display a message which
  indicates the room has been upgraded with a permalink to the new room. When the user
  accesses the permalink, they are to be joined to the new room.

  * Note that if the homeserver doesn't support the room version that the user may
    receive an error upon trying to join.
  * If the replacement room has a tombstone event, the client may automatically follow
    the chain until it finds a room which does not have a tombstone in it.

* Optionally, the client may wish to improve the presentation of unread messages when
  the user is in both the old and new rooms. For example, if the user was not active
  during the upgrade and had unread messages in the old room, the new room may have an
  indicator which shows the sum of unread notifications between the rooms.

Clients which understand ``m.room.tombstone`` events must also understand the ``predecessor``
field on ``m.room.create`` events such that:

* At the top of the scrollback/message view for the new room a message is displayed
  indicating that the room is a continuation of a previous room, with a permalink to
  the old room.
* Optionally supporting search and other functions of the room to span across the old
  and new rooms.

{{room_upgrades_cs_http_api}}

Server behaviour
----------------

When the client requests to upgrade a known room to a known version, the server:

1. Checks that the user has permission to send ``m.room.tombstone`` events in the room.
2. Creates a replacement room with a ``m.room.create`` event containing a ``predecessor``
   field and the applicable ``room_version``.
3. Replicates the power levels, privacy, topic, and other transferable state events to
   the new room. This generally excludes membership events.
4. Moves any local aliases to the new room.
5. Sends a ``m.room.tombstone`` event to the old room to indicate that it is not intended
   to be used any further.
6. If possible, the power levels in the old room should also be modified to prevent sending
   of events and inviting new users. For example, setting ``events_default`` and ``invite``
   to the greater of ``50`` and ``users_default + 1``.
