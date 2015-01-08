Table of Contents
=================

.. contents:: Table of Contents
.. sectnum::

Summary of changes from v1
==========================
Included:
 - Event filtering (type/room/users, federation-style events)
 - Incremental syncing
 - Rejecting invites
 - Deleting state
 - Contextual messages (view messages around an arbitrary message)
 - Race conditions on event stream / actions
 - Out-of-order events
 - Capabilities
 - Comments (relates_to key)
 - Editing/updating messages (updates key)
 
Excluded:
 - Searching messages
 - State event pagination (see Global /initialSync API)
 - Initial sync pagination (see Global /initialSync API)
 - PATCHing power levels
 - Handling "duplicate" events in state/messages key on initial sync.
 - Multiple devices (other than VoIP)
 - Room directory lists (aka public room list, paginating, permissions on 
   editing the list, etc)

Version 2 API
=============

Legend:
 - ``[TODO]``: API is not in this document yet.
 - ``[ONGOING]``: API is proposed but needs more work. There are known issues to be
   addressed.
 - ``[Draft]``: API is proposed and has no outstanding issues to be addressed, but
   needs more feedback.
 - ``[Final]``:  The API has no outstanding issues.

This contains the formal proposal for Matrix Client-Server API v2. This API 
would completely replace v1. It is a general API, not specific to any particular 
protocol e.g. HTTP. The following APIs will remain unchanged from v1:

- Registration API
- Login API
- Content repository API

This version will change the path prefix for HTTP:
 - Version 1: ``/_matrix/client/api/v1``
 - Version 2: ``/_matrix/client/v2``
 
Note the lack of the ``api`` segment. This is for consistency between other 
home server path prefixes.
 
Filter API ``[ONGOING]``
------------------------
.. NOTE::
 - Exactly what can be filtered? Which APIs use this? Are we 
   conflating too much?
 - Do we want to specify negative filters (e.g. don't give me 
   ``event.type.here`` events)

Inputs:
 - Which event types (incl wildcards)
 - Which room IDs
 - Which user IDs (for profile/presence)
 - Whether you want federation-style event JSON
 - Whether you want coalesced ``updates`` events
 - Whether you want coalesced ``relates_to`` events (and the max # to coalesce)
 - limit= param?
 - Which keys to return for events? e.g. no ``origin_server_ts`` if you don't 
   show timestamps
Outputs:
 - An opaque token which represents the inputs
Notes:
 - The token may expire, in which case you would need to request another one.
 - The token could be as simple as a concatenation of the requested filters with
   a delimiter between them.
 - Omitting the token on APIs results in ALL THE THINGS coming down.
 - Clients should remember which token they need to use for which API.
 - HTTP note: If the filter API is a separate endpoint, then you could easily 
   allow APIs which use filtering to ALSO specifiy query parameters to tweak the
   filter.

Global initial sync API ``[ONGOING]``
-------------------------------------
.. NOTE::
 - Will need some form of state event pagination like we have for message events
   to handle large amounts of state events for a room. Need to think of the 
   consequences of this: you may not get a ``m.room.member`` for someone's 
   message and so cannot display their display name / avatar. Do we want to 
   provide pagination on an event type basis?
 - Handle paginating initial sync results themselves (e.g. 10 most recent rooms)
 - No need for state events under the 'state' key to have a ``prev_content``. 
   Can also apply some optimisations depending on the direction of travel when 
   scrolling back.
 - Do we want to treat global / specific room initial syncs as separate entities?
   Aren't they just a filter?

Inputs:
 - A way of identifying the user (e.g. access token, user ID, etc)
 - Streaming token (optional)
 - Which state event types to return (e.g. ``m.room.name`` / ``m.room.topic`` 
   / ``m.room.aliases``)
 - Filter to apply
Outputs:
 - For each room the user is joined:
    - Requested state events
    - # members
    - max of limit= message events
    - room ID
Notes:
 - If a streaming token is applied, you will get a delta rather than all the 
   rooms.
What data flows does it address:
 - Home screen: data required on load.
   
 
Event Stream API ``[Draft]``
----------------------------
Inputs:
 - Position in the stream
 - Filter to apply: which event types, which room IDs, whether to get 
   out-of-order events, which users to get presence/profile updates for
 - User ID
 - Device ID
Outputs:
 - 0-N events the client hasn't seen. NB: Deleted state events will be missing a
   ``content`` key. Deleted message events are ``m.room.redaction`` events.
 - New position in the stream.
State Events Ordering Notes:
 - Home servers may receive state events over federation that are superceded by 
   state events previously sent to the client. The home server *cannot* send 
   these events to the client else they would end up erroneously clobbering the
   superceding state event. 
 - As a result, the home server reserves the right to omit sending state events 
   which are known to be superceded already.
 - This may result in missed *state* events. However, the state of the room will
   always be eventually consistent.
Message Events Ordering Notes:
 - Home servers may receive message events over federation that happened a long 
   time ago. The client may or may not be interested in these message events.
 - For clients which do not store scrollback for a room (they discard events 
   after processing them), this is not a problem as they only care about the 
   recent messages.
 - For clients which do persist scrollback for a room, they need to know about 
   the message event and where to insert it so that scrollback remains 
   consistent and doesn't omit messages.
 - Clients can specify an input parameter stating that they wish to receive 
   these out-of-order events.
 - The event, when it comes down the stream, will indicate which event it comes 
   after.
Rejected events:
 - A home server may find out via federation that it should not have accepted 
   an event (e.g. to send a message/state event in a room).
 - If this happens, the home server will send a ``m.room.redaction`` for the 
   event in question. This will be a local server event (not shared with other 
   servers).
 - If the event was a state event, it will synthesise a new state event to 
   correct the client's room state. This will be a local server event (not 
   shared with other servers).
 - In practice, clients don't need any extra special handling for this.
Unknown rooms:
 - You could receive events for rooms you are unaware of (e.g. you didn't do an
   initial sync, or your HS lost its database and is told from another HS that 
   they are in this room). How do you handle this?
 - The simplest option would be to redo the initial sync with a filter on the
   room ID you're unaware of. This would retrieve the room state so you can 
   display the room.
What data flows does it address:
 - Home Screen: Data required when new message arrives for a room
 - Home Screen: Data required when someone invites you to a room
 - Home Screen: Data required when you leave a room on another device
 - Home Screen: Data required when you join a room on another device
 - Home Screen: Data required when your profile info changes on another device
 - Chat Screen: Data required when member name changes
 - Chat Screen: Data required when the room name changes
 - Chat Screen: Data required when a new message arrives
 
Room Creation API ``[Draft]``
-----------------------------
Inputs:
  - Invitee list of user IDs, public/private, state events to set on creation 
    e.g. name of room, alias of room, topic of room
Output:
  - Room ID
Notes:
  - This is a special case of joining a room. See the notes on joining a room.
What data flows does it address:
  - Home Screen: Creating a room
 
Joining API ``[Draft]``
-----------------------
Inputs:
 - Room ID (with list of servers to join from) / room alias / invite event ID
 - Optional filter (which events to return, whether the returned events should 
   come down the event stream)
Outputs:
 - Room ID, the returned state events from the filter e.g. Room aliases 
   (plural), Name, topic, member list (f.e. member: user ID, avatar, presence, 
   display name, power level, whether they are typing), enough messages to fill
   screen (and whether there are more)
Notes:
 - How do you return room information? In response to the join, or from the 
   event stream?
 - The events returned need to be filterable. Different clients for the same 
   user may want different information (e.g. the client performing the join may
   jump to the chat screen and therefore want some messages, whereas the client
   not performing the join just needs to be aware of the new room).
 - As a result, the join response should return events *instead of* to the 
   event stream, depending on the client.
Mapping messages to the event stream:
 - Once you join a room, you will start getting message events for it. How do 
   you know when you started getting events for this room? You need to know so 
   you can provide a token when scrolling back. You cannot currently infer this
   from the join event itself, as individual events do not have tokens (only 
   chunks do).
 - This token can be provided as a separate server-generated event, or an 
   annotation on the join event itself.
 - We propose that a server-generated event is sent down the event stream to all
   clients, rather than annotating the join event. The server-generated event 
   works nicely for Application Services where an entity subscribes to a room 
   without a join event.
 - This will look like an event for the room, but have a special 
   "server-generated" event type e.g. ``m.homeserver.scrollback`` with a 
   ``token`` containing the start token for the room.
What data flows does it address:
 - Home Screen: Joining a room
 
Scrollback API ``[Draft]``
--------------------------
.. NOTE::
 - Pagination: Would be nice to have "and X more". It will probably be 
   Google-style estimates given we can't know the exact number over federation, 
   but as a purely informational display thing it would be nice.

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
 
Contextual windowing API ``[Draft]``
------------------------------------
This refers to showing a "window" of message events around a given message 
event. The window provides the "context" for the given message event.

Inputs:
 - Event ID of the message to get the surrounding context for (this specifies 
   the room to get messages in).
 - Number of messages before/after this message to obtain.
 - Filter to apply.
Outputs:
 - Chunk of messages
 - Start / End pagination tokens
 - Current room state at the end of the chunk as per initial sync.

Room Alias API ``[Draft]``
-------------------------
This provides mechanisms for creating and removing room aliases for a room on a
home server. Typically, any user in a room can make an alias for that room. The
alias creator (or anyone in the room?) can delete that alias. Server admins can
also delete any alias on their server.

Mapping a room alias to a room:

Inputs:
 - Room Alias
Output:
 - Room ID
 - List of home servers to join via.

Mapping a room to an alias:
 
Inputs:
 - Room ID
 - Desired room alias localpart
 - User ID (for auth)
Output:
 - Room alias
Notes:
 - The home server may add restrictions e.g. the user must be in the room.
 
Deleting a mapping:

Inputs:
 - Room alias
 - User ID (for auth)
Output:
 - None.


Public room list API ``[Draft]``
--------------------------------
This provides mechanisms for searching for public rooms on a home server.

Inputs:
 - Search text (e.g. room alias/name/topic to search on)
 - Home server to search on (this may just be the URL hit for HTTP)
 - Any existing pagination token
 - Limit for pagination
Output:
 - Pagination token
 - Total number of rooms
 - Which 'page' of results this response represents
 - A list of rooms with:
    - # users
    - A set of 'public' room state events, presumably ``m.room.name``, 
      ``m.room.topic`` and ``m.room.aliases``. This cannot be user-configured
      since the user is not in the room.
Notes:
 - This API would be hit again for the next page of results, with the pagination
   token provided from the previous hit.
 - We should probably provide "and X more" estimates for the number of 
   pagination results. This can be calculated by providing the total number of 
   rooms e.g. '100' and the page e.g. '3' coupled with the limit parameter (aka
   the number of results per page) specified e.g. '10'. 
 - In order to prevent the dataset from changing underneath the client whilst
   they paginate, a request without a pagination token should take a "snapshot"
   of the underlying data which is then paginated on, rather than the database
   which is a moving target as other clients add new public rooms.


User Profile API ``[Draft]``
---------------------------
Every user on a home server has a profile. This profile is effectively a
key-value store scoped to a user ID. It can include an ``avatar_url``, 
``displayname`` and other metadata. Updates to a profile should propagate to
other interested users.

Setting display name (strings):

Inputs:
 - User ID
 - New display name
Output:
 - None.
Notes:
 - This is a generic problem, so should probably not be special cased for
   display names. E.g. having an arbitrary key-value store here.
 
Setting avatar url (blob data):
 
Inputs:
 - User ID
 - New avatar url / file blob?
Output:
 - None.
Notes:
 - We may want to provide file uploading on this API for convenience.

Retrieving profile information:

Inputs:
 - User ID
 - Which keys to retrieve
Output:
 - The key/values specified.

Propagation
~~~~~~~~~~~
The goals of propagation are:

- Profile updates should propagate to all rooms the user is in. 
- We should support different kinds of profiles for different rooms. 

In v1, users have a single profile. This information is duplicated for
every room the user is in. This duplication means that things like
display names *could* change on a room-by-room basis. However, this is
extremely inefficient when updating the display name, as you have to
send ``num_joined_rooms`` events to inform everyone of the update.

There's no easy solution to this. The room needs a record of the name
changes; it's not good enough to send it just to the users (the set of
all users in all rooms the user changing their display name is in), as
new users who join later still need to know about these changes. The
ordering information needs to be preserved as well. 

An improvement would be to allow the client to not automatically share
updates of their profile information to all rooms.

Account Management API ``[Draft]``
----------------------------------
Users may wish to delete their account, revoke access tokens, manage
their devices, etc. This is achieved using an account management API.

Deleting an account:

Inputs:
 - User ID to delete
 - Auth key (e.g. access_token of user, of server admin, etc)
Output:
 - None.
 
Viewing access tokens related to this account:

Inputs:
 - User ID
 - Auth key (e.g. access_token of user, of server admin, etc)
Output:
 - A list of access tokens (+ last used / creation date / device / user-agent?)

Removing an access token:

Inputs:
 - User ID
 - Auth key (e.g. access_token of user, of server admin, etc)
 - Access token to revoke.
Output:
 - None.

Action APIs
-----------
The following APIs are "action APIs". This is defined to be a request which 
alters the state of a room you are already joined to.

When you perform an action in a room, you immediately want to display the local 
echo. The client can receive the response to the action either directly or from 
the event stream. The order in which you receive these responses is undefined. 
As a result, clients MUST be able to handle all possible orderings::

                 1                           2a                          3
 START ----> REQUEST SENT ---> RESPONSE TO REQUEST RECEIVED --------> GOT BOTH
                 |                                                       ^
                 |                      2b                               |
                 +----------> APPEARS IN EVENT STREAM -------------------+
                 
  1: Can display local echo at this point.
  2a: The request has been successfully processed and can be displayed as Sent.
  2b/3: The request has been successfully processed and the client knows its 
        position in the event stream.

When a client sends a request, they can include an "action ID" so that they can 
match up the event in the event stream to the request which they made. This ID 
is created by the client, and MUST be a monotonically increasing integer for 
that client. This ID serves as a transaction ID for idempotency as well as a 
sequence ID for ordering actions performed in parallel by that client. Events 
for actions performed by a client in that client's event stream will include the
action ID the client submitted when making the request. The action ID will *not*
appear in other client's event streams.

Action IDs are optional and are only needed by clients that retransmit their 
requests, or display local echo, or allow the submission of multiple requests 
in parallel. An example of a client which may not need the use of action IDs 
includes bots which operate using basic request/responses in a synchronous 
fashion.
 
Inviting a user ``[Final]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - User ID
 - Room ID
 - Action ID (optional)
Outputs:
 - Display name / avatar of user invited (if known)
What data flows does it address:
 - Chat Screen: Invite a user
 
Rejecting an invite ``[Final]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Event ID (to know which invite you're rejecting)
Outputs:
 - None.
Notes:
 - Giving the event ID rather than user ID/room ID combo because mutliple users 
   can invite the same user into the same room.
 - Rejecting an invite results in the ``m.room.member`` state event being 
   DELETEd for that user.
   
Sending state events ``[Final]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Event type
 - State key
 - Room ID
 - Content
Outputs:
 - None.
   
Deleting state events ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Event type
 - State key
 - Room ID
Outputs:
 - None.
Notes:
 - This is represented on the event stream as an event lacking a ``content`` 
   key (for symmetry with ``prev_content``)
   
Read-up-to markers ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - State Event type (``m.room.marker.delivered`` and ``m.room.marker.read``)
 - Event ID to mark up to. This is inclusive of the event ID specified.
Outputs:
 - None.
Efficiency notes:
 - Sending "read up to" markers is preferable to sending receipts for every
   message due to scaling problems on the client with one receipt per message.
   This results in an ever increasing amount of bandwidth being devoted to 
   receipts and not messages.
 - For individual receipts, each person would need to send at least 1 receipt 
   for every message, which would give a total number of ``msgs * num_people`` 
   receipts per room. Assuming that people in a room generally converse at say 
   a rate of 1 message per unit time, this scales ``n^2`` on the number of 
   people in the room.
 - Sending "read up to" markers in contrast allows people to skip some messages
   entirely. By making them state events, each user would clobber their own 
   marker, keeping the scaling at ``n``. For scrollback, the event filter would
   NOT want to retrieve these markers as they will be updated frequently.
 - This primarily benefits clients when doing an initial sync. Event graphs 
   will still have a lot of events, most of them from clobbering these state 
   events. Some gains can be made by skipping receipts, but it is difficult to 
   judge whether this would be substantial.
Notes:
 - What do you do if you get a marker for an event you don't have? Do you fall
   back to some kind of ordering heuristic e.g. ``if origin_server_ts > 
   latest message``. Do you request that event ID directly from the HS? How do
   you fit that in to the message thread if you did so? Would probably have to
   fall back to the timestamp heuristic. After all, these markers are only ever
   going to be heuristics given they are not acknowledging each message event.
 
Kicking a user ``[Final]``
~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - User ID
 - Room ID
 - Action ID (optional)
Outputs:
 - None.
What data flows does it address:
 - Chat Screen: Kick a user

Leaving a room ``[Final]``
~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Room ID
 - A way of identifying the user (user ID, access token)
 - Action ID (optional)
Outputs:
 - None.
What data flows does it address:
 - Chat Screen: Leave a room
 
Send a message ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
  Semantics for HTTP ordering. Do we really want to block requests with higher
  sequence numbers if the server hasn't received earlier ones? Is this even
  practical, given clients have a limit on the number of concurrent connections?
  How can this be done in a way which doesn't suck for clients? Could we just
  say "it isn't 'Sent' until it comes back down your event stream"?

Inputs:
 - Room ID
 - Message contents
 - Action ID (optional)
 - Whether the full event should be returned, or a compact version (default=full)
Outputs:
 - The actual event sent incl content OR:
 - The extra keys added or keys modified e.g. 'content' from a policy server 
   (if compact=true)
What data flows does it address:
 - Chat Screen: Send a Message
Ordering notes:
 - HTTP: When sending a message with a higher seqnum, it will block the request 
   until it receives earlier seqnums. The block will expire after a timeout and
   reject the message stating that it was missing a seqnum.
E2E Notes:
 - For signing: You send the original message to the HS and it will return the 
   full event JSON which will be sent. This full event is then signed and sent 
   to the HS again to send the message.
Compact flag notes:
 - You need to know information about the event sent, including the event ID,
   timestamp, etc.
 - Default behaviour will return the entire event JSON sent to make client
   implementations simple (just clobber it).
 - It sucks to have your own messages echoed back to you in response though.
   As a result, you can ask for a compact version which just sends down the
   keys which were added, e.g. timestamp and event ID.

Presence API ``[ONGOING]``
--------------------------
.. NOTE::
 - Per device presence: how does this work? Union of devices? Priority order for
   statuses? E.g. online trumps away trumps offline. So if any device is online,
   then the user is online, etc.
 - Presence lists / roster? We probably do want this, but are we happy with the
   v1 semantics?
   

When a session starts, the home server can treat the user as "online". When the 
session ends, the home server can treat the user as "offline".

Inputs:
 - Presence state (online, offline, away, busy, do not disturb, etc)
Outputs:
 - None.


Typing API ``[ONGOING]``
------------------------
.. NOTE::
 - Linking the termination of typing events to the message itself, so you don't 
   need to send two events and don't get flicker?

When in a session, a user can send a request stating that they are typing in a 
room. They are no longer typing when either the session ends or they explicitly 
send another request to say they are no longer typing.

Inputs:
 - Room ID
 - Whether you are typing or not.
Output:
 - None.
Notes:
 - Typing will time out when the session ends. If a session is restarted, the 
   typing notification must be sent again.
 
Relates-to pagination API ``[Draft]``
-------------------------------------
See the "Relates to" section for more info.

Inputs:
 - Event ID
 - Pagination token
 - limit
Output:
 - A chunk of child events
 - A new pagination token for earlier child events.
 
Capabilities API ``[ONGOING]``
------------------------------
.. NOTE::
 - Server capabilities: Keep hashing step for consistency or not? Extra request
   if we do.
 - Client capabilities: Clients which are offline but can be pushed should have 
   their capabilities visible. How to manage unregistering them e.g. if they 
   uninstall the app? Have a set of 'offline' capabilities?
  

How does a client know if the server it is using supports a content repository? 
How does a client know if another client has VoIP support? This section outlines
capability publishing for servers, clients and federation.

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

When a session is started, the client needs to provide a capability set. The 
server will take the hashes of all the user's connected clients' capability 
sets and send the list of hashes as part of presence information 
(not necesarily as a ``m.presence`` event, but it should act like presence 
events). It is sent as a list instead of a union of hashes because hashes work
best when they don't change. A union of many devices' hashes will change 
frequently when devices come on and offline (``max hashes = 2^num_devices``). 
In contrast, the size of the list would vary, but the hashes themselves 
would remain the same for a given device (``max hashes = num_devices``). Keeping
the hashes the same is the best as that means clients do not need to request
the capabilities for the given hash.

On first signup, the client will attempt to send the hash and be most likely 
refused by the home server as it does not know the full capability set for that 
hash. The client will then have to upload the full capability set to the home 
server. The client will then be able to send the hash as normal.

When a client receives a hash, the client will either recognise the hash or 
will have to request the capability set from their home server:

Inputs:
 - Hash
 - User ID
Output:
 - A list of capabilities

Federation
~~~~~~~~~~
- e.g. Whether you support backfill, hypothetical search/query/threading APIs
- Same as the server capability API

VoIP ``[TODO]``
---------------
This addresses one-to-one calling with multiple devices. This uses the 
``updates`` key to handle signalling.

Event updates
~~~~~~~~~~~~~
- Call is placed by caller. Event generated with offer.
- 1-N callees may pick up or reject this offer.
- Callees update the event (with sdp answer if they are accepting the call)
- Caller acknowledges *one* of the callees (either one which picked up or 
  rejected) by updating the event.
- Callees who weren't chosen then give up (Answered elsewhere, Rejected 
  elsewhere, etc)
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


General client changes
----------------------
These are changes which do not introduce new APIs, but are required for the new
APIs in order to fix certain issues.
 
Sessions ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
 - Offline mode? How does that work with sessions? Separate endpoint to say
   "start a session only"?

A session is a group of requests sent within a short amount of time by the same 
client. Sessions time out after a short amount of time without any requests. 
Starting a session is known as going "online". Its purpose is to wrap up the 
expiry of presence and typing notifications into a clearer scope. A session 
starts when the client makes any request. A session ends when the client doesn't
make a request for a particular amount of time (times out). A session can also 
end when explicitly hitting a particular endpoint. This is known as going 
"offline".

When a session starts, a session ID is sent in response to the first request the
client makes. This session ID should be sent in *all* subsequent requests. If 
the server expires a session and the client uses an old session ID, the server 
should fail the request with the old session ID and send a new session ID in 
response for the client to use. If the client receives a new session ID 
mid-session, it must re-establish its typing status and presence status, as they
are linked to the session ID.
 
Action IDs ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
 - HTTP Ordering: Blocking requests with higher seqnums is troublesome if there 
   is a max # of concurrent connections a client can have open. 
 - Session expiry: Do we really have to fonx the request if it was done with an 
   old session ID?

Action IDs are scoped per session. The first action ID for a session should be 
0. For each subsequent action request, the ID should be incremented by 1. It 
should be reset to 0 when a new session starts.

If the client sends an action request with a stale session ID, the home server 
MUST fail the request and start a new session. The request needs to be failed 
in order to avoid edge cases with incrementing action IDs.

Updates (Events) ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Events may update other events. This is represented by the ``updates`` key. This
is a key which contains the event ID for the event it relates to. Events that 
relate to other events are referred to as "Child Events". The event being 
related to is referred to as "Parent Events". Child events cannot stand alone as
a separate entity; they require the parent event in order to make sense.

Bundling
++++++++
Events that relate to another event should come down inside that event. That is,
the top-level event should come down with all the child events at the same time.
This is called a "bundle" and it is represented as an array of events inside the
top-level event.There are some issues with this however:

- Scrollback: Should you be told about child events for which you do not know 
  the parent event? Conclusion: No you shouldn't be told about child events. 
  You will receive them when you scroll back to the parent event. 
- Pagination of child events: You don't necessarily want to have 1000000s of 
  child events with the parent event. We can't reasonably paginate child events
  because we require all the child events in order to display the event 
  correctly. Comments on a message should be done via another technique,
  such as ``relates_to``.
- Do you allow child events to relate to other child events? There is no 
  technical reason why we cannot nest child events, however we can't think of 
  any use cases for it. The behaviour would be to get the child events 
  recursively from the top-level event. 
  
Main use cases for ``updates``:
 - Call signalling (child events are ICE candidates, answer to the offer, and 
   termination)
 - *Local* Delivery/Read receipts : "Local" means they are not shared with other
   users on the same home server or via federation but *are* shared between 
   clients for the same user; useful for push notifications, read count markers,
   etc. This is done to avoid the ``n^2`` problem for sending receipts, where 
   the vast majority of traffic tends towards sending more receipts.
 - s/foo/bar/ style message edits
 
Clients *always* need to know how to apply the deltas because clients may 
receive the events separately down the event stream. Combining event updates 
server-side does not make client implementation simpler, as the client still 
needs to know how to combine the events.

Relates to (Events) ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Events may be in response to other events, e.g. comments. This is represented 
by the ``relates_to`` key. This differs from the ``updates`` key as they *do 
not update the event itself*, and are *not required* in order to display the 
parent event. Crucially, the child events can be paginated, whereas ``updates`` 
child events cannot be paginated.

Bundling
++++++++
Child events can be optionally bundled with the parent event, depending on your 
display mechanism. The number of child events which can be bundled should be 
limited to prevent events becoming too large. This limit should be set by the 
client. If the limit is exceeded, then the bundle should also include a 
pagination token so that the client can request more child events.

Main use cases for ``relates_to``:
 - Comments on a message.
 - Non-local delivery/read receipts : If doing separate receipt events for each 
   message.
 - Meeting invite responses : Yes/No/Maybe for a meeting.

Like with ``updates``, clients need to know how to apply the deltas because 
clients may receive the events separately down the event stream.

TODO:
 - Can a child event reply to multiple parent events? Use case?
 - Should a parent event and its children share a thread ID? Does the 
   originating HS set this ID? Is this thread ID exposed through federation? 
   e.g. can a HS retrieve all events for a given thread ID from another HS?

   
Example using 'updates' and 'relates_to'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Room with a single message.
- 10 comments are added to the message via ``relates_to``.
- An edit is made to the original message via ``updates``.
- An initial sync on this room with a limit of 3 comments, would return the 
  message with the update event bundled with it and the most recent 3 comments 
  and a pagination token to request earlier comments
  
  .. code :: javascript
  
    {
      content: { body: "I am teh winner!" },
      updated_by: [
        { content: { body: "I am the winner!" }, ... }
      ],
      replies: {
        start: "some_token",
        chunk: [
          { content: { body: "8th comment" }, ... },
          { content: { body: "9th comment" }, ... },
          { content: { body: "10th comment" }, ... }
        ]
      },
      ...
    }
    
Events (breaking changes; event version 2) ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Prefix the event ``type`` to say if it is a state event, message event or 
  ephemeral event. Needed because you can't tell the different between message 
  events and ephemeral ROOM events (e.g. typing).
- State keys need additional restrictions in order to increase flexibility on 
  state event permissions. State keys prefixed with an ``_`` have no specific 
  restrictions. 0-length state keys are now represented by just a single ``_``.
  State keys prefixed with ``@`` can be modified only by the named user ID *OR* 
  the room ops. They can have an optional path suffixed to it. State keys that 
  start with a server name can only be modified by that server name (e.g. 
  ``some.server.com/some/path`` can only be modified by ``some.server.com``).
- Do we want to specify what restrictions apply to the state key in the event 
  type? This would allow HSes to enforce this, making life easier for clients 
  when dealing with custom event types. E.g. ``_custom.event`` would allow 
  anything in the state key, ``_@custom.event`` would only allow user IDs in 
  the state key, etc.
- s/user_id/sender/g given that home servers can send events, not just users.

 
