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
desirable to offer users the concept of speaking directly to one
particular person. This module defines a way of marking certain rooms
as 'direct chats' with a given person. This does not restrict the chat
to being between exactly two people since this would preclude the
presence of automated 'bot' users or even a 'personal assistant' who is
able to answer direct messages on behalf of the user in their absence.

A room may not necessarily be considered 'direct' by all members of the
room, but a signalling mechanism exists to propagate the information of
whether a chat is 'direct' to an invitee.

Events
------

{{m_direct_event}}

Client behaviour
----------------
The invitee's client may use the ``is_direct`` flag to automatically mark the
room as a direct message but this is not required: it may for example, prompt
the user, ignore the flag altogether. To do this, it stores this event in
account data using the ``account_data`` API: see `Client Config`_.

The inviter's client should set the ``is_direct`` flag to  ``createRoom``
whenever the flow the user has followed is one where their intention is to
speak directly with another person, as opposed to bringing that person in to a
shared room. For example, clicking on, 'Start Chat' beside a person's profile
picture would imply the ``is_direct`` flag should be set.

Server behaviour
----------------
When the ``is_direct`` flag is given to ``createRoom``, the home server must
set the ``is_direct`` flag in the invite member event for any users invited
in the ``createRoom`` call.
