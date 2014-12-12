API Changes Summary
===================
- Split up requesting tokens from delivering the data. This allows you to config many different tokens depending on the
  client. In v1, you could only hit /initialSync and get everything, even if that isn't what you wanted.
  
- Introduction of an 'event filtering token'. This filters the event types returned from streams/pagination. Clients may
  have several of these in use at any moment, depending on the endpoint they are hitting.

- All APIs which return events can optionally take a streaming token parameter. The server uses this to manage how events
  are sent to the client (either in response to the API call or via the stream, eg but not both for duplicate info reduction).
  This does mean each device would have a different streaming token.

- New API: Scrollback API. This is designed to be used when you click on a room and want to display something. It is used
  in conjunction with a max # events limit. If you have some previous data, then you supply your streaming token. 
  If there are > max events between that event ID and now, it returns a brand new page of events and a new
  pagination token. If there are < max events, it just returns them incrementally. This supports both heavy/lightweight
  clients. This can use the event filtering token to allow only 'displayable' events to be shown.
  
- New API: Pagination Overview API: This is designed for cases like forum threads, which tell you how many pages there are
  and allow you to jump around. This API returns an array of pagination tokens which represent each page. You tell it how
  many events per page. This can use the event filtering token to allow only 'displayable' events to be shown.

Resolves issues:
----------------
- You can't get events for a single room only as the event stream is global. FIX: You specify via the stream token.
- You can't filter between "data" events (e.g. m.room.message) for display, and "metadata" events (e.g. power level changes).
  FIX: You specify via the event filter token.
- There are race conditions when getting events via room initial sync and from the event stream. FIX: optional streaming
  token param allows intelligent suppression
- You can't tell if an event you PUT is the same event when it comes down the event stream. FIX: optional streaming token 
  param allows intelligent suppression]
- How do you obtain partial room state / handle large room state? FIX: You specify via the event filter token.
- How do you sensibly do incremental updates? FIX: You give it a streaming token to return incremental updates.

Outstanding Issues
------------------
- Duplication of events in /initialSync is sub-optimal

Issues not addressed
--------------------
These issues are more implementation specific (HTTP/JSON) and therefore haven't been addressed by this data model:

- Naming of endpoints / keys isn't great
- Can't set power levels incrementally.
- State event PUTs are not consistent with other APIs.

These issues are added features which have not been addressed:

- Accessing federation level events (prev_pdus, signing keys, etc)
- How do you reject an invite?
- How do you delete state?
- Paginating on global initial sync e.g. 10 most recently active rooms.
- How do you determine the capabilities of a given HS?

These issues are federation-related which have not been addressed:

- Pagination can take a while for backfill. FIX: Add flag to say server_local vs backfill_yes_please? Given the client
  is best suited to say how long they are willing to wait.
- Sending events may need to be multi-stage e.g. for signing. FIX: Extra 'Action API' added. Shouldn't be too invasive.
- Handle rejection of events after the fact. e.g. HS later finds out that it shouldn't have accepted an event.
  TODO: Clarifiy if 'rejection' === redaction.

These issues relate to events themselves which have not been addressed:

- Distinguish between *room* EDUs (e.g. typing) and PDUs
- Event timestamps (ISO8601?)


Meta APIs (API calls used to configure other APIs)
==================================================

Generating an event filtering token
-----------------------------------
Args:
 | Event Type Filter <[String]> (e.g. ["m.*", "org.matrix.custom.*", "my.specific.event.type"])
Response:
 | Event Filter Token <String>
Use Cases:
 | Picking out "displayable" events when paginating.
 | Reducing the amount of unhandled event types being sent to the client wasting bandwidth
 | Control whether presence is sent to the client (useless if they don't display it on the client!)

Generating a streaming token
----------------------------
Args:
 | Stream Config <Object> -> 
 | Room ID Filter <[String]> (e.g. ["!asd:foo.bar", "!dsf:foo.bar", ...]
 | User ID Filter <[String]> (e.g. ["@friend:foo.bar", "@boss:foo.bar", ...] or ["*"]) - e.g. control which user presence to get updates for
Response:
 | Token <String>
Use Cases:
 | Lightweight monitor-only-this-room-please
 | Heavyweight ALL THE THINGS
 | Middle of the road (all rooms joined with latest message + room names/aliases, rooms invited to + room names/aliases)


Action APIs (performs some sort of action)
==========================================

Create Room
-----------
Args:
 | Creation Config -> Join rules <String>, Visibility <String>
 | Response Config -> Events/filters/etc
 | Invitees <[String]>
Response:
 | Room ID <String>
 | Response <Object> (Optional)
Use Cases:
 | Create 1:1 PM room.
 | Create new private group chat
 | Create new public group chat with alias
 | Create new "forum thread"

Send Message
------------
Args:
 | Room ID <String>
 | Event Content <Object>
 | Event Type <String>
 | State Key <String> (Optional)
Response:
 | ??? ACK ???
Use Cases:
 | Sending message to a room.
 | Sending generic events to a room.
 | Sending state events to a room.
 | Send message in response to another message (commenting)
 
Joining a room
--------------
Args:
 | Invite Event ID(?sufficient?) OR Room Alias <String> : This is how you accept an invite.
 | Response Config <Object> -> Events/filters/etc
Response:
 | Room ID <String>
 | Response <Object> (Optional)
Use Cases:
 | Joining a room from an invite
 | Joining a room from a room alias


Invite/Leave/Kick/Ban
---------------------
Args:
 | Room ID <String>
 | User ID <String>
 | Reason/Invitation Text <String> (Optional)
Response:
 | ? ACK ?

 
Syncing APIs
============
 
Scrollback (aka I clicked a room and now want to display something)
-------------------------------------------------------------------
Args:
 | Room ID <String>
 | Max # Message Events <Integer>
 | Message Event Filter Token <String> (allows just 'displayable' events)
 | *Current* State Event Filter Token <String> (get member list, etc)
 | Streaming Token <String>
Response:
 | Events <[Object]>
 | Incremental <Boolean> - True if the events are incremental from the streaming token provided. If false, there is > Max # events between NOW and the token provided.
 | Pagination Token <String> - The start token for the earliest message if not incremental.
Use Cases:
 | Open a room and display messages (if no perm storage, supply no stream token to get the latest X events)
 | Open a room and get incremental (supply stream token and get either incremental messages or a new fresh lot depending on amount of events)
                                  
Syncing (aka I want live data)
------------------------------
NB: Does NOT provide any sort of 'catchup' service. This keeps the API simpler, and prevents potential attacks where people are dumb/maliciously request from ancient streaming tokens which then return 100000s of events, slowing down the HS. Alternatively, we could expire streaming tokens after a given time (but that doesn't help if 10000s of events come down really quickly). The general idea is to block all forms of historical data behind max events limits.

Args:
 | Streaming Token <String>
 | Event Filtering Token <String> (optional)
Response:
 | ??? EVENT STREAM DATA ???
 | Updated Streaming Token <String>
Use Cases:
 | Getting events as they happen.
 
 
Pagination (aka The user is infinite scrolling in a room)
---------------------------------------------------------
Getting messages:

Args:
 | Pagination Token <String>
 | Event Filter Token <String>
 | Room ID <String>
 | Max # Events <Integer>
Response:
 | Events [<Object>]
 | New Pagination Token <String>
Use Cases:
 | Infinite scrolling

Requesting overview of pagination:

Args:
 | Event Filter Token <String>
 | Room ID <String>
 | Max # Events per page <Integer>
Response:
 | Pagination Tokens<[String]> - A snapshot of all the events *at that point* with the tokens you need to feed in to get each page. E.g. to get the 1st page, use token[0] into the "Getting messages" API.
Use Cases:
 | Forum threads (page X of Y) - Allows jumping around.

Initial Sync (aka I just booted up and want to know what is going on)
---------------------------------------------------------------------
Args:
 | Message Events Event Filter Token <String> - the filter applied to message events f.e room
 | *Current* State Event Filter Token <String> - the filter applied to state events f.e room. Can specify nothing to not get ANY state events.
 | Max # events per room <Integer> - can be 0
 | Streaming Token <String> - A streaming token if you have one, to return incremental results
Response:
 | Events per room [<Object>] - Up to max # events per room. NB: Still get duplicates for state/message events!
 | Pagination token per room (if applicable) [<String>] - Rooms which have > max events returns a fresh batch of events (See "Scrollback")
Use Cases:
 | Populate recent activity completely from fresh.
 | Populate recent activity incrementally from a token.
 | Populate name/topic but NOT the name/topic changes when paginating (so m.room.name in state filter but not message filter)

 
Examples
========

Some examples of how these APIs could be used (emphasis on syncing since that is the main problem).

#1 SYWEB recreation
-------------------
The aim of this is to reproduce the same data as v1, as a sanity check that this API is functional.

- Login. POST streaming token (users["*"], rooms["*"]). Store token.
- GET /initialSync max=30 with token. Returns all rooms (because rooms["*"]) and all state, and all presence (because users["*"]),
  and 30 messages. All event types returned since I didn't supply any event filter tokens. Since the streaming token 
  hasn't ever been used (I just made one), it returns the most recent 30 messages f.e room. This is semantically the same
  as v1's /initialSync.
- GET /eventStream with streaming token. Starts blocking.
- Click on room !foo:bar. Start infinite scrolling.
- GET /paginate. Pagination token from initial sync. Get events and store new pagination token.

#2 Less buggy SYWEB recreation
------------------------------
The aim of this is to leverage the new APIs to fix some bugs.

- Login. POST streaming token (users["*"], rooms["*"]). Store stream token.
- POST event filter token (["m.room.message", "m.room.topic", "m.room.name", "m.room.member"]). Store as Message Event filter token.
- POST event filter token (["m.room.name", "m.room.topic", "m.room.member"]). Store as Current State Event filter token.
- GET /initialSync max=1 with all tokens. Returns all rooms (rooms["*"]), with name/topic/members (NOT all state), with
  max 1 m.room.message/topic/name/member (truly honouring max=1), with presence (users["*"]).
- GET /eventStream with stream token. Blocks.
- Click on room !foo:bar. Start infinite scrolling.
- GET /paginate with Message Event filter token. Returns only m.room.message/name/topic/member events.

#3 Mobile client (permanent storage)
------------------------------------
The aim of this is to use the new APIs to get incremental syncing working.

Initially:

- Login. POST streaming token (users["*"], rooms["*"]). Store as stream token.
- POST event filter token (["m.room.message"]). Store as Message Event filter token.
- POST event filter token (["m.*"]). Store as Current State Event filter token.
- GET /initialSync max=30 (we want a page worth of material) with all tokens. Returns all rooms (rooms["*"]), 
  with all m.* current state, with max 1 m.room.message, with presence (users["*"]).
- GET /eventStream with stream token. Blocks.
- Get some new events, new stream token. Quit app.

Subsequently:

- GET /initialSync max=30 with all tokens. Because the stream token has been used before, it tries to get the diff between
  then and now, with the filter tokens specified. If it finds > 30 events for a given room, it returns a brand new page 
  for that room. If it finds < 30 events, it returns those events. Any new rooms are also returned. Returns a new stream token.
- GET /eventStream with new stream token. Blocks.

#4 Lightweight client (super lazy loading, no permanent storage)
----------------------------------------------------------------
The aim of this is to have a working app with the smallest amount of data transfer. Event filter tokens MAY be reused
if the lightweight client persists them, reducing round-trips.

- POST streaming token (rooms["*"] only, no presence). Store as streaming token.
- POST event filter token (["m.room.message"]). Store message event filter token.
- POST event filter token (["m.room.name"]). Store as current state event filter token.
- POST event filter token (["m.room.message", "m.room.name", "m.room.member"]). Store as eventStream filter token.
- GET /initialSync max=1 with all tokens. Returns all rooms (rooms["*"]), with 1 m.room.message, no presence, and just
  the current m.room.name if a room has it.
- Click on room !foo:bar.
- POST streaming token (rooms["!foo:bar"]), store as foo:bar token.
- GET /eventStream with foo:bar token AND eventStream token. This will get new messages (m.room.message) and room name
  changes (m.room.name). It will also get me new room invites (m.room.member) and join/leave/kick/ban events (m.room.member),
  all JUST FOR THE ROOM !foo:bar.
  
