Voice over IP
-------------
Matrix can also be used to set up VoIP calls. This is part of the core
specification, although is at a relatively early stage. Voice (and video) over
Matrix is built on the WebRTC 1.0 standard. Call events are sent to a room, like
any other event. This means that clients must only send call events to rooms
with exactly two participants as currently the WebRTC standard is based around
two-party communication.

{{voip_events}}

Message Exchange
~~~~~~~~~~~~~~~~
A call is set up with messages exchanged as follows:

::

   Caller                    Callee
 [Place Call]
 m.call.invite ----------->
 m.call.candidate -------->
 [..candidates..] -------->
                           [Answers call]
          <--------------- m.call.answer
    [Call is active and ongoing]
          <--------------- m.call.hangup

Or a rejected call:

::

   Caller                      Callee
 m.call.invite ------------>
 m.call.candidate --------->
 [..candidates..] --------->
                            [Rejects call]
            <-------------- m.call.hangup

Calls are negotiated according to the WebRTC specification.


Glare
~~~~~
This specification aims to address the problem of two users calling each other
at roughly the same time and their invites crossing on the wire. It is a far
better experience for the users if their calls are connected if it is clear
that their intention is to set up a call with one another. In Matrix, calls are
to rooms rather than users (even if those rooms may only contain one other user)
so we consider calls which are to the same room. The rules for dealing with such
a situation are as follows:

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

