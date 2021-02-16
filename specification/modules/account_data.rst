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

Client Config
=============

.. _module:account_data:

Clients can store custom config data for their account on their homeserver.
This account data will be synced between different devices and can persist
across installations on a particular device. Users may only view the account
data for their own account

The account_data may be either global or scoped to a particular rooms.

Events
------

The client receives the account data as events in the ``account_data`` sections
of a ``/sync``.

These events can also be received in a ``/events`` response or in the
``account_data`` section of a room in ``/sync``. ``m.tag``
events appearing in ``/events`` will have a ``room_id`` with the room
the tags are for.

Client Behaviour
----------------

{{account_data_cs_http_api}}


Server Behaviour
----------------

Servers MUST reject clients from setting account data for event types that
the server manages. Currently, this only includes `m.fully_read`_.
