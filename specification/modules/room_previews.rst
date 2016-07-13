.. Copyright 2016 OpenMarket Ltd
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

Room Previews
=============

.. _module:room-previews:

It is sometimes desirable to offer a preview of a room, where a user can "lurk"
and read messages posted to the room, without joining the room. This can be
particularly effective when combined with `Guest Access`_.

Previews are implemented via the ``world_readable`` `Room History Visibility`_.
setting, along with a special version of the
`GET /events <#get-matrix-client-%CLIENT_MAJOR_VERSION%-events>`_ endpoint.

Client behaviour
----------------
A client wishing to view a room without joining it should call
`GET /rooms/:room_id/initialSync <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-initialsync>`_,
followed by `GET /events`__. Clients will need to do this
in parallel for each room they wish to view.

__  `peeking_events_api`_

Clients can of course also call other endpoints such as
`GET /rooms/:room_id/messages <#get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-messages>`_
and `GET /search <#get-matrix-client-%CLIENT_MAJOR_VERSION%-search>`_ to access
events outside the ``/events`` stream.

.. _peeking_events_api:

{{peeking_events_cs_http_api}}

Server behaviour
----------------
For clients which have not joined a room, servers are required to only return
events where the room state at the event had the ``m.room.history_visibility``
state event present with ``history_visibility`` value ``world_readable``.

Security considerations
-----------------------
Clients may wish to display to their users that rooms which are
``world_readable`` *may* be showing messages to non-joined users. There is no
way using this module to find out whether any non-joined guest users *do* see
events in the room, or to list or count any lurking users.

