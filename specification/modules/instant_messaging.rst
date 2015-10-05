Instant Messaging
=================

.. _module:im:

This module adds support for sending human-readable messages to a room. It also
adds support for associating human-readable information with the room itself
such as a room name and topic.

Events
------

{{m_room_message_event}}


.. admonition:: Rationale

  Not all clients can display all message types. The most commonly supported
  message type is raw text. As a result, we chose to have a textual fallback
  display method represented by the ``body`` key. This means that even if the
  client cannot display a particular ``msgtype``, they can still display
  *something*, even if it is just plain text.

{{m_room_message_feedback_event}}

Usage of this event is discouraged for several reasons:
 - The number of feedback events will grow very quickly with the number of users
   in the room. This event provides no way to "batch" feedback, unlike the
   `receipts module`_.
 - Pairing feedback to messages gets complicated when paginating as feedback
   arrives before the message it is acknowledging.
 - There are no guarantees that the client has seen the event ID being
   acknowledged.


.. _`receipts module`: `module:receipts`_

{{m_room_name_event}}

{{m_room_topic_event}}

m.room.message msgtypes
~~~~~~~~~~~~~~~~~~~~~~~

Each `m.room.message`_ MUST have a ``msgtype`` key which identifies the type
of message being sent. Each type has their own required and optional keys, as
outlined below. If a client cannot display the given ``msgtype`` then it MUST
display the fallback plain text ``body`` key instead.

{{msgtype_events}}


Client behaviour
----------------

Events which have attachments (e.g. ``m.image``, ``m.file``) are advised to be
uploaded using the `content repository module`_ where available. The
resulting ``mxc://`` URI can then be used in the ``url`` key. The
attachment SHOULD be uploaded *prior* to sending the event in order to stop a
race condition where the recipient receives a link to a non-existent attachment.

.. _`content repository module`: `module:content`_

Recommendations when sending messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Advise using idempotent PUTs to send messages (and why)
- Retries (exp backoff, giveup eventually allowing manual retry)
- Queueing (bucket per room)

Implementing local echo
~~~~~~~~~~~~~~~~~~~~~~~
- Local echo (document bug with races) - sending state. Pairing returned event ID.

Displaying membership information with messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Member name linking (incl. pagination aka historical display names)

Server behaviour
----------------

- SHOULD enforce the body/msgtype keys are present (can 400 them)

Security considerations
-----------------------

- Not encrypted, link to E2E module.
- XSS: Should sanitise ALL KEYS before injecting as unsafe HTML (name/topic/body/etc)

