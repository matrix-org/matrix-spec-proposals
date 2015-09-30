Typing Notifications
====================

Users often desire to see when another user is typing. This can be achieved
using typing notifications. These are ephemeral events scoped to a ``room_id``.
This means they do not form part of the `Event Graph`_ but still have a
``room_id`` key.

.. _Event Graph: `sect:event-graph`_

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

{{typing_http_api}}

Server behaviour
----------------

Servers MUST emit typing EDUs in the following form::

  {
    "type": "m.typing",
    "content": {
      "room_id": "!room-id-here:matrix.org",
      "user_id": "@user-id-here:matrix.org",
      "typing": true/false
    }
  }

This does not contain timing information so it is up to originating homeservers
to ensure they eventually send "stop" notifications.

.. TODO
  ((This will eventually need addressing, as part of the wider typing/presence
  timer addition work))

Security considerations
-----------------------

Clients may not wish to inform everyone in a room that they are typing and
instead only specific users in the room.

