.. Copyright 2018 New Vector Ltd
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

Room Specification
==================

.. contents:: Table of Contents
.. sectnum::

Rooms are central to how Matrix operates, and have strict rules for what
is allowed to be contained within them. Rooms can also have various
algorithms that handle different tasks, such as what to do when two or
more events collide in the underlying DAG. To allow rooms to be improved
upon through new algorithms or rules, "room versions" are employed to
manage a set of expectations for each room.


Room version grammar
--------------------

Room versions are used to change properties of rooms that may not be compatible
with other servers. For example, changing the rules for event authorization would
cause older servers to potentially end up in a split-brain situation due to them
not understanding the new rules.

A room version is defined as a string of characters which MUST NOT exceed 32
codepoints in length. Room versions MUST NOT be empty and SHOULD contain only
the characters ``a-z``, ``0-9``, ``.``, and ``-``.

Room versions are not intended to be parsed and should be treated as opaque
identifiers. Room versions consisting only of the characters ``0-9`` and ``.``
are reserved for future versions of the Matrix protocol.

The complete grammar for a legal room version is::

  room_version = 1*room_version_char
  room_version_char = DIGIT
                    / %x61-7A         ; a-z
                    / "-" / "."

Examples of valid room versions are:

* ``1`` (would be reserved by the Matrix protocol)
* ``1.2`` (would be reserved by the Matrix protocol)
* ``1.2-beta``
* ``com.example.version``


Other room versions
-------------------

The available room versions are:

* `Version 1 <v1.html>`_ - The current version of most rooms.
* `Version 2 <v2.html>`_ - Currently in development.

.. Note: the 'unstable' version is commented out pending a real release of rooms v2
.. See meta/releasing-rooms-v2.md
.. * `Unstable <unstable.html>`_ - The upcoming version of the room specification.
