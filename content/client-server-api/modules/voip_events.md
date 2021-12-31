---
type: module
---

### Voice over IP

This module outlines how two users in a room can set up a Voice over IP
(VoIP) call to each other. Voice and video calls are built upon the
WebRTC 1.0 standard. Call signalling is achieved by sending [message
events](#events) to the room. In this version of the spec, only two-party
communication is supported (e.g. between two peers, or between a peer
and a multi-point conferencing unit). This means that clients MUST only
send call events to rooms with exactly two participants.

#### Events

{{% event-group group_name="m.call" %}}

#### Client behaviour

A call is set up with message events exchanged as follows:

```
    Caller                    Callee
    [Place Call]
    m.call.invite ----------->
    m.call.candidate -------->
    [..candidates..] -------->
                            [Answers call]
           <--------------- m.call.answer
     [Call is active and ongoing]
           <--------------- m.call.hangup
```

Or a rejected call:

```
    Caller                      Callee
    m.call.invite ------------>
    m.call.candidate --------->
    [..candidates..] --------->
                             [Rejects call]
             <-------------- m.call.hangup
```

Calls are negotiated according to the WebRTC specification.

##### Glare

"Glare" is a problem which occurs when two users call each other at
roughly the same time. This results in the call failing to set up as
there already is an incoming/outgoing call. A glare resolution algorithm
can be used to determine which call to hangup and which call to answer.
If both clients implement the same algorithm then they will both select
the same call and the call will be successfully connected.

As calls are "placed" to rooms rather than users, the glare resolution
algorithm outlined below is only considered for calls which are to the
same room. The algorithm is as follows:

-   If an `m.call.invite` to a room is received whilst the client is
    **preparing to send** an `m.call.invite` to the same room:
    -   the client should cancel its outgoing call and instead
        automatically accept the incoming call on behalf of the user.
-   If an `m.call.invite` to a room is received **after the client has
    sent** an `m.call.invite` to the same room and is waiting for a
    response:
    -   the client should perform a lexicographical comparison of the
        call IDs of the two calls and use the *lesser* of the two calls,
        aborting the greater. If the incoming call is the lesser, the
        client should accept this call on behalf of the user.

The call setup should appear seamless to the user as if they had simply
placed a call and the other party had accepted. This means any media
stream that had been setup for use on a call should be transferred and
used for the call that replaces it.

#### Server behaviour

The homeserver MAY provide a TURN server which clients can use to
contact the remote party. The following HTTP API endpoints will be used
by clients in order to get information about the TURN server.

{{% http-api spec="client-server" api="voip" %}}

#### Security considerations

Calls should only be placed to rooms with one other user in them. If
they are placed to group chat rooms it is possible that another user
will intercept and answer the call.
