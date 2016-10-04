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

Direct Messaging
================

.. _module:dm:

All communication over Matrix happens within a room. It is sometimes
desireable to offer users the concept of speaking directly to one
particular person. This module defines a way of marking certain rooms
as 'direct chats' with a given person. This does not restrict the chat
to being between exactly two people since this would preclude the
presence of automated 'bot' users or even a 'personal assistant' who is
able to answer direct messages on behalf of the user in their absence.

A room may not necessarily be considered 'direct' by all members of the
room, but a signalling mechanism exists to propagate the information of
whether a chat is 'direct' to an invitee. The invitee's client may
use this flag to automatically mark the room as a direct message but
this is not required: it may for example, prompt the user, ignore the
flag altogether.

Events
------

A map of which rooms are considered 'direct' rooms for specific users
is kept in  ``account_data`` in an event of type ``m.direct``. The
content of this event is an object where the keys are the user IDs
and values are lists of room ID strings of the 'direct' rooms for
that user ID.

Example::

    {
        "@bob:example.com": [
            "!abcdefgh:example.com",
            "!hgfedcba:example.com"
        ]
    }


When creating a room, the ``is_direct`` flag may be specified to signal
to the invitee that this is a direct chat. See
`GET /_matrix/client/unstable/initialSync`_. This flag appears as
``is_direct`` in the member event: see `m.room.member`_.
