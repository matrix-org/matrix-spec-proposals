Matrix Specification
====================

WARNING
=======

.. WARNING::
  The Matrix specification is still very much evolving: the API is not yet frozen
  and this document is in places incomplete, stale, and may contain security
  issues. Needless to say, we have made every effort to highlight the problem
  areas that we're aware of.

  We're publishing it at this point because it's complete enough to be more than
  useful and provide a canonical reference to how Matrix is evolving. Our end
  goal is to mirror WHATWG's `Living Standard <http://wiki.whatwg.org/wiki/FAQ#What_does_.22Living_Standard.22_mean.3F>`_
  approach except right now Matrix is more in the process of being born than actually being
  living!

Table of Contents
=================

.. contents:: Table of Contents
.. sectnum::

Matrix is a new set of open APIs for open-federated Instant Messaging and VoIP
functionality, designed to create and support a new global real-time
communication ecosystem on the internet. This specification is the ongoing
result of standardising the APIs used by the various components of the Matrix
ecosystem to communicate with one another.

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
- Extensible user profile management (avatars, displaynames, etc)
- Managing user accounts (registration, login, logout)
- Use of 3rd Party IDs (3PIDs) such as email addresses, phone numbers,
  Facebook accounts to authenticate, identify and discover users on Matrix.
- Trusted federation of Identity servers for:

  + Publishing user public keys for PKI
  + Mapping of 3PIDs to Matrix IDs

The end goal of Matrix is to be a ubiquitous messaging layer for synchronising
arbitrary data between sets of people, devices and services - be that for
instant messages, VoIP call setups, or any other objects that need to be
reliably and persistently pushed from A to B in an interoperable and federated
manner.

Basis
=====

Architecture
------------

Clients transmit data to other clients through home servers (HSes). Clients do
not communicate with each other directly.

::

                         How data flows between clients
                         ==============================

       { Matrix client A }                             { Matrix client B }
           ^          |                                    ^          |
           |  events  |                                    |  events  |
           |          V                                    |          V
       +------------------+                            +------------------+
       |                  |---------( HTTP )---------->|                  |
       |   Home Server    |                            |   Home Server    |
       |                  |<--------( HTTP )-----------|                  |
       +------------------+        Federation          +------------------+

A "Client" typically represents a human using a web application or mobile app.
Clients use the "Client-to-Server" (C-S) API to communicate with their home
server, which stores their profile data and their record of the conversations
in which they participate. Each client is associated with a user account (and
may optionally support multiple user accounts). A user account is represented
by a unique "User ID". This ID is namespaced to the home server which allocated
the account and looks like::

  @localpart:domain

The ``localpart`` of a user ID may be a user name, or an opaque ID identifying
this user. They are case-insensitive.

.. TODO-spec
    - Need to specify precise grammar for Matrix IDs

A "Home Server" is a server which provides C-S APIs and has the ability to
federate with other HSes.  It is typically responsible for multiple clients.
"Federation" is the term used to describe the sharing of data between two or
more home servers.

Data in Matrix is encapsulated in an "event". An event is an action within the
system. Typically each action (e.g. sending a message) correlates with exactly
one event. Each event has a ``type`` which is used to differentiate different
kinds of data. ``type`` values MUST be uniquely globally namespaced following
Java's `package naming conventions
<http://docs.oracle.com/javase/specs/jls/se5.0/html/packages.html#7.7>`, e.g.
``com.example.myapp.event``. The special top-level namespace ``m.`` is reserved
for events defined in the Matrix specification. Events are usually sent in the
context of a "Room".

Room structure
~~~~~~~~~~~~~~

A room is a conceptual place where users can send and receive events. Rooms can
be created, joined and left. Events are sent to a room, and all participants in
that room with sufficient access will receive the event. Rooms are uniquely
identified internally via a "Room ID", which look like::

  !opaque_id:domain

There is exactly one room ID for each room. Whilst the room ID does contain a
domain, it is simply for globally namespacing room IDs. The room does NOT
reside on the domain specified. Room IDs are not meant to be human readable.
They ARE case-sensitive.

The following diagram shows an ``m.room.message`` event being sent in the room
``!qporfwt:matrix.org``::

       { @alice:matrix.org }                             { @bob:domain.com }
               |                                                 ^
               |                                                 |
      Room ID: !qporfwt:matrix.org                 Room ID: !qporfwt:matrix.org
      Event type: m.room.message                   Event type: m.room.message
      Content: { JSON object }                     Content: { JSON object }
               |                                                 |
               V                                                 |
       +------------------+                          +------------------+
       |   Home Server    |                          |   Home Server    |
       |   matrix.org     |<-------Federation------->|   domain.com     |
       +------------------+                          +------------------+
                |       .................................        |
                |______|           Shared State          |_______|
                       | Room ID: !qporfwt:matrix.org    |
                       | Servers: matrix.org, domain.com |
                       | Members:                        |
                       |  - @alice:matrix.org            |
                       |  - @bob:domain.com              |
                       |.................................|

Federation maintains shared state between multiple home servers, such that when
an event is sent to a room, the home server knows where to forward the event on
to, and how to process the event. State is scoped to a single room, and
federation ensures that all home servers have the information they need, even
if that means the home server has to request more information from another home
server before processing the event.

Room Aliases
~~~~~~~~~~~~

Each room can also have multiple "Room Aliases", which looks like::

  #room_alias:domain

.. TODO
  - Need to specify precise grammar for Room Aliases

A room alias "points" to a room ID and is the human-readable label by which
rooms are publicised and discovered.  The room ID the alias is pointing to can
be obtained by visiting the domain specified. They are case-insensitive. Note
that the mapping from a room alias to a room ID is not fixed, and may change
over time to point to a different room ID. For this reason, Clients SHOULD
resolve the room alias to a room ID once and then use that ID on subsequent
requests.

When resolving a room alias the server will also respond with a list of servers
that are in the room that can be used to join via.

::

          GET
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
~~~~~~~~

Users in Matrix are identified via their user ID. However, existing ID
namespaces can also be used in order to identify Matrix users. A Matrix
"Identity" describes both the user ID and any other existing IDs from third
party namespaces *linked* to their account.

Matrix users can *link* third-party IDs (3PIDs) such as email addresses, social
network accounts and phone numbers to their user ID. Linking 3PIDs creates a
mapping from a 3PID to a user ID. This mapping can then be used by other Matrix
users in order to discover other users, according to a strict set of privacy
permissions.

In order to ensure that the mapping from 3PID to user ID is genuine, a globally
federated cluster of trusted "Identity Servers" (IS) are used to perform
authentication of the 3PID.  Identity servers are also used to preserve the
mapping indefinitely, by replicating the mappings across multiple ISes.

Usage of an IS is not required in order for a client application to be part of
the Matrix ecosystem. However, without one clients will not be able to look up
user IDs using 3PIDs.

Presence
~~~~~~~~

Each user has the concept of presence information. This encodes the
"availability" of that user, suitable for display on other user's clients. This
is transmitted as an ``m.presence`` event and is one of the few events which
are sent *outside the context of a room*. The basic piece of presence
information is represented by the ``presence`` key, which is an enum of one of
the following:

  - ``online`` : The default state when the user is connected to an event
    stream.
  - ``unavailable`` : The user is not reachable at this time.
  - ``offline`` : The user is not connected to an event stream.
  - ``free_for_chat`` : The user is generally willing to receive messages
    moreso than default.
  - ``hidden`` : Behaves as offline, but allows the user to see the client
    state anyway and generally interact with client features. (Not yet
    implemented in synapse).

This basic ``presence`` field applies to the user as a whole, regardless of how
many client devices they have connected. The home server should synchronise
this status choice among multiple devices to ensure the user gets a consistent
experience.

In addition, the server maintains a timestamp of the last time it saw an active
action from the user; either sending a message to a room, or changing presence
state from a lower to a higher level of availability (thus: changing state from
``unavailable`` to ``online`` will count as an action for being active, whereas
in the other direction will not). This timestamp is presented via a key called
``last_active_ago``, which gives the relative number of miliseconds since the
message is generated/emitted, that the user was last seen active.

Home servers can also use the user's choice of presence state as a signal for
how to handle new private one-to-one chat message requests. For example, it
might decide:

  - ``free_for_chat`` : accept anything
  - ``online`` : accept from anyone in my address book list
  - ``busy`` : accept from anyone in this "important people" group in my
    address book list

Presence List
+++++++++++++
Each user's home server stores a "presence list" for that user. This stores a
list of other user IDs the user has chosen to add to it. To be added to this
list, the user being added must receive permission from the list owner. Once
granted, both user's HSes store this information. Since such subscriptions
are likely to be bidirectional, HSes may wish to automatically accept requests
when a reverse subscription already exists.

As a convenience, presence lists should support the ability to collect users
into groups, which could allow things like inviting the entire group to a new
("ad-hoc") chat room, or easy interaction with the profile information ACL
implementation of the HS.

Presence and Permissions
++++++++++++++++++++++++
For a viewing user to be allowed to see the presence information of a target
user, either:

 - The target user has allowed the viewing user to add them to their presence
   list, or
 - The two users share at least one room in common

In the latter case, this allows for clients to display some minimal sense of
presence information in a user list for a room.

Idle Time
+++++++++
.. NOTE::
  Needs specificity & detail.  Not present in Synapse.

As well as the basic ``presence`` field, the presence information can also show
a sense of an "idle timer". This should be maintained individually by the
user's clients, and the home server can take the highest reported time as that
to report. When a user is offline, the home server can still report when the
user was last seen online.

Device Type
+++++++++++
.. NOTE::
  Needs specificity & detail.  Not present in Synapse.

Client devices that may limit the user experience somewhat (such as "mobile"
devices with limited ability to type on a real keyboard or read large amounts of
text) should report this to the home server, as this is also useful information
to report as "presence" if the user cannot be expected to provide a good typed
response to messages.



Profiles
~~~~~~~~

.. TODO-spec
  - Metadata extensibility

Internally within Matrix users are referred to by their user ID, which is
typically a compact unique identifier. Profiles grant users the ability to see
human-readable names for other users that are in some way meaningful to them.
Additionally, profiles can publish additional information, such as the user's
age or location.

A Profile consists of a display name, an avatar picture, and a set of other
metadata fields that the user may wish to publish (email address, phone
numbers, website URLs, etc...). This specification puts no requirements on the
display name other than it being a valid unicode string. Avatar images are not
stored directly; instead the home server stores an ``http``-scheme URL where
clients may fetch it from.

Model
-----

Overview
~~~~~~~~

Matrix is used to reliably distribute data between sets of `users`.

Users are associated with one of many matrix `servers`. These distribute,
receive and store data on behalf of its registered users. Servers can be run on
any host accessible from the internet.

When a user wishes to send data to users on different servers the local server
will distribute the data to each remote server. These will in turn distribute
to their local users involved.

A user sends and receives data using one or more authenticated `clients`
connected to his server. Clients may persist data locally or request it when
required from the server.

Events
~~~~~~
An event is a collection of data (the `payload`) and metadata to be distributed
across servers and is the primary data unit in Matrix.  Events are extensible
so that clients and servers can add extra arbitrary fields to both the payload
or metadata.

Events are distributed to interested servers upon creation. Historical events
may be requested from servers; servers are not required to produce all
or any events requested.

All events have a metadata `type` field that is used by client and servers to
determine how the payload should be processed and used. There are a number of
types reserved by the protocol for particular uses, but otherwise types may be
defined by applications, clients or servers for their own purposes.

.. TODO : Namespacing of new types.

Graph
+++++
Each event has a list of zero or more `parent` events. These relations form
directed acyclic graphs of events called `event graphs`. Every event graph has
a single root event, and each event graph forms the basis of the history of a
matrix room.

Event graphs give a partial ordering of events, i.e. given two events one may
be considered to have come before the other if one is an ancestor of the other.
Since two events may be on separate branches, not all events can be compared in
this manner.

Every event has a metadata `depth` field that is a positive integer that is
strictly greater than the depths of any of its parents. The root event should
have a depth of 1.

[Note: if one event is before another, then it must have a strictly smaller
depth]

Integrity
+++++++++

.. TODO: Specify the precise subset of essential fields

Portions of events will be signed by one or more servers or clients. The parent
relations, type, depth and payload (as well as other metadata fields that will
be specified) must be signed by the originating server. [Note: Thus, once an
event is distributed and referenced by later events, they effectively become
immutable].

The payload may also be encrypted by clients, except in the case where the
payload needs to be interpreted by the servers. A list of event types that
cannot have an encrypted payload are given later.


State
~~~~~
Event graphs may have meta information associated with them, called `state`.
State can be updated over time by servers or clients, subject to
authorisation.

The state of a graph is split into `sections` that can be atomically updated
independently of each other.

State is stored within the graph itself, and can be computed by looking at the
graph in its entirety. We define the state at a given event to be the state of
the sub graph of all events "before" and including that event.

Some sections of the state may determine behaviour of the protocol, including
authorisation and distribution. These sections must not be encrypted.

State Events
++++++++++++
`State events` are events that update a section of the state of a graph. These
state events hold all the same properties of events, and are part of the event
graph. The payload of the event is the replacement value for the particular
section of state being updated.

State events must also include a `state_key` metadata field. The pair of fields
type and state_key uniquely defines the section of state that is to be updated.

State Resolution
++++++++++++++++
A given state section may have multiple state events associated with it in a
given graph. A consistent method of selecting which state event takes
precedence is therefore required.

This is done by taking the latest state events, i.e. the set of events that are
either incomparable or after every other event in the graph. A state resolution
algorithm is then applied to this set to select the single event that takes
precedence.

The state resolution algorithm must be transitive and not depend on server
state, as it must consistently select the same event irrespective of the server
or the order the events were received in.

State Dictionary
++++++++++++++++
The state dictionary is the mapping from sections of state to the state events
which set the section to its current value.  The state dictionary, like the
state itself, depends on the events currently in the graph and so is updated
with each new event received.

Since the sections of the state are defined by the pair of strings from the
type and state_key of the events that update them, the state dictionary can be
defined as a mapping from the pair (type, state_key) to a state event with
those values in the graph.

Deleting State
++++++++++++++
State sections may also be deleted, i.e. removed from the state dictionary. The
state events will still be present in the event graph.

This is done by sending a special state event indicating that the given entry
should be removed from the dictionary. These events follow the same rules for
state resolution, with the added requirement that it loses all conflicts.
[Note: This is required to make the algorithm transitive.]


API Standards
-------------

The mandatory baseline for communication in Matrix is exchanging JSON objects
over RESTful HTTP APIs. HTTPS is mandated as the baseline for server-server
(federation) communication.  HTTPS is recommended for client-server
communication, although HTTP may be supported as a fallback to support basic
HTTP clients. More efficient optional transports for client-server
communication will in future be supported as optional extensions - e.g. a
packed binary encoding over stream-cipher encrypted TCP socket for
low-bandwidth/low-roundtrip mobile usage.

.. TODO
  We need to specify capability negotiation for extensible transports

For the default HTTP transport, all API calls use a Content-Type of
``application/json``.  In addition, all strings MUST be encoded as UTF-8.

Clients are authenticated using opaque ``access_token`` strings (see
`Registration and Login`_ for details), passed as a query string parameter on
all requests.

.. TODO
  Need to specify any HMAC or access_token lifetime/ratcheting tricks

Any errors which occur on the Matrix API level MUST return a "standard error
response". This is a JSON object which looks like::

  {
    "errcode": "<error code>",
    "error": "<error message>"
  }

The ``error`` string will be a human-readable error message, usually a sentence
explaining what went wrong. The ``errcode`` string will be a unique string
which can be used to handle an error message e.g. ``M_FORBIDDEN``. These error
codes should have their namespace first in ALL CAPS, followed by a single _.
For example, if there was a custom namespace ``com.mydomain.here``, and a
``FORBIDDEN`` code, the error code should look like
``COM.MYDOMAIN.HERE_FORBIDDEN``. There may be additional keys depending on the
error, but the keys ``error`` and ``errcode`` MUST always be present.

Some standard error codes are below:

:``M_FORBIDDEN``:
  Forbidden access, e.g. joining a room without permission, failed login.

:``M_UNKNOWN_TOKEN``:
  The access token specified was not recognised.

:``M_BAD_JSON``:
  Request contained valid JSON, but it was malformed in some way, e.g. missing
  required keys, invalid values for keys.

:``M_NOT_JSON``:
  Request did not contain valid JSON.

:``M_NOT_FOUND``:
  No resource was found for this request.

:``M_LIMIT_EXCEEDED``:
  Too many requests have been sent in a short period of time. Wait a while then
  try again.

Some requests have unique error codes:

:``M_USER_IN_USE``:
  Encountered when trying to register a user ID which has been taken.

:``M_ROOM_IN_USE``:
  Encountered when trying to create a room which has been taken.

:``M_BAD_PAGINATION``:
  Encountered when specifying bad pagination query parameters.

:``M_LOGIN_EMAIL_URL_NOT_YET``:
  Encountered when polling for an email link which has not been clicked yet.

The C-S API typically uses ``HTTP POST`` to submit requests. This means these
requests are not idempotent. The C-S API also allows ``HTTP PUT`` to make
requests idempotent. In order to use a ``PUT``, paths should be suffixed with
``/{txnId}``. ``{txnId}`` is a unique client-generated transaction ID which
identifies the request, and is scoped to a given Client (identified by that
client's ``access_token``). Crucially, it **only** serves to identify new
requests from retransmits. After the request has finished, the ``{txnId}``
value should be changed (how is not specified; a monotonically increasing
integer is recommended). It is preferable to use ``HTTP PUT`` to make sure
requests to send messages do not get sent more than once should clients need to
retransmit requests.

Valid requests look like::

    POST /some/path/here?access_token=secret
    {
      "key": "This is a post."
    }

    PUT /some/path/here/11?access_token=secret
    {
      "key": "This is a put with a txnId of 11."
    }

In contrast, these are invalid requests::

    POST /some/path/here/11?access_token=secret
    {
      "key": "This is a post, but it has a txnId."
    }

    PUT /some/path/here?access_token=secret
    {
      "key": "This is a put but it is missing a txnId."
    }

Glossary
--------

Backfilling:
  The process of synchronising historic state from one home server to another,
  to backfill the event storage so that scrollback can be presented to the
  client(s). Not to be confused with pagination.

Context:
  A single human-level entity of interest (currently, a chat room)

EDU (Ephemeral Data Unit):
  A message that relates directly to a given pair of home servers that are
  exchanging it. EDUs are short-lived messages that related only to one single
  pair of servers; they are not persisted for a long time and are not forwarded
  on to other servers. Because of this, they have no internal ID nor previous
  EDUs reference chain.

Event:
  A record of activity that records a single thing that happened on to a context
  (currently, a chat room). These are the "chat messages" that Synapse makes
  available.

PDU (Persistent Data Unit):
  A message that relates to a single context, irrespective of the server that
  is communicating it. PDUs either encode a single Event, or a single State
  change. A PDU is referred to by its PDU ID; the pair of its origin server
  and local reference from that server.

PDU ID:
  The pair of PDU Origin and PDU Reference, that together globally uniquely
  refers to a specific PDU.

PDU Origin:
  The name of the origin server that generated a given PDU. This may not be the
  server from which it has been received, due to the way they are copied around
  from server to server. The origin always records the original server that
  created it.

PDU Reference:
  A local ID used to refer to a specific PDU from a given origin server. These
  references are opaque at the protocol level, but may optionally have some
  structured meaning within a given origin server or implementation.

Presence:
  The concept of whether a user is currently online, how available they declare
  they are, and so on. See also: doc/model/presence

Profile:
  A set of metadata about a user, such as a display name, provided for the
  benefit of other users. See also: doc/model/profiles

Room ID:
  An opaque string (of as-yet undecided format) that identifies a particular
  room and used in PDUs referring to it.

Room Alias:
  A human-readable string of the form #name:some.domain that users can use as a
  pointer to identify a room; a Directory Server will map this to its Room ID

State:
  A set of metadata maintained about a Context, which is replicated among the
  servers in addition to the history of Events.

User ID:
  A string of the form @localpart:domain.name that identifies a user for
  wire-protocol purposes. The localpart is meaningless outside of a particular
  home server. This takes a human-readable form that end-users can use directly
  if they so wish, avoiding the 3PIDs.

Transaction:
  A message which relates to the communication between a given pair of servers.
  A transaction contains possibly-empty lists of PDUs and EDUs.

.. TODO
  This glossary contradicts the terms used above - especially on State Events v. "State"
  and Non-State Events v. "Events".  We need better consistent names.

