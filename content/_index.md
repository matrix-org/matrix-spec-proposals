---
title: "Matrix Specification"
type: docs
weight: 10
---

Matrix defines a set of open APIs for decentralised communication,
suitable for securely publishing, persisting and subscribing to data
over a global open federation of servers with no single point of
control. Uses include Instant Messaging (IM), Voice over IP (VoIP)
signalling, Internet of Things (IoT) communication, and bridging
together existing communication silos - providing the basis of a new
open real-time communication ecosystem.

To propose a change to the Matrix Spec, see the explanations at
[Proposals for Spec Changes to Matrix](/proposals).

## Matrix APIs

The specification consists of the following parts:

* [Client-Server API](/client-server-api)
* [Server-Server API](/server-server-api)
* [Application Service API](/application-service-api)
* [Identity Service API](/identity-service-api)
* [Push Gateway API](/push-gateway-api)
* [Room Versions](/rooms)
* [Appendices](/appendices)

Additionally, this introduction page contains the key baseline
information required to understand the specific APIs, including the
section the [overall architecture](#architecture).

The [Matrix Client-Server API Swagger
Viewer](https://matrix.org/docs/api/client-server/) is useful for
browsing the Client-Server API.

## Introduction to the Matrix APIs

Matrix is a set of open APIs for open-federated Instant Messaging (IM),
Voice over IP (VoIP) and Internet of Things (IoT) communication,
designed to create and support a new global real-time communication
ecosystem. The intention is to provide an open decentralised pubsub
layer for the internet for securely persisting and
publishing/subscribing JSON objects. This specification is the ongoing
result of standardising the APIs used by the various components of the
Matrix ecosystem to communicate with one another.

The principles that Matrix attempts to follow are:

-   Pragmatic Web-friendly APIs (i.e. JSON over REST)
-   Keep It Simple & Stupid
    -   provide a simple architecture with minimal third-party
        dependencies.
-   Fully open:
    -   Fully open federation - anyone should be able to participate in
        the global Matrix network
    -   Fully open standard - publicly documented standard with no IP or
        patent licensing encumbrances
    -   Fully open source reference implementation - liberally-licensed
        example implementations with no IP or patent licensing
        encumbrances
-   Empowering the end-user
    -   The user should be able to choose the server and clients they
        use
    -   The user should be able to control how private their
        communication is
    -   The user should know precisely where their data is stored
-   Fully decentralised - no single points of control over conversations
    or the network as a whole
-   Learning from history to avoid repeating it
    -   Trying to take the best aspects of XMPP, SIP, IRC, SMTP, IMAP
        and NNTP whilst trying to avoid their failings

The functionality that Matrix provides includes:

-   Creation and management of fully distributed chat rooms with no
    single points of control or failure
-   Eventually-consistent cryptographically secure synchronisation of
    room state across a global open network of federated servers and
    services
-   Sending and receiving extensible messages in a room with (optional)
    end-to-end encryption
-   Extensible user management (inviting, joining, leaving, kicking,
    banning) mediated by a power-level based user privilege system.
-   Extensible room state management (room naming, aliasing, topics,
    bans)
-   Extensible user profile management (avatars, display names, etc)
-   Managing user accounts (registration, login, logout)
-   Use of 3rd Party IDs (3PIDs) such as email addresses, phone numbers,
    Facebook accounts to authenticate, identify and discover users on
    Matrix.
-   Trusted federation of identity servers for:
    -   Publishing user public keys for PKI
    -   Mapping of 3PIDs to Matrix IDs

The end goal of Matrix is to be a ubiquitous messaging layer for
synchronising arbitrary data between sets of people, devices and
services - be that for instant messages, VoIP call setups, or any other
objects that need to be reliably and persistently pushed from A to B in
an interoperable and federated manner.

### Spec Change Proposals

To propose a change to the Matrix Spec, see the explanations at
[Proposals for Spec Changes to Matrix](/proposals).

## Architecture

Matrix defines APIs for synchronising extensible JSON objects known as
"events" between compatible clients, servers and services. Clients are
typically messaging/VoIP applications or IoT devices/hubs and
communicate by synchronising communication history with their
"homeserver" using the "Client-Server API". Each homeserver stores the
communication history and account information for all of its clients,
and shares data with the wider Matrix ecosystem by synchronising
communication history with other homeservers and their clients.

Clients typically communicate with each other by emitting events in the
context of a virtual "room". Room data is replicated across *all of the
homeservers* whose users are participating in a given room. As such, *no
single homeserver has control or ownership over a given room*.
Homeservers model communication history as a partially ordered graph of
events known as the room's "event graph", which is synchronised with
eventual consistency between the participating servers using the
"Server-Server API". This process of synchronising shared conversation
history between homeservers run by different parties is called
"Federation". Matrix optimises for the Availability and Partitioned
properties of CAP theorem at the expense of Consistency.

For example, for client A to send a message to client B, client A
performs an HTTP PUT of the required JSON event on its homeserver (HS)
using the client-server API. A's HS appends this event to its copy of
the room's event graph, signing the message in the context of the graph
for integrity. A's HS then replicates the message to B's HS by
performing an HTTP PUT using the server-server API. B's HS authenticates
the request, validates the event's signature, authorises the event's
contents and then adds it to its copy of the room's event graph. Client
B then receives the message from his homeserver via a long-lived GET
request.

How data flows between clients:

```
    { Matrix client A }                             { Matrix client B }
        ^          |                                    ^          |
        |  events  |  Client-Server API                 |  events  |
        |          V                                    |          V
    +------------------+                            +------------------+
    |                  |---------( HTTPS )--------->|                  |
    |   homeserver     |                            |   homeserver     |
    |                  |<--------( HTTPS )----------|                  |
    +------------------+      Server-Server API     +------------------+
                          History Synchronisation
                              (Federation)
```

### Users

Each client is associated with a user account, which is identified in
Matrix using a unique "user ID". This ID is namespaced to the homeserver
which allocated the account and has the form:

    @localpart:domain

See ['Identifier Grammar' in the
appendices](/appendices#identifier-grammar) for full details of the
structure of user IDs.

### Devices

The Matrix specification has a particular meaning for the term "device".
As a user, I might have several devices: a desktop client, some web
browsers, an Android device, an iPhone, etc. They broadly relate to a
real device in the physical world, but you might have several browsers
on a physical device, or several Matrix client applications on a mobile
device, each of which would be its own device.

Devices are used primarily to manage the keys used for end-to-end
encryption (each device gets its own copy of the decryption keys), but
they also help users manage their access - for instance, by revoking
access to particular devices.

When a user first uses a client, it registers itself as a new device.
The longevity of devices might depend on the type of client. A web
client will probably drop all of its state on logout, and create a new
device every time you log in, to ensure that cryptography keys are not
leaked to a new user. In a mobile client, it might be acceptable to
reuse the device if a login session expires, provided the user is the
same.

Devices are identified by a `device_id`, which is unique within the
scope of a given user.

A user may assign a human-readable display name to a device, to help
them manage their devices.

### Events

All data exchanged over Matrix is expressed as an "event". Typically
each client action (e.g. sending a message) correlates with exactly one
event. Each event has a `type` which is used to differentiate different
kinds of data. `type` values MUST be uniquely globally namespaced
following Java's [package naming
conventions](https://en.wikipedia.org/wiki/Java_package#Package_naming_conventions),
e.g. `com.example.myapp.event`. The special top-level namespace `m.` is
reserved for events defined in the Matrix specification - for instance
`m.room.message` is the event type for instant messages. Events are
usually sent in the context of a "Room".

{{% boxes/warning %}}
Event bodies are considered untrusted data. This means that any application using
Matrix must validate that the event body is of the expected shape/schema
before using the contents verbatim.

**It is not safe to assume that an event body will have all the expected
fields of the expected types.**

See [MSC2801](https://github.com/matrix-org/matrix-doc/pull/2801) for more
detail on why this assumption is unsafe.
{{% /boxes/warning %}}

### Event Graphs

Events exchanged in the context of a room are stored in a directed
acyclic graph (DAG) called an "event graph". The partial ordering of
this graph gives the chronological ordering of events within the room.
Each event in the graph has a list of zero or more "parent" events,
which refer to any preceding events which have no chronological
successor from the perspective of the homeserver which created the
event.

Typically an event has a single parent: the most recent message in the
room at the point it was sent. However, homeservers may legitimately
race with each other when sending messages, resulting in a single event
having multiple successors. The next event added to the graph thus will
have multiple parents. Every event graph has a single root event with no
parent.

To order and ease chronological comparison between the events within the
graph, homeservers maintain a `depth` metadata field on each event. An
event's `depth` is a positive integer that is strictly greater than the
depths of any of its parents. The root event should have a depth of 1.
Thus if one event is before another, then it must have a strictly
smaller depth.

### Room structure

A room is a conceptual place where users can send and receive events.
Events are sent to a room, and all participants in that room with
sufficient access will receive the event. Rooms are uniquely identified
internally via "Room IDs", which have the form:

    !opaque_id:domain

There is exactly one room ID for each room. Whilst the room ID does
contain a domain, it is simply for globally namespacing room IDs. The
room does NOT reside on the domain specified.

See ['Identifier Grammar' in the
appendices](/appendices#identifier-grammar) for full details of the
structure of a room ID.

The following conceptual diagram shows an `m.room.message` event being
sent to the room `!qporfwt:matrix.org`:

    { @alice:matrix.org }                             { @bob:example.org }
            |                                                 ^
            |                                                 |
    [HTTP POST]                                  [HTTP GET]
    Room ID: !qporfwt:matrix.org                 Room ID: !qporfwt:matrix.org
    Event type: m.room.message                   Event type: m.room.message
    Content: { JSON object }                     Content: { JSON object }
            |                                                 |
            V                                                 |
    +------------------+                          +------------------+
    |   homeserver     |                          |   homeserver     |
    |   matrix.org     |                          |   example.org    |
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

                  ....................................
                 |           Shared Data              |
                 | State:                             |
                 |   Room ID: !qporfwt:matrix.org     |
                 |   Servers: matrix.org, example.org |
                 |   Members:                         |
                 |    - @alice:matrix.org             |
                 |    - @bob:example.org              |
                 | Messages:                          |
                 |   - @alice:matrix.org              |
                 |     Content: { JSON object }       |
                 |....................................|

Federation maintains *shared data structures* per-room between multiple
homeservers. The data is split into `message events` and `state events`.

Message events:
These describe transient 'one-off' activity in a room such as
instant messages, VoIP call setups, file transfers, etc. They generally
describe communication activity.

State events:
These describe updates to a given piece of persistent information
('state') related to a room, such as the room's name, topic, membership,
participating servers, etc. State is modelled as a lookup table of
key/value pairs per room, with each key being a tuple of `state_key` and
`event type`. Each state event updates the value of a given key.

The state of the room at a given point is calculated by considering all
events preceding and including a given event in the graph. Where events
describe the same state, a merge conflict algorithm is applied. The
state resolution algorithm is transitive and does not depend on server
state, as it must consistently select the same event irrespective of the
server or the order the events were received in. Events are signed by
the originating server (the signature includes the parent relations,
type, depth and payload hash) and are pushed over federation to the
participating servers in a room, currently using full mesh topology.
Servers may also request backfill of events over federation from the
other servers participating in a room.

{{% boxes/note %}}
Events are not limited to the types defined in this specification. New
or custom event types can be created on a whim using the Java package
naming convention. For example, a `com.example.game.score` event can be
sent by clients and other clients would receive it through Matrix,
assuming the client has access to the `com.example` namespace.
{{% /boxes/note %}}

#### Room Aliases

Each room can also have multiple "Room Aliases", which look like:

    #room_alias:domain

See ['Identifier Grammar' in the
appendices](/appendices#identifier-grammar) for full details of the
structure of a room alias.

A room alias "points" to a room ID and is the human-readable label by
which rooms are publicised and discovered. The room ID the alias is
pointing to can be obtained by visiting the domain specified. Note that
the mapping from a room alias to a room ID is not fixed, and may change
over time to point to a different room ID. For this reason, Clients
SHOULD resolve the room alias to a room ID once and then use that ID on
subsequent requests.

When resolving a room alias the server will also respond with a list of
servers that are in the room that can be used to join via.

    HTTP GET
    #matrix:example.org      !aaabaa:matrix.org
       |                    ^
       |                    |
    _______V____________________|____
    |          example.org           |
    | Mappings:                      |
    | #matrix >> !aaabaa:matrix.org  |
    | #golf   >> !wfeiofh:sport.com  |
    | #bike   >> !4rguxf:matrix.org  |
    |________________________________|

### Identity

Users in Matrix are identified via their Matrix user ID. However,
existing 3rd party ID namespaces can also be used in order to identify
Matrix users. A Matrix "Identity" describes both the user ID and any
other existing IDs from third party namespaces *linked* to their
account. Matrix users can *link* third-party IDs (3PIDs) such as email
addresses, social network accounts and phone numbers to their user ID.
Linking 3PIDs creates a mapping from a 3PID to a user ID. This mapping
can then be used by Matrix users in order to discover the user IDs of
their contacts. In order to ensure that the mapping from 3PID to user ID
is genuine, a globally federated cluster of trusted "identity servers"
(IS) are used to verify the 3PID and persist and replicate the mappings.

Usage of an IS is not required in order for a client application to be
part of the Matrix ecosystem. However, without one clients will not be
able to look up user IDs using 3PIDs.

### Profiles

Users may publish arbitrary key/value data associated with their account
- such as a human-readable display name, a profile photo URL, contact
information (email address, phone numbers, website URLs etc).

### Private User Data

Users may also store arbitrary private key/value data in their account -
such as client preferences, or server configuration settings which lack
any other dedicated API. The API is symmetrical to managing Profile
data.

## Common concepts

Various things are common throughout all of the Matrix APIs. They are
documented here.

### Namespacing

Namespacing helps prevent conflicts between multiple applications and
the specification itself. Where namespacing is used, `m.` prefixes are
used by the specification to indicate that the field is controlled by
the specification. Custom or non-specified namespaces used in the wild
MUST use the Java package naming convention to prevent conflicts.

As an example, event types defined in the specification are namespaced
under the special `m.` prefix, however any client can send a custom
event type, such as `com.example.game.score` (assuming the client has
rights to the `com.example` namespace) without needing to put the event
into the `m.` namespace.

### Timestamps

Unless otherwise stated, timestamps are measured as milliseconds since
the Unix epoch. Throughout the specification this may be referred to as
POSIX, Unix, or just "time in milliseconds".

## Specification Versions

Matrix as a whole is released under a single specification number in the
form `vX.Y`.

* A change to `X` reflects a breaking or substantially invasive change.
  When exactly to increment this number is left to the Spec Core Team,
  however it is intended for changes such as moving away from JSON,
  altering the signing algorithm, or when a large number of `Y` changes
  feel deserving of a major version increase.
* A change to `Y` represents a backwards compatible or "managed" backwards
  compatible change to the specification, usually in the form of features.

Additionally, the spec version may have arbitrary metadata applied to it
when followed by a `-`. For example, `v1.1-alpha`. Usage of this is not
strictly specified but is intended for usage of pre-release builds of the
specification.

Note that while `v1.2` is meant to be backwards compatible with `v1.1`, it
is not guaranteed that future versions will be fully backwards compatible
with `v1.1`. For example, if `/test` were to be introduced in `v1.1` and
deprecated in `v1.2`, then it can be removed in `v1.3`. More information
about this is described in the [deprecation policy](#deprecation-policy)
below.

### Endpoint versioning

All API endpoints within the specification are versioned individually.
This means that `/v3/sync` (for example) can get deprecated in favour
of `/v4/sync` without affecting `/v3/profile` at all. A server supporting
`/v4/sync` would keep serving `/v3/profile` as it always has.

When an MSC proposes a breaking change to an endpoint it should also
deprecate the existing endpoint. For some endpoints this might be implicit,
such as `/v4/sync` being introduced (deprecating `/v3/sync`), however
for more nuanced examples the MSC should deprecate the endpoint explicitly.

### Deprecation policy

An MSC is required to transition something from stable (the default) to
deprecated. Once something has been deprecated for suitably long enough
(usually 1 version), it is eligible for removal from the specification
with another MSC.

Implementations of Matrix are required to implement deprecated functionality
of the specification, though when the functionality is later removed then
the implementation is welcome to drop support (if they don't advertise
support for a version which includes deprecated functionality). For
example, if `/test` were deprecated in `v1.2` and removed in `v1.3`, then
an implementation which wants to advertise support for `v1.2` would have
to implement `/test`, even if the implementation also advertises support
for `v1.3`. If that implementation *only* advertises support for `v1.3`
then it would not be required to implement `/test`.

### Legacy versioning

Prior to this system, the different APIs of Matrix were versioned individually.
This is no longer possible with the new specification versioning approach.

For historical reference, the APIs were versioned as `rX.Y.Z` where `X`
roughly represents a breaking change, `Y` a backwards-compatible change, and
`Z` a patch or insignificant alteration to the API.

`v1.0` of Matrix was released on June 10th, 2019 with the following API
versions:

| API/Specification       | Version |
|-------------------------|---------|
| Client-Server API       | r0.5.0  |
| Server-Server API       | r0.1.2  |
| Application Service API | r0.1.1  |
| Identity Service API    | r0.1.1  |
| Push Gateway API        | r0.1.0  |
| Room Version            | v5      |


## License

The Matrix specification is licensed under the [Apache License, Version
2.0](http://www.apache.org/licenses/LICENSE-2.0).
