.. Copyright 2016 OpenMarket Ltd
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

Event Structure
===============

All communication in Matrix is expressed in the form of data objects called
Events. These are the fundamental building blocks common to the client-server,
server-server and application-service APIs, and their structure is dependent
upon the version of the room they appear within. For a full description of
what makes up an event, please see the `room version specification`_.

.. _`room version specification`: ../rooms/latest.html


Room Events
-----------
.. NOTE::
  This section is a work in progress.

This specification outlines several standard event types, all of which are
prefixed with ``m.``

{{m_room_aliases_event}}

{{m_room_canonical_alias_event}}

{{m_room_create_event}}

{{m_room_join_rules_event}}

{{m_room_member_event}}

{{m_room_power_levels_event}}

{{m_room_redaction_event}}

.. _`Canonical JSON`: ../appendices.html#canonical-json
