Instant Messaging
=================

TODO:
 - EDU stuff (presence/typing)
 - Concept of a session (for announcing of presence, and scoping of action IDs)
 - The actual filter APIs themselves
 - VoIP

Global ``/initialSync`` API
---------------------------
Inputs:
 - A way of identifying the user (e.g. access token, user ID, etc)
Outputs:
 - For each room the user is joined: Name, topic, # members, last message, room ID, aliases
What data flows does it address:
 - Home screen: data required on load.
 
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
 
VoIP
----
WIPWIPWIPWIPWIPWIPWIPWIPWIPWIPWIPWIP

Placing a call (initial)
~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - WIP
Outputs:
 - WIP
What data flows does it address:
 - WIP
 
Placing a call (candidates)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - WIP
Outputs:
 - WIP
What data flows does it address:
 - WIP
 
