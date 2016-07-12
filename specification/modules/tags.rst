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

Room Tagging
============

.. _module:tagging:

Users can add tags to rooms. Tags are short strings used to label rooms, e.g.
"work", "family". A room may have multiple tags. Tags are only visible to the
user that set them but are shared across all their devices.

Events
------

The tags on a room are received as single ``m.tag`` event in the
``account_data`` section of a room in a ``/sync``.

The ``m.tag`` can also be received in a ``/events`` response or in the
``account_data`` section of a room in ``/initialSync``. ``m.tag``
events appearing in ``/events`` will have a ``room_id`` with the room
the tags are for.

Each tag has an associated JSON object with information about the tag, e.g how
to order the rooms with a given tag.

Ordering information is given under the ``order`` key as a string. The string
are compared lexicographically by unicode codepoint to determine which should
displayed first. So a room with a tag with an ``order`` key of ``"apples"``
would appear before a room with a tag with an ``order`` key of ``"oranges"``.
If a room has a tag without an ``order`` key then it should appear after the
rooms with that tag that have an ``order`` key.

The name of a tag MUST not exceed 255 bytes.

The name of a tag should be human readable. When displaying tags for a room a
client should display this human readable name. When adding a tag for a room
a client may offer a list to choose from that includes all the tags that the
user has previously set on any of their rooms.

Two special names are listed in the specification:

* ``m.favourite``
* ``m.lowpriority``

{{m_tag_event}}

Client Behaviour
----------------

{{tags_cs_http_api}}
