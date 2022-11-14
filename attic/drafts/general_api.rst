Table of Contents
=================

.. contents:: Table of Contents
.. sectnum::

Summary of changes from v1
==========================

Version 2.0
-----------
- Event filtering (type/room/users, federation-style events)
- Incremental initial syncing
- Deleting state
- Race conditions on event stream / actions
- Out-of-order events
- Published room API: support searching remote HSes.
- Account management: specifically the concept of devices so push works.
- Multiple devices
   - Presence status unioning: is partially specced (needs more eyes).
   - Syncing data between multiple devices: is specced.  
   - TODO: Push for offline devices.

Lower priority
~~~~~~~~~~~~~~
- Capabilities
- Editing/updating messages (updates key)
- Room alias API

Version 2.1
-----------
- Comments (relates_to key)
- Contextual messages (view messages around an arbitrary message)
- Rejecting invites
- State event pagination (e.g. from initial sync)
- Initial sync pagination (e.g. X most recent rooms)
 
Out of scope
------------
- Searching messages

Version 2 API
=============

Legend:
 - ``[TODO]``: API is not in this document yet.
 - ``[ONGOING]``: API is proposed but needs more work. There are known issues 
   to be addressed.
 - ``[Draft]``: API is proposed and has no outstanding issues to be addressed, 
   but needs more feedback.
 - ``[Final]``:  The API has no outstanding issues.

This contains the formal proposal for Matrix Client-Server API v2. This API 
would completely replace v1. It is a general API, not specific to any particular 
protocol e.g. HTTP. The following APIs will remain unchanged from v1:

- Content repository API

This version will change the path prefix for HTTP:
 - Version 1: ``/_matrix/client/api/v1``
 - Version 2: ``/_matrix/client/v2``
 
Note the lack of the ``api`` segment. This is for consistency between other 
homeserver path prefixes.

Terminology:
 - ``Chunk token`` : An opaque string which can be used to return another chunk
   of results. For example, the initial sync API and scrollback/contextual 
   windowing APIs. If the total size of the data set is unknown, it should
   return a chunk token to navigate it.
 - ``Filter token`` : An opaque string representing the inputs originally given
   to the filter API.
 - ``Pagination token`` : An opaque string used for pagination requests. For
   example, the published room list API. The size of the data set is known (e.g.
   because a snapshot of it was taken) and you can do "Page X of Y" style 
   navigation.

 
Filter API ``[Draft]``
------------------------

Inputs:
 - Which event types (incl wildcards)
 - Which room IDs
 - Which user IDs (for profile/presence)
 - Whether you want federation-style event JSON
 - Whether you want coalesced ``updates`` events
 - Whether you want coalesced ``relates_to`` events (and the max # to coalesce,
   and the relationship types, and the sort order)
 - limit= param? (XXX: probably not; this should be done in the query itself)
 - Which keys to return for events? e.g. no ``origin_server_ts`` if you don't 
   show timestamps (n.b. encrypted keys can't be filtered out)
Outputs:
 - An opaque token which represents the inputs, the "filter token".
Notes:
 - The token may expire, in which case you would need to request another one.
 - The token could be as simple as a concatenation of the requested filters with
   a delimiter between them.
 - Omitting the token on APIs results in ALL THE THINGS coming down.
 - Clients should remember which token they need to use for which API.
 - It should be possible to define negative filters (e.g. not presence)
 - HTTP note: If the filter API is a separate endpoint, then you could easily 
   allow APIs which use filtering to ALSO specifiy query parameters to tweak the
   filter.

Global initial sync API ``[Draft]``
-------------------------------------
.. NOTE::
 - The output to this should also have something like:
    For each room the user is invited to:
      - The invite event
      - Other state info (e.g. room name, topic, join_rules to know if pubilc)
      - # members?

    so clients know more information about the room other than the user_id of the
    inviter, timestamp and the room ID.

 v2.1:
   - Will need some form of state event pagination like we have for message 
     events to handle large amounts of state events for a room. Need to think of
     the consequences of this: you may not get a ``m.room.member`` for someone's 
     message and so cannot display their display name / avatar. Do we want to 
     provide pagination on an event type basis?
   - Handle paginating initial sync results themselves (e.g. 10 most recent 
     rooms)

Inputs:
 - A way of identifying the user (e.g. access token, user ID, etc)
 - Filter to apply (e.g. a single room ID for a 'room initial sync')
 - Chunk token (for incremental deltas)
Outputs:
 - For each room the user is joined:
    - Requested state events
    - # members
    - max of limit= message events
    - room ID
Notes:
 - If a chunk token is applied, you will get a delta relative to the last request
    performed with that streaming token rather than all the rooms.
Compacting notes:
 - Fixes the problem with the same event appearing in both the ``messages`` and
   ``state`` keys. Represent as something like::

     {
       events: { event_id: Event, ... },
       messages: [ event_id, event_id, ...],
       state: [ event_id, event_id, ...],
     }
Duplicate content notes:
 - For non-compacted state events, duplicate state events in the ``messages`` 
   key need to have a ``prev_content`` to correctly display the state change 
   text. This is not required for ``state`` key events, which just represent 
   the *current* state and as such do not need a ``prev_content``. Compacted 
   state events will need to specify the ``prev_content``.
What data flows does it address:
 - Home screen: data required on load.
 - XXX: would this also be used for initially loading room history screens too?

Event Stream API ``[Draft]``
----------------------------
Inputs:
 - Position in the stream (chunk token)
 - Filter to apply: which event types, which room IDs, whether to get 
   out-of-order events, which users to get presence/profile updates for
 - User ID
 - Device ID
Outputs:
 - 0-N events the client hasn't seen. NB: Deleted state events will be missing a
   ``content`` key. Deleted message events are ``m.room.redaction`` events.
 - New position in the stream. (chunk token)
State Events Ordering Notes:
 - Homeservers may receive state events over federation that are superceded by 
   state events previously sent to the client. The homeserver *cannot* send 
   these events to the client else they would end up erroneously clobbering the
   superceding state event. 
 - As a result, the homeserver reserves the right to omit sending state events 
   which are known to be superceded already.
 - This may result in missed *state* events. However, the state of the room will
   always be eventually consistent.
Message Events Ordering Notes:
 - Homeservers may receive message events over federation that happened a long 
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
 - A homeserver may find out via federation that it should not have accepted 
   an event (e.g. to send a message/state event in a room). For example, it may
   send an event to another homeserver and receive an auth event stating 
   that the event should not have been sent. 
 - If this happens, the homeserver will send a ``m.room.redaction`` for the 
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
  - Invitee list of user IDs, published/not, state events to set on creation 
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
 
Room History
------------
This concerns APIs which return historical events for a room. There are several
common parameters.

Inputs:
 - Room ID
 - Max number of events to return
 - Filter to apply.
Outputs:
 - Requested events
 - Chunk token to use to request more events.

 
Scrollback API ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
 - Pagination: Would be nice to have "and X more". It will probably be 
   Google-style estimates given we can't know the exact number over federation, 
   but as a purely informational display thing it would be nice.

Additional Inputs:
 - flag to say if the homeserver should do a backfill over federation
Additional Outputs:
 - whether there are more events on the local HS / over federation.
What data flows does it address:
 - Chat Screen: Scrolling back (infinite scrolling)
 
Contextual windowing API ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This refers to showing a "window" of message events around a given message 
event. The window provides the "context" for the given message event.

Additional Inputs:
 - Event ID of the message to get the surrounding context for (this specifies 
   the room to get messages in).
 - Whether to get results before / after / around (mid point) this event
Additional Outputs:
 - Start / End chunk tokens to go either way (not just one token)
 - Current room state at the end of the chunk as per initial sync.

Room Alias API ``[Draft]``
--------------------------
This provides mechanisms for creating and removing room aliases for a room on a
homeserver. Typically, any user in a room can make an alias for that room. The
alias creator (or anyone in the room?) can delete that alias. Server admins can
also delete any alias on their server.

Mapping a room alias to a room:

Inputs:
 - Room Alias
Output:
 - Room ID
 - List of homeservers to join via.

Mapping a room to an alias:
 
Inputs:
 - Room ID
 - Desired room alias localpart
 - User ID (for auth)
Output:
 - Room alias
Notes:
 - The homeserver may add restrictions e.g. the user must be in the room.
 
Deleting a mapping:

Inputs:
 - Room alias
 - User ID (for auth)
Output:
 - None.


Published room list API ``[Draft]``
-----------------------------------
This provides mechanisms for searching for published rooms on a homeserver.

Inputs:
 - Search text (e.g. room alias/name/topic to search on)
 - Homeserver to search on (this may just be the URL hit for HTTP)
 - Any existing pagination token, can be missing if this is the first hit.
 - Limit for pagination
Output:
 - Pagination token
 - Total number of rooms
 - Which 'page' of results this response represents
 - A list of rooms with:
    - # users
    - A set of 'publishable' room state events, presumably ``m.room.name``, 
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
   which is a moving target as other clients add new published rooms.


User Profile API ``[Draft]``
----------------------------
Every user on a homeserver has a profile. This profile is effectively a
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
  
Propagation ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~
The goals of propagation are:

- Profile updates should propagate to all rooms the user is in so
  rooms can display change events. Due to this, profile propagation
  HAS to be in the event graph for the room, in order to place it in
  the right position.
- We should support different kinds of profiles for different rooms. 
- Propagation should avoid flicker between joining a room and getting
  profile information.

In v1, this was achieved by sending ``displayname`` and ``avatar_url``
keys inside the ``content`` of an ``m.room.member`` event. This event
type was chosen in order to prevent flicker on the client, as all the
information came down in one lump.

This had a number of problems associated with it:

- It conflated profile info and membership info, simply to avoid client
  flicker.
- Name/avatar changes created more ``m.room.member`` events which meant
  they needed to be included in the auth chains for federation. This
  created long auth chains which is suboptimal since homeservers need
  to store the auth chains forever.

These problems can be resolved by creating an ``m.room.member.profile``
event which contains profile information. This reduces the number of
``m.room.member`` events over federation, since profile changes are of
a different event type. This also prevents conflation of profile changes
and membership changes.

However, this introduces its own set of problems, namely flicker. The
client would receive the ``m.room.member`` event first, followed by
the ``m.room.member.profile`` event, which could cause a flicker. In
addition, federation may not send both events in a single transaction,
resulting in missing information on the receiving homeserver.

For federation, these problems can be resolved by sending the 
``m.room.member`` event as they are in v1 (with ``displayname`` and 
``avatar_url`` in the ``content``). These keys need to be signed so
they cannot be in the ``unsigned`` part of the event. The receiving home 
server will then extract these keys and create a server-generated 
``m.room.member.profile`` event. To avoid confusion with duplicate 
information, the ``avatar_url`` and ``displayname`` keys should be 
removed from the ``m.room.member`` event by the receiving homeserver.
When a client requests these events (either from the event stream
or from an initial sync), the server will send the generated
``m.room.member.profile`` event under the ``unsigned.profile`` key of the
``m.room.member`` event. Subsequent profile updates are just sent as
``m.room.member.profile`` events.

For clients, profile information is now *entirely* represented in
``m.room.member.profile`` events. To avoid flicker, this event is 
combined with the ``m.room.member`` event under an ``unsigned.profile``
key.

::

   Case #1: @user:domain "User" joins a room

   HS --> HS:
   {
     content: {
       displayname: "User",
       membership: "join"
     },
     type: "m.room.member",
     [...]
   }
   
   Receiving HS transformation:
   {
     content: {
       <remove displayname key>
       membership: "join"
     },
     type: "m.room.member",
     [...]
   }
   
   Receiving HS creates new server-generated event:
   {
     content: {
       displayname: "User"
     },
     type: "m.room.member.profile",
     [...]
   }
   
   Client sees: (e.g. from event stream / initial sync)
   {
     content: {
       membership: "join"
     },
     type: "m.room.member",
     unsigned: {
       profile: {
         content: {
           displayname: "User"
         },
         type: "m.room.member.profile",
         [...]
       }
     }
     [...]
   }
   
::

   Case #2: @user:domain "User" updates their display name to "User2"
            (they are already in the room)
            
   HS --> HS:
   {
     content: {
       displayname: "User2"
     },
     prev_content: {
       displayname: "User"
     },
     type: "m.room.member.profile",
     [...]
   }
   
   Client sees:
   {
     content: {
       displayname: "User2"
     },
     prev_content: {
       displayname: "User"
     },
     type: "m.room.member.profile",
     [...]
   }

The removal of the ``displayname`` and ``avatar_url`` keys from ``m.room.member``
can only be done if the client trusts their HS, as it will break the sending HS's
signature. Requesting the "raw" federation event will have to return these keys.

Account Management API ``[Draft]``
----------------------------------
The registration and login APIs in v1 do not support specifying device IDs. In v2,
this will become *mandatory* when sending your initial request. Access tokens will
be scoped per device, so using the same device ID twice when logging in will 
clobber the old access token.

In terms of additional APIs, users may wish to delete their account, revoke access 
tokens, manage their devices, etc. This is achieved using an account management API.

Deleting an account:

Inputs:
 - User ID to delete
 - Auth key (e.g. access_token of user, of server admin, etc)
Output:
 - None.
 
Viewing devices related to this account:

Inputs:
 - User ID
 - Auth key (e.g. access_token of user, of server admin, etc)
Output:
 - A list of devices (+ last used / access tokens / creation date / device / 
   user-agent?)

Removing an access token:

Inputs:
 - User ID
 - Auth key (e.g. access_token of user, of server admin, etc)
 - Access token to revoke.
Output:
 - None.
 
Removing a device:

Inputs:
 - User ID
 - Auth key (e.g. access_token of user, of server admin, etc)
 - Device ID to remove.
Output:
 - None.
Notes:
 - This revokes all access tokens linked to this device.

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
is created by the client. This ID serves as a transaction ID for idempotency 
as well as a marker to match the response when it appears in the event stream. 
Events for actions performed by a client in that client's event stream will 
include the action ID the client submitted when making the request. The 
action ID will *not* appear in other client's event streams.

Action IDs are optional and are only needed by clients that retransmit their 
requests or display local echo. An example of a client which may not need the 
use of action IDs includes bots which operate using basic request/responses 
in a synchronous fashion.

A client may wish to send multiple actions in parallel. The send event APIs
support sending multiple events in a batch.
 
Inviting a user ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
  - Clients need to know *why* they are being invited (e.g. a ``reason`` key,
    just like for kicks/bans). However, this opens up a spam vector where any
    user can send any other user a string. Do we really want to do that?
  - It may be useful to send other state information such as the room name,
    topic, etc. How is this specified in this request? Does the inviter even
    specify this, or is it a room config option which fields are shared? This
    has a lot of parallels with the published room API which exposes some state
    events. How do we prevent spam attacks via the room name/topic?
  - The spam attack vector may be something we're just going to have to deal 
    with. Ultimately, we need to expose more data about the room. This data is
    going to be set by the client. Compromises like "just give the event type"
    don't really fix the problem "because.my.event.type.could.be.like.this".

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
 - Event type[s]
 - State key[s]
 - Room ID
 - Content[s]
Outputs:
 - None.
Notes:
 - A batching version of this API needs to be provided.
   
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
   
Patching power levels ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Room ID
 - Key to update
 - New value
Outputs:
 - None.
Notes:
 - This allows a single key on power levels to be updated e.g. specifying 
   ``kick`` as the key and ``60`` as the value to change the level required to
   kick someone.
 - The local HS will take the current ``m.room.power_levels`` event and set the
   new key before sending it to other HSes *in its full form*. This means HSes
   will not need to worry about partial power level events.
   
Knocking on a room ``[TODO]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If a room has the right ``join_rule`` e.g. ``knock``, then it should be able
to send a special knock event to ask to join the room.
   
Read-up-to markers ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
  - Convert to EDUs for markers with periodic PDUs to reduce event graph size?

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
 - These markers also allow unread message counts to be kept in sync for multiple
   devices.
 
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
 
Send a message ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~
Inputs:
 - Room ID
 - Message contents
 - Action ID (optional)
 - Whether the full event should be returned, or a compact version 
   (default=full)
Outputs:
 - The actual event sent incl content OR:
 - The extra keys added or keys modified e.g. 'content' from a policy server 
   (if compact=true)
What data flows does it address:
 - Chat Screen: Send a Message
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
Notes:
 - A batching version of this API needs to be provided.

Presence API ``[Draft]``
------------------------

.. FIXME
  this seems to be ignoring activity timers entirely, which were present on
  the planning etherpad and are present in the actual HTTP API. Needs attention.

The goals of presence are to:

- Let other users know if someone is "online".
- Let other users know if someone is likely to respond to any messages.
- Let other users know specific status information (e.g. "In a Meeting").

"Online" state can be detected by inspecting when the last time the client made
a request to the server. This could be any request, or a specific kind of 
request. For connection-orientated protocols, detecting "online" state can be 
determined by the state of this connection stream. For HTTP, this can be 
detected via requests to the event stream.

Online state is separate from letting other users know if someone is *likely to
respond* to messages. This introduces the concept of being "idle", which is
when the user has not done any "interaction" with the app for a while. The 
definition of "interaction" and "for a while" varies based on the app, so it is
up to the app to set when the user is idle.

Letting users know specific status information can be achieved via the same 
method as v1. Status information should be scoped per *user* and not device as 
determining a union algorithm between statuses is nonsensical. Passing status 
information per device to all other users just redirects the union problem to 
the client, which will commonly be presenting this information as an icon 
alongside the user.

When a client hits the event stream, the homeserver can treat the user as 
"online". This behaviour should be able to be overridden to avoid flicker 
during connection losses when the client is appear offline (e.g. device is
appear offline > goes into a tunnel > server times out > device regains 
connection and hits the event stream forcing the device online before the
"appear offline" state can be set). When the client has not hit the event 
stream for a certain period of time, the homeserver can treat the user as 
"offline". The user can also set a global *per-user* appear offline flag.

The user should also be able to set their presence state via a direct API, 
without having to hit the event stream. The homeserver will set a timer when 
the connection ends, after which it will set that device to offline.

As the idle flag and online state is determined per device, there needs to be a
union algorithm to merge these into a single state and flag per user, which will
be sent to other users. The algorithm is:

- If any device is online and not idle, the user is online.
- Else if all online devices are idle, the user is idle.
- Else the user is offline (no online devices).

Changing presence status:

Inputs:
 - User ID
 - Presence status (busy, do not disturb, in a meeting, etc)
Output:
 - None.
 
Setting presence state:

Inputs:
 - User ID
 - Device ID
 - Presence state (online|idle|offline)
Output:
 - None.
 
Setting global appear offline:

Inputs:
 - User ID
 - Should appear offline (boolean)
Output:
 - None.
 
Extra parameters associated with the event stream:

Inputs:
 - Presence state (online, idle, offline)
Notes:
 - Scoped per device just like the above API, e.g. from the access_token.


Typing API ``[Final]``
------------------------
.. NOTE::
 - Linking the termination of typing events to the message itself, so you don't 
   need to send two events and don't get flicker?

The typing API remains unchanged from v1.
 
Relates-to pagination API ``[Draft]``
-------------------------------------
See the "Relates to" section for more info.

Inputs:
 - Event ID
 - Chunk token
 - limit
Output:
 - A chunk of child events
 - A new chunk token for earlier child events.
 
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

When a client app is launched, the client needs to provide a capability set. The 
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
refused by the homeserver as it does not know the full capability set for that 
hash. The client will then have to upload the full capability set to the home 
server. The client will then be able to send the hash as normal.

When a client receives a hash, the client will either recognise the hash or 
will have to request the capability set from their homeserver:

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

Updates (Events) ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Events may update other events. This is represented by the ``updates`` key. This
is a key which contains the event ID for the event it relates to. Events that 
relate to other events are referred to as "Child Events". The event being 
related to is referred to as "Parent Events". Child events cannot stand alone as
a separate entity; they require the parent event in order to make sense.

Bundling updates
++++++++++++++++
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
   users on the same homeserver or via federation but *are* shared between 
   clients for the same user; useful for push notifications, read count markers,
   etc. This is done to avoid the ``n^2`` problem for sending receipts, where 
   the vast majority of traffic tends towards sending more receipts.
 - s/foo/bar/ style message edits
 
Clients *always* need to know how to apply the deltas because clients may 
receive the events separately down the event stream. Combining event updates 
server-side does not make client implementation simpler, as the client still 
needs to know how to combine the events.

Relates to (Events) ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
  - Should be able to specify more relationship info other than just the event
    type. Forcing that m.room.message A "relates_to" another m.room.message B 
    means that A is a threaded conversation reply to B is needlessly 
    restrictive. What if A and B relate to each other by some other metric 
    (e.g. they are part of a group rather than a thread? or we distinguish 
    mail-style threading from multithreaded-IM threading for the same set of 
    messages? etc)? E.g. ``"relates_to" : [["in_reply_to", "$event_id1"], 
    ["another_type_of_relation", "$event_id2"]]``

Events may be in response to other events, e.g. comments. This is represented 
by the ``relates_to`` key. This differs from the ``updates`` key as they *do 
not update the event itself*, and are *not required* in order to display the 
parent event. Crucially, the child events can be paginated, whereas ``updates`` 
child events cannot be paginated.

Bundling relations
++++++++++++++++++
Child events can be optionally bundled with the parent event, depending on your 
display mechanism. The number of child events which can be bundled should be 
limited to prevent events becoming too large. This limit should be set by the 
client. If the limit is exceeded, then the bundle should also include a 
chunk token so that the client can request more child events.

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
  and a chunk token to request earlier comments
  
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
- s/user_id/sender/g given that homeservers can send events, not just users.

Server-generated events ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Homeservers may want to send events to their local clients or to other home
servers e.g. for server status notifications.

These events look like regular events but have a server domain name as the
``sender`` and not a user ID. This can be easily detected by clients by the 
absence of a starting ``@``.

Different types of events (e.g. EDUs, room EDUs) are detected in the same way
as normal events (as proposed in the ``Events`` section of this document).


 
