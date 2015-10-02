Instant Messaging
=================

.. _module:im:

This module adds support for sending human-readable messages to a room. It also
adds human-readable information to the room itself such as a room name and topic.

Events
------

{{m_room_message_event}}

{{m_room_message_feedback_event}}

{{m_room_name_event}}

{{m_room_topic_event}}

m.room.message msgtypes
~~~~~~~~~~~~~~~~~~~~~~~

.. TODO-spec
   How a client should handle unknown message types.


Each `m.room.message`_ MUST have a ``msgtype`` key which identifies the type
of message being sent. Each type has their own required and optional keys, as
outlined below.

{{msgtype_events}}


Client behaviour
----------------

Server behaviour
----------------

Security considerations
-----------------------

