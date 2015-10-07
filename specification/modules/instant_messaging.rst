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

Clients SHOULD verify the structure of incoming events to ensure that the
expected keys exist and that they are of the right type. Clients can discard
malformed events or display a placeholder message to the user. Redacted
``m.room.message`` events MUST be removed from the client. This can either be
replaced with placeholder text (e.g. "[REDACTED]") or the redacted message can
be removed entirely from the messages view.

Events which have attachments (e.g. ``m.image``, ``m.file``) SHOULD be
uploaded using the `content repository module`_ where available. The
resulting ``mxc://`` URI can then be used in the ``url`` key. The
attachment SHOULD be uploaded *prior* to sending the event in order to stop a
race condition where the recipient receives a link to a non-existent attachment.

.. _`content repository module`: `module:content`_

Recommendations when sending messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients can send messages using ``POST`` or ``PUT`` requests. Clients SHOULD use
``PUT`` requests with `transaction IDs`_ to make requests idempotent. This
ensures that messages are sent exactly once even under poor network conditions.
Clients SHOULD retry requests using an exponential-backoff algorithm for a
certain amount of time T. It is recommended that T is no longer than 5 minutes.
After this time, the client should stop retrying and mark the message as "unsent".
Users should be able to manually resend unsent messages.

Users may type several messages at once and send them all in quick succession.
Clients SHOULD preserve the order in which they were sent by the user. This
means that clients should wait for the response to the previous request before
sending the next request. This can lead to head-of-line blocking. In order to
reduce the impact of head-of-line blocking, clients should use a queue per room
rather than a global queue, as ordering is only relevant within a single room
rather than between rooms.

.. _`transaction IDs`: `sect:txn_ids`_

Local echo
~~~~~~~~~~

Messages SHOULD appear immediately in the message view when a user presses the
"send" button. This should occur even if the message is still sending. This is
referred to as "local echo". Clients SHOULD implement "local echo" of messages.
 
Clients need to be able to pair up the "remote echo" from the server with the
"local echo" to prevent duplicate messages being displayed. Ideally this pairing
would occur transparently to the user: the UI would not flicker as it transitions
from local to remote. Flickering cannot be fully avoided in version 1 of the
client-server API. Two scenarios need to be considered:

- The client sends a message and the remote echo arrives on the event stream
  *after* the request to send the message completes.
- The client sends a message and the remote echo arrives on the event stream
  *before* the request to send the message completes.

In the first scenario, the client will receive an event ID when the request to
send the message completes. This ID can be used to identify the duplicate event
when it arrives on the event stream. However, in the second scenario, the event
arrives before the client has obtained an event ID. This makes it impossible to
identify it as a duplicate event. This results in the client displaying the
message twice for a fraction of a second before the the original request to send
the message completes. Once it completes, the client can take remedial actions
to remove the duplicate event by looking for duplicate event IDs. Version 2 of
the client-server API resolves this by attaching the transaction ID of the
sending request to the event itself.


Displaying membership information with messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients may wish to show the display name and avatar URL of the room member who
sent a message. This can be achieved by inspecting the ``m.room.member`` event
for that user ID.

When a user paginates the message history, clients may wish to show the
**historical** display name and avatar URL for a room member. This is possible
because older ``m.room.member`` events are returned when paginating. This can
be implemented efficiently by keeping two sets of room state: old and current.
As new events arrive and/or the user paginates back in time, these two sets of
state diverge from each other. New events update the current state and paginated
events update the old state. When paginated events are processed sequentially,
the old state represents the state of the room *at the time the event was sent*.
This can then be used to set the historical display name and avatar URL.

Server behaviour
----------------

Homeservers SHOULD enforce that ``m.room.message`` events have textual ``body``
and ``msgtype`` keys by 400ing the request to send a message.

Security considerations
-----------------------

Messages sent using this module are not encrypted. Encryption can be layered
over the top of this module: where the plaintext format is an ``m.room.message``
conforming to this module. This can be achieved using the `E2E module`_.

Clients should sanitise **all keys** for unsafe HTML to prevent Cross-Site
Scripting (XSS) attacks. This includes room names and topics.

.. _`E2E module`: `module:e2e`_

