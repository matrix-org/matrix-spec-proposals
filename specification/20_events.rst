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

Voice over IP
-------------
Matrix can also be used to set up VoIP calls. This is part of the core
specification, although is at a relatively early stage. Voice (and video) over
Matrix is built on the WebRTC 1.0 standard.

Call events are sent to a room, like any other event. This means that clients
must only send call events to rooms with exactly two participants as currently
the WebRTC standard is based around two-party communication.

{{voip_events}}

Message Exchange
~~~~~~~~~~~~~~~~
A call is set up with messages exchanged as follows:

::

   Caller                   Callee
 m.call.invite ----------->
 m.call.candidate -------->
 [more candidates events]
                         User answers call
                  <------ m.call.answer
               [...]
                  <------ m.call.hangup

Or a rejected call:

::

   Caller                   Callee
 m.call.invite ----------->
 m.call.candidate -------->
 [more candidates events]
                        User rejects call
                 <------- m.call.hangup

Calls are negotiated according to the WebRTC specification.


Glare
~~~~~
This specification aims to address the problem of two users calling each other
at roughly the same time and their invites crossing on the wire. It is a far
better experience for the users if their calls are connected if it is clear
that their intention is to set up a call with one another.

In Matrix, calls are to rooms rather than users (even if those rooms may only
contain one other user) so we consider calls which are to the same room.

The rules for dealing with such a situation are as follows:

 - If an invite to a room is received whilst the client is preparing to send an
   invite to the same room, the client should cancel its outgoing call and
   instead automatically accept the incoming call on behalf of the user.
 - If an invite to a room is received after the client has sent an invite to
   the same room and is waiting for a response, the client should perform a
   lexicographical comparison of the call IDs of the two calls and use the
   lesser of the two calls, aborting the greater. If the incoming call is the
   lesser, the client should accept this call on behalf of the user.

The call setup should appear seamless to the user as if they had simply placed
a call and the other party had accepted. Thusly, any media stream that had been
setup for use on a call should be transferred and used for the call that
replaces it.

