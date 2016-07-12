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

Typing Notifications
====================

.. _module:typing:

Users may wish to be informed when another user is typing in a room. This can be
achieved using typing notifications. These are ephemeral events scoped to a
``room_id``. This means they do not form part of the
`Event Graph <index.html#event-graphs>`_ but still have a ``room_id`` key.

Events
------

{{m_typing_event}}

Client behaviour
----------------

When a client receives an ``m.typing`` event, it MUST use the user ID list to
**REPLACE** its knowledge of every user who is currently typing. The reason for
this is that the server *does not remember* users who are not currently typing
as that list gets big quickly. The client should mark as not typing any user ID
who is not in that list.

It is recommended that clients store a ``boolean`` indicating whether the user
is typing or not. Whilst this value is ``true`` a timer should fire periodically
every N seconds to send a typing HTTP request. The value of N is recommended to
be no more than 20-30 seconds. This request should be re-sent by the client to
continue informing the server the user is still typing. As subsequent
requests will replace older requests, a safety margin of 5 seconds before the
expected timeout runs out is recommended. When the user stops typing, the
state change of the ``boolean`` to ``false`` should trigger another HTTP request
to inform the server that the user has stopped typing.

{{typing_cs_http_api}}

Security considerations
-----------------------

Clients may not wish to inform everyone in a room that they are typing and
instead only specific users in the room.

