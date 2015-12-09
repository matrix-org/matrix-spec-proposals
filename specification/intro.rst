.. contents:: Table of Contents
.. sectnum::

.. Note that this file is specifically unversioned because we don't want to
.. have to add Yet Another version number, and the commentary on what specs we
.. have should hopefully not get complex enough that we need to worry about
.. versioning it.

Introduction
------------
.. WARNING::
  The Matrix specification is still evolving: the APIs are not yet frozen
  and this document is in places a work in progress or stale. We have made every 
  effort to clearly flag areas which are still being finalised.
  We're publishing it at this point because it's complete enough to be more than
  useful and provide a canonical reference to how Matrix is evolving. Our end
  goal is to mirror WHATWG's `Living Standard   
  <http://wiki.whatwg.org/wiki/FAQ#What_does_.22Living_Standard.22_mean.3F>`_.

Matrix is a set of open APIs for open-federated Instant Messaging (IM), Voice
over IP (VoIP) and Internet of Things (IoT) communication, designed to create
and support a new global real-time communication ecosystem. The intention is to
provide an open decentralised pubsub layer for the internet for securely
persisting and publishing/subscribing JSON objects. This specification is the
ongoing result of standardising the APIs used by the various components of the
Matrix ecosystem to communicate with one another.

The principles that Matrix attempts to follow are:

- Pragmatic Web-friendly APIs (i.e. JSON over REST)
- Keep It Simple & Stupid

  + provide a simple architecture with minimal third-party dependencies.

- Fully open:

  + Fully open federation - anyone should be able to participate in the global
    Matrix network
  + Fully open standard - publicly documented standard with no IP or patent
    licensing encumbrances
  + Fully open source reference implementation - liberally-licensed example
    implementations with no IP or patent licensing encumbrances

- Empowering the end-user

  + The user should be able to choose the server and clients they use
  + The user should be control how private their communication is
  + The user should know precisely where their data is stored

- Fully decentralised - no single points of control over conversations or the
  network as a whole
- Learning from history to avoid repeating it

  + Trying to take the best aspects of XMPP, SIP, IRC, SMTP, IMAP and NNTP
    whilst trying to avoid their failings

The functionality that Matrix provides includes:

- Creation and management of fully distributed chat rooms with no
  single points of control or failure
- Eventually-consistent cryptographically secure synchronisation of room
  state across a global open network of federated servers and services
- Sending and receiving extensible messages in a room with (optional)
  end-to-end encryption
- Extensible user management (inviting, joining, leaving, kicking, banning)
  mediated by a power-level based user privilege system.
- Extensible room state management (room naming, aliasing, topics, bans)
- Extensible user profile management (avatars, display names, etc)
- Managing user accounts (registration, login, logout)
- Use of 3rd Party IDs (3PIDs) such as email addresses, phone numbers,
  Facebook accounts to authenticate, identify and discover users on Matrix.
- Trusted federation of Identity servers for:

  + Publishing user public keys for PKI
  + Mapping of 3PIDs to Matrix IDs

The end goal of Matrix is to be a ubiquitous messaging layer for synchronising
arbitrary data between sets of people, devices and services - be that for
instant messages, VoIP call setups, or any other objects that need to be
reliably and persistently pushed from A to B in an inter-operable and federated
manner.

Overview
--------

Architecture
~~~~~~~~~~~~

Matrix defines APIs for synchronising extensible JSON objects known as
"events" between compatible clients, servers and services. Clients are
typically messaging/VoIP applications or IoT devices/hubs and communicate by
synchronising communication history with their "homeserver" using the
"Client-Server API". Each homeserver stores the communication history and
account information for all of its clients, and shares data with the wider
Matrix ecosystem by synchronising communication history with other homeservers
and their clients.

Clients typically communicate with each other by emitting events in the
context of a virtual "room". Room data is replicated across *all of the
homeservers* whose users are participating in a given room. As such, *no
single homeserver has control or ownership over a given room*. Homeservers
model communication history as a partially ordered graph of events known as
the room's "event graph", which is synchronised with eventual consistency
between the participating servers using the "Server-Server API". This process
of synchronising shared conversation history between homeservers run by
different parties is called "Federation". Matrix optimises for the the
Availability and Partitioned properties of CAP theorem at
the expense of Consistency.

For example, for client A to send a message to client B, client A performs an
HTTP PUT of the required JSON event on its homeserver (HS) using the
client-server API. A's HS appends this event to its copy of the room's event
graph, signing the message in the context of the graph for integrity. A's HS
then replicates the message to B's HS by performing an HTTP PUT using the
server-server API. B's HS authenticates the request, validates the event's
signature, authorises the event's contents and then adds it to its copy of the
room's event graph. Client B then receives the message from his homeserver via
a long-lived GET request.

::

                         How data flows between clients
                         ==============================

       { Matrix client A }                             { Matrix client B }
           ^          |                                    ^          |
           |  events  |  Client-Server API                 |  events  |
           |          V                                    |          V
       +------------------+                            +------------------+
       |                  |---------( HTTPS )--------->|                  |
       |   homeserver    |                            |   homeserver    |
       |                  |<--------( HTTPS )----------|                  |
       +------------------+      Server-Server API     +------------------+
                              History Synchronisation
                                  (Federation)


Users
+++++

Each client is associated with a user account, which is identified in Matrix
using a unique "User ID". This ID is namespaced to the homeserver which
allocated the account and has the form::

  @localpart:domain

The ``localpart`` of a user ID may be a user name, or an opaque ID identifying
this user. The ``domain`` of a user ID is the domain of the homeserver.

.. TODO-spec
    - Need to specify precise grammar for Matrix IDs

Events
++++++

All data exchanged over Matrix is expressed as an "event". Typically each client
action (e.g. sending a message) correlates with exactly one event. Each event
has a ``type`` which is used to differentiate different kinds of data. ``type``
values MUST be uniquely globally namespaced following Java's `package naming
conventions`_, e.g.
``com.example.myapp.event``. The special top-level namespace ``m.`` is reserved
for events defined in the Matrix specification - for instance ``m.room.message``
is the event type for instant messages. Events are usually sent in the context
of a "Room".

.. _package naming conventions: https://en.wikipedia.org/wiki/Java_package#Package_naming_conventions

Event Graphs
++++++++++++

.. _sect:event-graph:

Events exchanged in the context of a room are stored in a directed acyclic graph
(DAG) called an "event graph". The partial ordering of this graph gives the
chronological ordering of events within the room. Each event in the graph has a
list of zero or more "parent" events, which refer to any preceding events
which have no chronological successor from the perspective of the homeserver
which created the event.

Typically an event has a single parent: the most recent message in the room at
the point it was sent. However, homeservers may legitimately race with each
other when sending messages, resulting in a single event having multiple
successors. The next event added to the graph thus will have multiple parents.
Every event graph has a single root event with no parent.

To order and ease chronological comparison between the events within the graph,
homeservers maintain a ``depth`` metadata field on each event. An event's
``depth`` is a positive integer that is strictly greater than the depths of any
of its parents. The root event should have a depth of 1. Thus if one event is
before another, then it must have a strictly smaller depth.

Room structure
++++++++++++++

A room is a conceptual place where users can send and receive events. Events are
sent to a room, and all participants in that room with sufficient access will
receive the event. Rooms are uniquely identified internally via "Room IDs",
which have the form::

  !opaque_id:domain

There is exactly one room ID for each room. Whilst the room ID does contain a
domain, it is simply for globally namespacing room IDs. The room does NOT
reside on the domain specified. Room IDs are not meant to be human readable.
They are case-sensitive. The following conceptual diagram shows an
``m.room.message`` event being sent to the room ``!qporfwt:matrix.org``::

       { @alice:matrix.org }                             { @bob:domain.com }
               |                                                 ^
               |                                                 |
      [HTTP POST]                                  [HTTP GET]
      Room ID: !qporfwt:matrix.org                 Room ID: !qporfwt:matrix.org
      Event type: m.room.message                   Event type: m.room.message
      Content: { JSON object }                     Content: { JSON object }
               |                                                 |
               V                                                 |
       +------------------+                          +------------------+
       |   homeserver    |                          |   homeserver    |
       |   matrix.org     |                          |   domain.com     |
       +------------------+                          +------------------+
               |                                                 ^
               |         [HTTP PUT]                              |
               |         Room ID: !qporfwt:matrix.org            |
               |         Event type: m.room.message              |
               |         Content: { JSON object }                |
               `-------> Pointer to the preceding message  ------`
                         PKI signature from matrix.org
                         Transaction-layer metadata
                         PKI Authorization header
                         
                     ...................................
                    |           Shared Data             |
                    | State:                            |
                    |   Room ID: !qporfwt:matrix.org    |
                    |   Servers: matrix.org, domain.com |
                    |   Members:                        |
                    |    - @alice:matrix.org            |
                    |    - @bob:domain.com              |
                    | Messages:                         |
                    |   - @alice:matrix.org             |
                    |     Content: { JSON object }      |
                    |...................................|

Federation maintains *shared data structures* per-room between multiple home
servers. The data is split into ``message events`` and ``state events``.

Message events: 
  These describe transient 'once-off' activity in a room such as an
  instant messages, VoIP call setups, file transfers, etc. They generally
  describe communication activity.

State events:
  These describe updates to a given piece of persistent information
  ('state') related to a room, such as the room's name, topic, membership,
  participating servers, etc. State is modelled as a lookup table of key/value
  pairs per room, with each key being a tuple of ``state_key`` and ``event type``.
  Each state event updates the value of a given key.

The state of the room at a given point is calculated by considering all events
preceding and including a given event in the graph. Where events describe the
same state, a merge conflict algorithm is applied. The state resolution
algorithm is transitive and does not depend on server state, as it must
consistently select the same event irrespective of the server or the order the
events were received in. Events are signed by the originating server (the
signature includes the parent relations, type, depth and payload hash) and are
pushed over federation to the participating servers in a room, currently using
full mesh topology. Servers may also request backfill of events over federation
from the other servers participating in a room.


Room Aliases
^^^^^^^^^^^^

Each room can also have multiple "Room Aliases", which look like::

  #room_alias:domain

.. TODO
  - Need to specify precise grammar for Room Aliases

A room alias "points" to a room ID and is the human-readable label by which
rooms are publicised and discovered.  The room ID the alias is pointing to can
be obtained by visiting the domain specified. Note that the mapping from a room
alias to a room ID is not fixed, and may change over time to point to a
different room ID. For this reason, Clients SHOULD resolve the room alias to a
room ID once and then use that ID on subsequent requests. Room aliases MUST NOT
exceed 255 bytes (including the domain).


When resolving a room alias the server will also respond with a list of servers
that are in the room that can be used to join via.

::

        HTTP GET
   #matrix:domain.com      !aaabaa:matrix.org
           |                    ^
           |                    |
    _______V____________________|____
   |          domain.com            |
   | Mappings:                      |
   | #matrix >> !aaabaa:matrix.org  |
   | #golf   >> !wfeiofh:sport.com  |
   | #bike   >> !4rguxf:matrix.org  |
   |________________________________|

Identity
++++++++

Users in Matrix are identified via their matrix user ID (MXID). However,
existing 3rd party ID namespaces can also be used in order to identify Matrix
users. A Matrix "Identity" describes both the user ID and any other existing IDs
from third party namespaces *linked* to their account.
Matrix users can *link* third-party IDs (3PIDs) such as email addresses, social
network accounts and phone numbers to their user ID. Linking 3PIDs creates a
mapping from a 3PID to a user ID. This mapping can then be used by Matrix
users in order to discover the MXIDs of their contacts.
In order to ensure that the mapping from 3PID to user ID is genuine, a globally
federated cluster of trusted "Identity Servers" (IS) are used to verify the 3PID
and persist and replicate the mappings.

Usage of an IS is not required in order for a client application to be part of
the Matrix ecosystem. However, without one clients will not be able to look up
user IDs using 3PIDs.


Profiles
++++++++

Users may publish arbitrary key/value data associated with their account - such
as a human readable display name, a profile photo URL, contact information
(email address, phone numbers, website URLs etc).

.. TODO
  Actually specify the different types of data - e.g. what format are display
  names allowed to be?

Private User Data
+++++++++++++++++

Users may also store arbitrary private key/value data in their account - such as
client preferences, or server configuration settings which lack any other
dedicated API.  The API is symmetrical to managing Profile data.

.. TODO
  Would it really be overengineered to use the same API for both profile &
  private user data, but with different ACLs?

