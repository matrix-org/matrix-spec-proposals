Instant Messaging
=================

TODO
----
- Pagination: Would be nice to have "and X more". It will probably be Google-style estimates given
  we can't know the exact number over federation, but as a purely informational display thing it would
  be nice.
 
Filter API
----------
Inputs:
 - Which event types (incl wildcards)
 - Which room IDs
 - Which user IDs (for profile/presence)
 - Whether you want federation-style event JSON
 - Whether you want coalesced ``updates`` events
 - Whether you want coalesced ``in_reply_to`` events (and the max # to coalesce)
 - limit= param?
Outputs:
 - An opaque token which represents the inputs
Notes:
 - The token may expire, in which case you would need to request another one.
 - The token could be as simple as a concatenation of the requested filters with a delimiter between them.
 - Omitting the token on APIs results in ALL THE THINGS coming down.
 - Clients should remember which token they need to use for which API.
 - HTTP note: If the filter API is a separate endpoint, then you could easily allow APIs which use filtering
   to ALSO specifiy query parameters to tweak the filter.

Global ``/initialSync`` API
---------------------------
Inputs:
 - A way of identifying the user (e.g. access token, user ID, etc)
 - Streaming token (optional)
 - Filter to apply
Outputs:
 - For each room the user is joined: Name, topic, # members, last message, room ID, aliases
Notes:
 - If a streaming token is applied, you will get a delta rather than all the rooms.
What data flows does it address:
 - Home screen: data required on load.
 
TODO:
 - Will need some form of state event pagination like we have for message events to handle large
   amounts of state events for a room. Need to think of the consequences of this: you may not get a
   ``m.room.member`` for someone's message and so cannot display their display name / avatar.
 - Handle paginating initial sync results themselves (e.g. 10 most recent rooms)
 - No need for state events under the 'state' key to have a ``prev_content``. Can also apply some
   optimisations depending on the direction of travel when scrolling back.
   
 
Event Stream API
----------------
Inputs:
 - Position in the stream
 - Filter to apply: which event types, which room IDs, whether to get out-of-order events, which users 
   to get presence/profile updates for
 - User ID
 - Device ID
Outputs:
 - 0-N events the client hasn't seen.
 - New position in the stream.
State Events Ordering Notes:
 - Home servers may receive state events over federation that are superceded by state events previously 
   sent to the client. The home server *cannot* send these events to the client else they would end up
   erroneously clobbering the superceding state event. 
 - As a result, the home server reserves the right to omit sending state events which are known to be
   superceded already.
 - This may result in missed *state* events. However, the state of the room will always be eventually
   consistent.
Message Events Ordering Notes:
 - Home servers may receive message events over federation that happened a long time ago. The client
   may or may not be interested in these message events.
 - For clients which do not persist scrollback for a room, this is not a problem as they only care
   about the recent messages.
 - For clients which do persist scrollback for a room, they need to know about the message event and
   where to insert it so that scrollback remains consistent and doesn't omit messages.
 - Clients can specify an input parameter stating that they wish to receive these out-of-order events.
 - The event, when it comes down the stream, will indicate which event it comes after.
Rejected events:
 - A home server may find out via federation that it should not have accepted an event (e.g. to send a
   message/state event in a room).
 - If this happen, the home server will send a ``m.room.redaction`` for the event in question.
 - If the event was a state event, it will synthesise a new state event to correct the client's room state.
 - In practice, clients don't need any extra special handling for this.
What data flows does it address:
 - Home Screen: Data required when new message arrives for a room
 - Home Screen: Data required when someone invites you to a room
 - Home Screen: Data required when you leave a room on another device
 - Home Screen: Data required when you join a room on another device
 - Home Screen: Data required when your profile info changes on another device
 - Chat Screen: Data required when member name changes
 - Chat Screen: Data required when the room name changes
 - Chat Screen: Data required when a new message arrives
 
Room Creation
-------------
Inputs:
  - Invitee list of user IDs, public/private, name of room, alias of room, topic of room
Output:
  - Room ID
Notes:
 - This is a special case of joining a room. See the notes on joining a room.
What data flows does it address:
  - Home Screen: Creating a room
 
Joining a room
--------------
Inputs:
 - Room ID / alias
 - Optional filter (which events to return, whether the returned events should come down
   the event stream)
Outputs:
 - Room ID, Room aliases (plural), Name, topic, member list (f.e. member: user ID,
   avatar, presence, display name, power level, whether they are typing), enough
   messages to fill screen (and whether there are more)
Notes:
 - How do you return room information? In response to the join, or from the event stream?
 - The events returned need to be filterable. Different clients for the same user may want
   different information (e.g. the client performing the join may jump to the chat screen and
   therefore want some messages, whereas the client not performing the join just needs to be
   aware of the new room).
 - As a result, the join response should return events *instead of* to the event stream, depending
   on the client.
Mapping messages to the event stream:
 - Once you join a room, you will start getting message events for it. How do you know when
   you started getting events for this room? You need to know so you can provide a token when
   scrolling back. You cannot currently infer this from the join event itself, as individual
   events do not have tokens (only chunks do).
 - This token can be provided as a separate server-generated event, or an annotation on the join
   event itself.
 - We propose that a server-generated event is sent down the event stream to all clients, rather
   than annotating the join event. The server-generated event works nicely for Application 
   Services where an entity subscribes to a room without a join event.
What data flows does it address:
 - Home Screen: Joining a room
 
Scrolling back (infinite scrolling)
-----------------------------------
Inputs:
 - Identifier for the earliest event
 - # requested events
 - filter to apply
 - flag to say if the home server should do a backfill over federation
Outputs:
 - requested events (f.e change in display name, what the old name was), 
 - whether there are more events on the local HS / over federation.
 - new identifier for the earliest event
What data flows does it address:
 - Chat Screen: Scrolling back (infinite scrolling)
 
Contextual messages
-------------------
Inputs:
 - Event ID of the message to get the surrounding context for (this specifies the room to get messages in).
 - Number of messages before/after this message to obtain.
 - Filter to apply.
Outputs:
 - Chunk of messages
 - Start / End pagination tokens
 - Current room state at the end of the chunk as per initial sync.


Action APIs
-----------
The following APIs are "action APIs". This is defined to be a request which alters the state of
a room you are already joined to.

When you perform an action in a room, you immediately want to display the local echo. The client
can receive the response to the action either directly or from the event stream. The order in which
you receive these responses is undefined. As a result, clients MUST be able to handle all possible
orderings::

                 1                           2a                          3
 START ----> REQUEST SENT ---> RESPONSE TO REQUEST RECEIVED --------> GOT BOTH
                 |                                                       ^
                 |                      2b                               |
                 +----------> APPEARS IN EVENT STREAM -------------------+
                 
  1: Can display local echo at this point.
  2a: The request has been successfully processed and can be displayed as Sent.
  2b/3: The request has been successfully processed and the client knows its position in the event stream.

When a client sends a request, they can include an "action ID" so that they can match up the event in
the event stream to the request which they made. This ID is created by the client, and MUST be a 
monotonically increasing integer for that client. This ID serves as a transaction ID for idempotency as
well as a sequence ID for ordering actions performed in parallel by that client. Events for actions 
performed by a client in that client's event stream will include the action ID the client submitted 
when making the request. The action ID will *not* appear in other client's event streams.

Action IDs are optional and are only needed by clients that retransmit their requests, or display local
echo, or allow the submission of multiple requests in parallel. An example of a client which may not need
the use of action IDs includes bots which operate using basic request/responses in a synchronous fashion.
 
Inviting a user
~~~~~~~~~~~~~~~
Inputs:
 - User ID
 - Room ID
 - Action ID (optional)
Outputs:
 - Display name / avatar of user invited (if known)
What data flows does it address:
 - Chat Screen: Invite a user
 
Rejecting an invite
~~~~~~~~~~~~~~~~~~~
Inputs:
 - Event ID (to know which invite you're rejecting)
Outputs:
 - None.
Notes:
 - Giving the event ID rather than user ID/room ID combo because mutliple users can invite the
   same user into the same room.
   
Deleting a state event
~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Event type
 - State key
 - Room ID
Outputs:
 - None.
 
Kicking a user
~~~~~~~~~~~~~~
Inputs:
 - User ID
 - Room ID
 - Action ID (optional)
Outputs:
 - None.
What data flows does it address:
 - Chat Screen: Kick a user

Leaving a room
~~~~~~~~~~~~~~
Inputs:
 - Room ID
 - A way of identifying the user (user ID, access token)
 - Action ID (optional)
Outputs:
 - None.
What data flows does it address:
 - Chat Screen: Leave a room
 
Send a message
~~~~~~~~~~~~~~
Inputs:
 - Room ID
 - Message contents
 - Action ID (optional)
Outputs:
 - Actual content sent (if server modified it)
 - When in the stream this action happened. (to correctly display local echo)
What data flows does it address:
 - Chat Screen: Send a Message
Ordering notes:
 - HTTP: When sending a message with a higher seqnum, it will block the request until it receives 
   earlier seqnums. The block will expire after a timeout and reject the message stating that it 
   was missing a seqnum.
E2E Notes:
 - For signing: You send the original message to the HS and it will return the full event JSON which will
   be sent. This full event is then signed and sent to the HS again to send the message.
 
Sessions
--------
A session is a group of requests sent within a short amount of time by the same client. Starting
a session is known as going "online". Its purpose is to wrap up the expiry of presence and 
typing notifications into a clearer scope. A session starts when the client makes any request.
A session ends when the client doesn't make a request for a particular amount of time (times out).
A session can also end when explicitly hitting a particular endpoint. This is known as going "offline".

When a session starts, a session ID is sent in response to the first request the client makes. This
session ID should be sent in *all* subsequent requests. If the server expires a session and the client
uses an old session ID, the server should fail the request with the old session ID and send a new 
session ID in response for the client to use. If the client receives a new session ID mid-session, 
it must re-establish its typing status and presence status, as they are linked to the session ID.

Presence
~~~~~~~~
When a session starts, the home server can treat the user as "online". When the session ends, the home
server can treat the user as "offline".

Inputs:
 - Presence state (online, offline, away, busy, do not disturb, etc)
Outputs:
 - None.
Notes:
 - TODO: Handle multiple devices.


Typing
~~~~~~
When in a session, a user can send a request stating that they are typing in a room. They are no longer
typing when either the session ends or they explicitly send another request to say they are no longer
typing.

Inputs:
 - Room ID
 - Whether you are typing or not.
Output:
 - None.
Notes:
 - Typing will time out when the session ends.
 
Action IDs
~~~~~~~~~~
Action IDs are scoped per session. The first action ID for a session should be 0. For each subsequent
action request, the ID should be incremented by 1. It should be reset to 0 when a new session starts.

If the client sends an action request with a stale session ID, the home server MUST fail the request
and start a new session. The request needs to be failed in order to avoid edge cases with incrementing
action IDs.

Updates (Events)
----------------
Events may update other events. This is represented by the ``updates`` key. This is a key which
contains the event ID for the event it relates to. Events that relate to other events are referred to
as "Child Events". The event being related to is referred to as "Parent Events". Child events cannot
stand alone as a separate entity; they require the parent event in order to make sense.

Bundling
~~~~~~~~
Events that relate to another event should come down inside that event. That is, the top-level event
should come down with all the child events at the same time. This is called a "bundle" and it is 
represented as an array of events inside the top-level event.There are some issues with this however:

- Scrollback: Should you be told about child events for which you do not know the parent event?
  Conclusion: No you shouldn't be told about child events. You will receive them when you scroll back
  to the parent event. 
- Pagination of child events: You don't necessarily want to have 1000000s of child events with the
  parent event. We can't reasonably paginate child events because we require all the child events
  in order to display the event correctly. Comments on a message should be done via another technique,
  such as ``in_reply_to`.
- Do you allow child events to relate to other child events? There is no technical reason why we
  cannot nest child events, however we can't think of any use cases for it. The behaviour would be
  to get the child events recursively from the top-level event. 
  
Main use cases for ``updates``:
 - Call signalling (child events are ICE candidates, answer to the offer, and termination)
 - *Local* Delivery/Read receipts : "Local" means they are not shared with other users on the same home
   server or via federation but *are* shared between clients for the same user; useful for push 
   notifications, read count markers, etc. This is done to avoid the ``n^2`` problem for sending 
   receipts, where the vast majority of traffic tends towards sending more receipts.
 - s/foo/bar/ style message edits
 
Clients *always* need to know how to apply the deltas because clients may receive the events separately
down the event stream. Combining event updates server-side does not make client implementation simpler, 
as the client still needs to know how to combine the events.

In reply to (Events)
--------------------
Events may be in response to other events, e.g. comments. This is represented by the ``in_reply_to`` 
key. This differs from the ``updates`` key as they *do not update the event itself*, and are *not required* 
in order to display the parent event. Crucially, the child events can be paginated, whereas ``updates`` child events cannot
be paginated.

Bundling
~~~~~~~~
Child events can be optionally bundled with the parent event, depending on your display mechanism. The
number of child events which can be bundled should be limited to prevent events becoming too large. This
limit should be set by the client. If the limit is exceeded, then the bundle should also include a pagination
token so that the client can request more child events.

Main use cases for ``in_reply_to``:
 - Comments on a message.
 - Non-local delivery/read receipts : If doing separate receipt events for each message.
 - Meeting invite responses : Yes/No/Maybe for a meeting.

Like with ``updates``, clients need to know how to apply the deltas because clients may receive the 
events separately down the event stream.

TODO:
 - Can a child event reply to multiple parent events? Use case?
 - Should a parent event and its children share a thread ID? Does the originating HS set this ID? Is
   this thread ID exposed through federation? e.g. can a HS retrieve all events for a given thread ID from
   another HS?
   
Example using ``updates`` and ``in_reply_to``
---------------------------------------------
- Room with a single message.
- 10 comments are added to the message via ``in_reply_to``.
- An edit is made to the original message via ``updates``.
- An initial sync on this room with a limit of 3 comments, would return the message with the update 
  event bundled with it and the most recent 3 comments and a pagination token to request earlier comments
  
  .. code :: javascript
  
    {
      content: { body: "I am teh winner!" },
      updated_by: [
        { content: { body: "I am the winner!" } }
      ],
      replies: {
        start: "some_token",
        chunk: [
          { content: { body: "8th comment" } },
          { content: { body: "9th comment" } },
          { content: { body: "10th comment" } }
        ]
      }
    }
    
Events (breaking changes; event version 2)
------------------------------------------
- Prefix the event ``type`` to say if it is a state event, message event or ephemeral event. Needed
  because you can't tell the different between message events and ephemeral ROOM events (e.g. typing).
- State keys need additional restrictions in order to increase flexibility on state event permissions.
  State keys prefixed with an ``_`` have no specific restrictions. 0-length state keys are now represented
  by just a single ``_``. State keys prefixed with ``@`` can be modified only by the named user ID *OR* the
  room ops. They can have an optional path suffixed to it. State keys that start with a server name can only
  be modified by that server name (e.g. ``some.server.com/some/path`` can only be modified by 
  ``some.server.com``).
- Do we want to specify what restrictions apply to the state key in the event type? This would allow HSes
  to enforce this, making life easier for clients when dealing with custom event types. E.g. ``_custom.event``
  would allow anything in the state key, ``_@custom.event`` would only allow user IDs in the state key, etc.
- s/user_id/sender/g given that home servers can send events, not just users.

Capabilities
------------
How does a client know if the server it is using supports a content repository? How does a client know 
if another client has VoIP support? This section outlines capability publishing for servers,
clients and federation.

Server
~~~~~~
- List of extensions it supports (e.g. content repo, contact repo, turn servers)

Inputs:
 - User ID (e.g. only @bob can use the content repo)
Output:
 - Hash of the capabilities::
 
    {
      "sha256": "fD876SFrt3sugh23FWEjio3"
    }

This hash is fed into another API:

Inputs:
 - The hash of the capabilities
Output:
 - A list of capabilities::
 
    {
      "custom.feature.v1": {},
      "m.cap.turnserver.v1": {}
    }

Client
~~~~~~
- e.g. Whether this client supports VoIP

When a session is started, the client needs to provide a capability set. The server will take the "union"
of all the user's connected clients' capability sets and send the hash of the capabilities as part of 
presence information (not necesarily as a ``m.presence`` event, but it should act like presence events).

On first signup, the client will attempt to send the hash and be most likely refused by the home server as
it does not know the full capability set for that hash. The client will then have to upload the full capability
set to the home server. The client will then be able to send the hash as normal.

When a client receives a hash, the client will either recognise the hash or will have to request the capability
set from their home server:

Inputs:
 - Hash
 - User ID
Output:
 - A list of capabilities

Federation
~~~~~~~~~~
- e.g. Whether you support backfill, hypothetical search/query/threading APIs
- Same as the server capability API

VoIP
----
This addresses one-to-one calling with multiple devices. This uses the ``updates`` key to
handle signalling.

Event updates
~~~~~~~~~~~~~
- Call is placed by caller. Event generated with offer.
- 1-N callees may pick up or reject this offer.
- Callees update the event (with sdp answer if they are accepting the call)
- Caller acknowledges *one* of the callees (either one which picked up or rejected) by updating the event.
- Callees who weren't chosen then give up (Answered elsewhere, Rejected elsewhere, etc)
- Update with ICE candidates as they appear.
- ... in call ...
- Send hangup update when hanging up.

Placing a call
~~~~~~~~~~~~~~
::

  caller                callee
   |-----m.call.invite--->|
   |                      |
   |<----m.call.answer----|
   |     device_id=foo    |
   |                      |
   |------m.call.ack----->|
   |     device_id=foo    |
   |                      |
   |<--m.call.candidate---|
   |---m.call.candidate-->|
   |                      |
 [...]                  [...]
   |                      |
   |<----m.call.hangup----|
   |     device_id=foo    |

Expiry
~~~~~~
- WIP: Of invites
- WIP: Of calls themselves (as they may never send a ``m.call.hangup``



 
