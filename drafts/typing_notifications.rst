Typing Notifications
====================

Client APIs
-----------

To set "I am typing for the next N msec"::
  PUT .../rooms/:room_id/typing/:user_id
  Content:  { "typing": true, "timeout": N }
    # timeout is in msec; I suggest no more than 20 or 30 seconds

This should be re-sent by the client to continue informing the server the user
is still typing; I suggest a safety margin of 5 seconds before the expected
timeout runs out. Just keep declaring a new timeout, it will replace the old
one.

To set "I am no longer typing"::
  PUT ../rooms/:room_id/typing/:user_id
  Content: { "typing": false }

Client Events
-------------

All room members will receive an event on the event stream::

  {
    "type": "m.typing",
    "room_id": "!room-id-here:matrix.org",
    "content": {
      "user_ids": ["list of", "every user", "who is", "currently typing"]
    }
  }

The client must use this list to *REPLACE* its knowledge of every user who is
currently typing. The reason for this is that the server DOES NOT remember
users who are not currently typing, as that list gets big quickly. The client
should mark as not typing, any user ID who is not in that list.

Server APIs
-----------

Servers will emit EDUs in the following form::

  {
    "type": "m.typing",
    "content": {
      "room_id": "!room-id-here:matrix.org",
      "user_id": "@user-id-here:matrix.org",
      "typing": true/false,
    }
  }

Server EDUs don't (currently) contain timing information; it is up to
originating HSes to ensure they eventually send "stop" notifications.

((This will eventually need addressing, as part of the wider typing/presence
timer addition work))
