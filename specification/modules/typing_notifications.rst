Typing Notifications
====================

Events
------

{{m_typing_event}}

Client behaviour
----------------

 - suggested no more than 20-30 seconds

This should be re-sent by the client to continue informing the server the user
is still typing; a safety margin of 5 seconds before the expected
timeout runs out is recommended. Just keep declaring a new timeout, it will
replace the old one.

Event: The client must use this list to *REPLACE* its knowledge of every user who is
currently typing. The reason for this is that the server DOES NOT remember
users who are not currently typing, as that list gets big quickly. The client
should mark as not typing, any user ID who is not in that list.

{{typing_http_api}}

Server behaviour
----------------

Servers will emit EDUs in the following form::

  {
    "type": "m.typing",
    "content": {
      "room_id": "!room-id-here:matrix.org",
      "user_id": "@user-id-here:matrix.org",
      "typing": true/false
    }
  }

Server EDUs don't (currently) contain timing information; it is up to
originating HSes to ensure they eventually send "stop" notifications.

.. TODO
  ((This will eventually need addressing, as part of the wider typing/presence
  timer addition work))

Security considerations
-----------------------

Clients may not wish to inform everyone in a room that they are typing and
instead only specific users in the room.

