Instant Messaging
=================

.. _module:im:

Events
------

{{m_room_message_event}}

{{m_room_message_feedback_event}}

{{m_room_name_event}}

{{m_room_topic_event}}

m.room.message msgtypes
-----------------------

.. TODO-spec
   How a client should handle unknown message types.


Each `m.room.message`_ MUST have a ``msgtype`` key which identifies the type
of message being sent. Each type has their own required and optional keys, as
outlined below.

{{msgtype_events}}

