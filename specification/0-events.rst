Events
======

All communication in Matrix is expressed in the form of data objects called
Events. These are the fundamental building blocks common to the client-server,
server-server and application-service APIs, and are described below.

{{common_event_fields}}

{{common_room_event_fields}}

{{common_state_event_fields}}


Room Events
-----------
.. NOTE::
  This section is a work in progress.

This specification outlines several standard event types, all of which are
prefixed with ``m.``

{{room_events}}

m.room.message msgtypes
~~~~~~~~~~~~~~~~~~~~~~~

.. TODO-spec
   How a client should handle unknown message types.


Each `m.room.message`_ MUST have a ``msgtype`` key which identifies the type
of message being sent. Each type has their own required and optional keys, as
outlined below.

{{msgtype_events}}

Presence Events
~~~~~~~~~~~~~~~

{{presence_events}}
 
Each user has the concept of presence information. This encodes the
"availability" of that user, suitable for display on other user's clients.
This is transmitted as an ``m.presence`` event and is one of the few events
which are sent *outside the context of a room*. The basic piece of presence
information is represented by the ``presence`` key, which is an enum of one
of the following:

      - ``online`` : The default state when the user is connected to an event
        stream.
      - ``unavailable`` : The user is not reachable at this time.
      - ``offline`` : The user is not connected to an event stream.
      - ``free_for_chat`` : The user is generally willing to receive messages
        moreso than default.
      - ``hidden`` : Behaves as offline, but allows the user to see the client
        state anyway and generally interact with client features. (Not yet
        implemented in synapse).

In addition, the server maintains a timestamp of the last time it saw a
pro-active event from the user; either sending a message to a room, or
changing presence state from a lower to a higher level of availability
(thus: changing state from ``unavailable`` to ``online`` counts as a
proactive event, whereas in the other direction it will not). This timestamp
is presented via a key called ``last_active_ago``, which gives the relative
number of milliseconds since the message is generated/emitted that the user
was last seen active.
    

Events on Change of Profile Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because the profile displayname and avatar information are likely to be used in
many places of a client's display, changes to these fields cause an automatic
propagation event to occur, informing likely-interested parties of the new
values. This change is conveyed using two separate mechanisms:

 - a ``m.room.member`` event is sent to every room the user is a member of,
   to update the ``displayname`` and ``avatar_url``.
 - a ``m.presence`` presence status update is sent, again containing the new values of the
   ``displayname`` and ``avatar_url`` keys, in addition to the required
   ``presence`` key containing the current presence state of the user.

Both of these should be done automatically by the home server when a user
successfully changes their displayname or avatar URL fields.

Additionally, when home servers emit room membership events for their own
users, they should include the displayname and avatar URL fields in these
events so that clients already have these details to hand, and do not have to
perform extra roundtrips to query it.

