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

Clients which understand ``m.room.tombstone`` events and the ``predecessor`` field on
``m.room.create`` events should communicate to the user that the room was upgraded.
One way of accomplishing this would be hiding the old room from the user's room list
and showing banners linking between the old and new room - ensuring that permalinks
work when referencing the old room. Another approach may be to virtually merge the
rooms such that the old room's timeline seamlessly continues into the new timeline
without the user having to jump between the rooms.

{{room_upgrades_cs_http_api}}

Server behaviour
----------------

When the client requests to upgrade a known room to a known version, the server:

1. Checks that the user has permission to send ``m.room.tombstone`` events in the room.
2. Creates a replacement room with a ``m.room.create`` event containing a ``predecessor``
   field and the applicable ``room_version``.
3. Replicates transferable state events to the new room. The exact details for what is
   transferred is left as an implementation detail, however the recommended state events
   to transfer are:

   * ``m.room.server_acl``
   * ``m.room.encryption``
   * ``m.room.name``
   * ``m.room.avatar``
   * ``m.room.topic``
   * ``m.room.guest_access``
   * ``m.room.history_visibility``
   * ``m.room.join_rules``
   * ``m.room.power_levels``

   Membership events should not be transferred to the new room due to technical limitations
   of servers not being able to impersonate people from other homeservers. Additionally,
   servers should not transfer state events which are sensitive to who sent them, such as
   events outside of the Matrix namespace where clients may rely on the sender to match
   certain criteria.

4. Moves any local aliases to the new room.
5. Sends a ``m.room.tombstone`` event to the old room to indicate that it is not intended
   to be used any further.
6. If possible, the power levels in the old room should also be modified to prevent sending
   of events and inviting new users. For example, setting ``events_default`` and ``invite``
   to the greater of ``50`` and ``users_default + 1``.

When a user joins the new room, the server should automatically transfer/replicate some of
the user's personalized settings such as notifications, tags, etc.
