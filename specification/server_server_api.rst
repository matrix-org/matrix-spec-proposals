.. Copyright 2016 OpenMarket Ltd
.. Copyright 2017 New Vector Ltd
.. Copyright 2018 New Vector Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Federation API
==============

.. WARNING::
  This API is unstable and will change without warning or discussion while
  we work towards a r0 release (scheduled for August 2018).

Matrix homeservers use the Federation APIs (also known as server-server APIs)
to communicate with each other. Homeservers use these APIs to push messages to
each other in real-time, to retrieve historic messages from each other, and to
query profile and presence information about users on each other's servers.

The APIs are implemented using HTTPS requests between each of the servers. 
These HTTPS requests are strongly authenticated using public key signatures 
at the TLS transport layer and using public key signatures in HTTP 
Authorization headers at the HTTP layer.

There are three main kinds of communication that occur between homeservers:

Persisted Data Units (PDUs):
    These events are broadcast from one homeserver to any others that have
    joined the same room (identified by Room ID). They are persisted in
    long-term storage and record the history of messages and state for a
    room.

    Like email, it is the responsibility of the originating server of a PDU
    to deliver that event to its recipient servers. However PDUs are signed
    using the originating server's private key so that it is possible to
    deliver them through third-party servers.

Ephemeral Data Units (EDUs):
    These events are pushed between pairs of homeservers. They are not
    persisted and are not part of the history of a room, nor does the
    receiving homeserver have to reply to them.

Queries:
    These are single request/response interactions between a given pair of
    servers, initiated by one side sending an HTTPS GET request to obtain some
    information, and responded by the other. They are not persisted and contain
    no long-term significant history. They simply request a snapshot state at
    the instant the query is made.


EDUs and PDUs are further wrapped in an envelope called a Transaction, which is
transferred from the origin to the destination homeserver using an HTTPS PUT
request.

.. contents:: Table of Contents
.. sectnum::

Specification version
---------------------

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

Server Discovery
----------------

Resolving Server Names
~~~~~~~~~~~~~~~~~~~~~~

Each matrix homeserver is identified by a server name consisting of a hostname
and an optional TLS port.

.. code::

    server_name = hostname [ ":" tls_port]
    tls_port = *DIGIT

.. **

If the port is present then the server is discovered by looking up an AAAA or
A record for the hostname and connecting to the specified TLS port. If the port
is absent then the server is discovered by looking up a ``_matrix._tcp`` SRV
record for the hostname. If this record does not exist then the server is
discovered by looking up an AAAA or A record on the hostname and taking the
default fallback port number of 8448.
Homeservers may use SRV records to load balance requests between multiple TLS
endpoints or to failover to another endpoint if an endpoint fails.

If the DNS name is a literal IP address, the port specified or the fallback
port should be used.

When making requests to servers, use the DNS name of the target server in the
``Host`` header, regardless of the host given in the SRV record. For example,
if making a request to ``example.org``, and the SRV record resolves to ``matrix.
example.org``, the ``Host`` header in the request should be ``example.org``. The
port number for target server should not appear in the ``Host`` header.

Server implementation
~~~~~~~~~~~~~~~~~~~~~~

{{version_ss_http_api}}

Retrieving Server Keys
~~~~~~~~~~~~~~~~~~~~~~

.. NOTE::
  There was once a "version 1" of the key exchange. It has been removed from the
  specification due to lack of significance. It may be reviewed `here
  <https://github.com/matrix-org/matrix-doc/blob/51faf8ed2e4a63d4cfd6d23183698ed169956cc0/specification/server_server_api.rst#232version-1>`_.

Each homeserver publishes its public keys under ``/_matrix/key/v2/server/{keyId}``.
Homeservers query for keys by either getting ``/_matrix/key/v2/server/{keyId}``
directly or by querying an intermediate notary server using a
``/_matrix/key/v2/query/{serverName}/{keyId}`` API. Intermediate notary servers 
query the ``/_matrix/key/v2/server/{keyId}`` API on behalf of another server and
sign the response with their own key. A server may query multiple notary servers to
ensure that they all report the same public keys.

This approach is borrowed from the `Perspectives Project`_, but modified to
include the NACL keys and to use JSON instead of XML. It has the advantage of
avoiding a single trust-root since each server is free to pick which notary
servers they trust and can corroborate the keys returned by a given notary
server by querying other servers.

.. _Perspectives Project: https://web.archive.org/web/20170702024706/https://perspectives-project.org/

Publishing Keys
+++++++++++++++

Homeservers publish the allowed TLS fingerprints and signing keys in a JSON
object at ``/_matrix/key/v2/server/{key_id}``. The response contains a list of
``verify_keys`` that are valid for signing federation requests made by the
homeserver and for signing events. It contains a list of ``old_verify_keys`` which
are only valid for signing events. Finally the response contains a list of TLS
certificate fingerprints to validate any connection made to the homeserver.

{{keys_server_ss_http_api}}


Querying Keys Through Another Server
++++++++++++++++++++++++++++++++++++

Servers may query another server's keys through a notary server. The notary
server may be another homeserver. The notary server will retrieve keys from
the queried servers through use of the ``/_matrix/key/v2/server/{keyId}``
API. The notary server will additionally sign the response from the queried
server before returning the results.

Notary servers can return keys for servers that are offline or having issues
serving their own keys by using cached responses. Keys can be queried from
multiple servers to mitigate against DNS spoofing.

{{keys_query_ss_http_api}}

Authentication
--------------

Request Authentication
~~~~~~~~~~~~~~~~~~~~~~

Every HTTP request made by a homeserver is authenticated using public key
digital signatures. The request method, target and body are signed by wrapping
them in a JSON object and signing it using the JSON signing algorithm. The
resulting signatures are added as an Authorization header with an auth scheme
of ``X-Matrix``. Note that the target field should include the full path
starting with ``/_matrix/...``, including the ``?`` and any query parameters if
present, but should not include the leading ``https:``, nor the destination
server's hostname.

Step 1 sign JSON:

.. code::

    {
        "method": "GET",
        "uri": "/target",
        "origin": "origin.hs.example.com",
        "destination": "destination.hs.example.com",
        "content": <request body>,
        "signatures": {
            "origin.hs.example.com": {
                "ed25519:key1": "ABCDEF..."
            }
        }
   }

Step 2 add Authorization header:

.. code::

    GET /target HTTP/1.1
    Authorization: X-Matrix origin=origin.example.com,key="ed25519:key1",sig="ABCDEF..."
    Content-Type: application/json

    <JSON-encoded request body>


Example python code:

.. code:: python

    def authorization_headers(origin_name, origin_signing_key,
                              destination_name, request_method, request_target,
                              content=None):
        request_json = {
             "method": request_method,
             "uri": request_target,
             "origin": origin_name,
             "destination": destination_name,
        }

        if content_json is not None:
            request["content"] = content

        signed_json = sign_json(request_json, origin_name, origin_signing_key)

        authorization_headers = []

        for key, sig in signed_json["signatures"][origin_name].items():
            authorization_headers.append(bytes(
                "X-Matrix origin=%s,key=\"%s\",sig=\"%s\"" % (
                    origin_name, key, sig,
                )
            ))

        return ("Authorization", authorization_headers)

Response Authentication
~~~~~~~~~~~~~~~~~~~~~~~

Responses are authenticated by the TLS server certificate. A homeserver should
not send a request until it has authenticated the connected server to avoid
leaking messages to eavesdroppers.

Client TLS Certificates
~~~~~~~~~~~~~~~~~~~~~~~

Requests are authenticated at the HTTP layer rather than at the TLS layer
because HTTP services like Matrix are often deployed behind load balancers that
handle the TLS and these load balancers make it difficult to check TLS client
certificates.

A homeserver may provide a TLS client certificate and the receiving homeserver
may check that the client certificate matches the certificate of the origin
homeserver.

Transactions
------------

The transfer of EDUs and PDUs between homeservers is performed by an exchange
of Transaction messages, which are encoded as JSON objects, passed over an HTTP
PUT request. A Transaction is meaningful only to the pair of homeservers that
exchanged it; they are not globally-meaningful.

{{transactions_ss_http_api}}

PDUs
----

Each PDU contains a single Room Event which the origin server wants to send to
the destination.

The ``prev_events`` field of a PDU identifies the "parents" of the event, and
thus establishes a partial ordering on events within the room by linking them
into a Directed Acyclic Graph (DAG). The sending server should populate this
field with all of the events in the room for which it has not yet seen a
child - thus demonstrating that the event comes after all other known events.

For example, consider a room whose events form the DAG shown below. A server
creating a new event in this room should populate the new event's
``prev_events`` field with ``E4`` and ``E5``, since neither event yet has a child::

      E1
      ^
      |
  +-> E2 <-+
  |        |
  E3       E5
  ^
  |
  E4

The ``auth_events`` field of a PDU identifies the set of events which give the
sender permission to send the event. The ``auth_events`` for the
``m.room.create`` event in a room is empty; for other events, it should be the
following subset of the room state:

- The ``m.room.create`` event.
- The current ``m.room.power_levels`` event, if any.
- The current ``m.room.join_rules`` event, if any.
- The sender's current ``m.room.member`` event, if any.

{{definition_ss_pdu}}

Authorization of PDUs
~~~~~~~~~~~~~~~~~~~~~

Whenever a server receives an event from a remote server, the receiving server
must check that the event is allowed by the authorization rules. These rules
depend on the state of the room at that event.

Definitions
+++++++++++

Required Power Level
  A given event type has an associated *required power level*. This is given by
  the current ``m.room.power_levels`` event. The event type is either listed
  explicitly in the ``events`` section or given by either ``state_default`` or
  ``events_default`` depending on if the event is a state event or not.

Invite Level, Kick Level, Ban Level, Redact Level
   The levels given by the ``invite``, ``kick``, ``ban``, and ``redact``
   properties in the current ``m.room.power_levels`` state. Each defaults to 50
   if unspecified.

Target User
  For an ``m.room.member`` state event, the user given by the ``state_key`` of
  the event.

.. _`authorization rules`:

Rules
+++++

The rules governing whether an event is authorized depend solely on the
state of the room at the point in the room graph at which the new event is to
be inserted. The types of state events that affect authorization are:

- ``m.room.create``
- ``m.room.member``
- ``m.room.join_rules``
- ``m.room.power_levels``

Servers should not create new events that reference unauthorized events.
However, any event that does reference an unauthorized event is not itself
automatically considered unauthorized.

Unauthorized events that appear in the event graph do *not* have any effect on
the state of the room.

.. Note:: This is in contrast to redacted events which can still affect the
          state of the room. For example, a redacted ``join`` event will still
          result in the user being considered joined.

The rules are as follows:

1. If type is ``m.room.create``, allow if and only if it has no
   previous events - *i.e.* it is the first event in the room.

2. If type is ``m.room.member``:

  a. If ``membership`` is ``join``:

    i. If the only previous event is an ``m.room.create``
       and the ``state_key`` is the creator, allow.

    #. If the ``sender`` does not match ``state_key``, reject.

    #. If the user's current membership state is ``invite`` or ``join``,
       allow.

    #. If the ``join_rule`` is ``public``, allow.

    #. Otherwise, reject.

  b. If ``membership`` is ``invite``:

    i. If the ``sender``'s current membership state is not ``join``, reject.

    #. If *target user*'s current membership state is ``join`` or ``ban``,
       reject.

    #. If the ``sender``'s power level is greater than or equal to the *invite
       level*, allow.

    #. Otherwise, reject.

  c. If ``membership`` is ``leave``:

    i. If the ``sender`` matches ``state_key``, allow if and only if that user's
       current membership state is ``invite`` or ``join``.

    #. If the ``sender``'s current membership state is not ``join``, reject.

    #. If the *target user*'s current membership state is ``ban``, and the
       ``sender``'s power level is less than the *ban level*, reject.

    #. If the ``sender``'s power level is greater than or equal to the *kick
       level*, and the *target user*'s power level is less than the
       ``sender``'s power level, allow.

    #. Otherwise, reject.

  d. If ``membership`` is ``ban``:

    i. If the ``sender``'s current membership state is not ``join``, reject.

    #. If the ``sender``'s power level is greater than or equal to the *ban
       level*, and the *target user*'s power level is less than the
       ``sender``'s power level, allow.

    #. Otherwise, reject.

  e. Otherwise, the membership is unknown. Reject.

3. If the ``sender``'s current membership state is not ``join``, reject.

4. If the event type's *required power level* is greater than the ``sender``'s power
   level, reject.

5. If type is ``m.room.power_levels``:

  a. If there is no previous ``m.room.power_levels`` event in the room, allow.

  b. For each of the keys ``users_default``, ``events_default``,
     ``state_default``, ``ban``, ``redact``, ``kick``, ``invite``, as well as
     each entry being changed under the ``events`` or ``users`` keys:

    i. If the current value is higher than the ``sender``'s current power level,
       reject.

    #. If the new value is higher than the ``sender``'s current power level,
       reject.

  c. For each entry being changed under the ``users`` key, other than the
     ``sender``'s own entry:

    i. If the current value is equal to the ``sender``'s current power level,
       reject.

  d. Otherwise, allow.

6. If type is ``m.room.redaction``:

  a. If the ``sender``'s power level is greater than or equal to the *redact
     level*, allow.

  #. If the ``sender`` of the event being redacted is the same as the
     ``sender`` of the ``m.room.redaction``, allow.

  #. Otherwise, reject.

7. Otherwise, allow.

.. NOTE::

  Some consequences of these rules:

  * Unless you are a member of the room, the only permitted operations (apart
    from the intial create/join) are: joining a public room; accepting or
    rejecting an invitation to a room.

  * To unban somebody, you must have power level greater than or equal to both
    the kick *and* ban levels, *and* greater than the target user's power
    level.

.. TODO-spec

  I think there is some magic about 3pid invites too.

Retrieving event authorization information
++++++++++++++++++++++++++++++++++++++++++

The homeserver may be missing event authorization information, or wish to check
with other servers to ensure it is receiving the correct auth chain. These APIs
give the homeserver an avenue for getting the information it needs.

{{event_auth_ss_http_api}}

EDUs
----

EDUs, by comparison to PDUs, do not have an ID, a room ID, or a list of
"previous" IDs. They are intended to be non-persistent data such as user
presence, typing notifications, etc.

{{definition_ss_edu}}

Room State Resolution
---------------------

The *state* of a room is a map of ``(event_type, state_key)`` to
``event_id``. Each room starts with an empty state, and each state event which
is accepted into the room updates the state of that room.

Where each event has a single ``prev_event``, it is clear what the state of the
room after each event should be. However, when two branches in the event graph
merge, the state of those branches might differ, so a *state resolution*
algorithm must be used to determine the resultant state.

For example, consider the following event graph (where the oldest event, E0,
is at the top)::

      E0
      |
      E1
     /  \
    E2  E4
    |    |
    E3   |
     \  /
      E5


Suppose E3 and E4 are both ``m.room.name`` events which set the name of the
room. What should the name of the room be at E5?

Servers should follow the following recursively-defined algorithm to determine
the room state at a given point on the DAG.

State resolution algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. WARNING::
  This section documents the state resolution algorithm as implemented by
  Synapse as of December 2017 (and therefore the de-facto Matrix protocol).
  However, this algorithm is known to have some problems.

The room state :math:`S'(E)` after an event :math:`E` is defined in terms of
the room state :math:`S(E)` before :math:`E`, and depends on whether
:math:`E` is a state event or a message event:

* If :math:`E` is a message event, then :math:`S'(E) = S(E)`.

* If :math:`E` is a state event, then :math:`S'(E)` is :math:`S(E)`, except
  that its entry corresponding to :math:`E`'s ``event_type`` and ``state_key``
  is replaced by :math:`E`'s ``event_id``.

The room state :math:`S(E)` before :math:`E` is the *resolution* of the set of
states :math:`\{ S'(E'), S'(E''), … \}` consisting of the states after each of
:math:`E`'s ``prev_event``\s :math:`\{ E', E'', … \}`.

The *resolution* of a set of states is defined as follows.  The resolved state
is built up in a number of passes; here we use :math:`R` to refer to the
results of the resolution so far.

* Start by setting :math:`R` to the union of the states to be resolved,
  excluding any *conflicting* events.

* First we resolve conflicts between ``m.room.power_levels`` events. If there
  is no conflict, this step is skipped, otherwise:

  * Assemble all the ``m.room.power_levels`` events from the states to
    be resolved into a list.

  * Sort the list by ascending ``depth`` then descending ``sha1(event_id)``.

  * Add the first event in the list to :math:`R`.

  * For each subsequent event in the list, check that the event would be
    allowed by the `authorization rules`_ for a room in state :math:`R`. If the
    event would be allowed, then update :math:`R` with the event and continue
    with the next event in the list. If it would not be allowed, stop and
    continue below with ``m.room.join_rules`` events.

* Repeat the above process for conflicts between ``m.room.join_rules`` events.

* Repeat the above process for conflicts between ``m.room.member`` events.

* No other events affect the authorization rules, so for all other conflicts,
  just pick the event with the highest depth and lowest ``sha1(event_id)`` that
  passes authentication in :math:`R` and add it to :math:`R`.

A *conflict* occurs between states where those states have different
``event_ids`` for the same ``(state_type, state_key)``. The events thus
affected are said to be *conflicting* events.


Backfilling and retrieving missing events
-----------------------------------------

Once a homeserver has joined a room, it receives all the events emitted by
other homeservers in that room, and is thus aware of the entire history of the
room from that moment onwards. Since users in that room are able to request the
history by the ``/messages`` client API endpoint, it's possible that they might
step backwards far enough into history before the homeserver itself was a
member of that room.

To cover this case, the federation API provides a server-to-server analog of
the ``/messages`` client API, allowing one homeserver to fetch history from
another. This is the ``/backfill`` API.

To request more history, the requesting homeserver picks another homeserver 
that it thinks may have more (most likely this should be a homeserver for 
some of the existing users in the room at the earliest point in history it 
has currently), and makes a ``/backfill`` request.

Similar to backfilling a room's history, a server may not have all the events
in the graph. That server may use the ``/get_missing_events`` API to acquire
the events it is missing.

.. TODO-spec
  Specify (or remark that it is unspecified) how the server handles divergent
  history. DFS? BFS? Anything weirder?

{{backfill_ss_http_api}}

Retrieving events
-----------------

In some circumstances, a homeserver may be missing a particular event or information
about the room which cannot be easily determined from backfilling. These APIs provide
homeservers with the option of getting events and the state of the room at a given
point in the timeline.

{{events_ss_http_api}}


Joining Rooms
-------------

When a new user wishes to join a room that the user's homeserver already knows
about, the homeserver can immediately determine if this is allowable by
inspecting the state of the room. If it is acceptable, it can generate, sign,
and emit a new ``m.room.member`` state event adding the user into that room.
When the homeserver does not yet know about the room it cannot do this
directly. Instead, it must take a longer multi-stage handshaking process by
which it first selects a remote homeserver which is already participating in
that room, and use it to assist in the joining process. This is the remote
join handshake.

This handshake involves the homeserver of the new member wishing to join
(referred to here as the "joining" server), the directory server hosting the
room alias the user is requesting to join with, and a homeserver where existing
room members are already present (referred to as the "resident" server).

In summary, the remote join handshake consists of the joining server querying
the directory server for information about the room alias; receiving a room ID
and a list of join candidates. The joining server then requests information
about the room from one of the residents. It uses this information to construct
a ``m.room.member`` event which it finally sends to a resident server.

Conceptually these are three different roles of homeserver. In practice the
directory server is likely to be resident in the room, and so may be selected
by the joining server to be the assisting resident. Likewise, it is likely that
the joining server picks the same candidate resident for both phases of event
construction, though in principle any valid candidate may be used at each time.
Thus, any join handshake can potentially involve anywhere from two to four
homeservers, though most in practice will use just two.

::

  Client         Joining                Directory       Resident
                 Server                 Server          Server

  join request -->
                 |
                 directory request ------->
                 <---------- directory response
                 |
                 make_join request ----------------------->
                 <------------------------------- make_join response
                 |
                 send_join request ----------------------->
                 <------------------------------- send_join response
                 |
  <---------- join response

The first part of the handshake usually involves using the directory server to
request the room ID and join candidates through the |/query/directory|_
API endpoint. In the case of a new user joining a room as a result of a received
invite, the joining user's homeserver could optimise this step away by picking 
the origin server of that invite message as the join candidate. However, the 
joining server should be aware that the origin server of the invite might since
have left the room, so should be prepared to fall back on the regular join flow 
if this optimisation fails.

Once the joining server has the room ID and the join candidates, it then needs
to obtain enough information about the room to fill in the required fields of
the ``m.room.member`` event. It obtains this by selecting a resident from the
candidate list, and using the ``GET /make_join`` endpoint. The resident server
will then reply with enough information for the joining server to fill in the
event.

The joining server is expected to add or replace the ``origin``, ``origin_server_ts``,
and ``event_id`` on the templated event received by the resident server. This
event is then signed by the joining server.

To complete the join handshake, the joining server must now submit this new
event to a resident homeserver, by using the ``PUT /send_join`` endpoint.

The resident homeserver then accepts this event into the room's event graph,
and responds to the joining server with the full set of state for the
newly-joined room. The resident server must also send the event to other servers
participating in the room. 

{{joins_ss_http_api}}

.. TODO-spec
  - (paul) I don't really understand why the full auth_chain events are given
    here. What purpose does it serve expanding them out in full, when surely
    they'll appear in the state anyway?

Inviting to a room
------------------

When a user on a given homeserver invites another user on the same homeserver,
the homeserver may sign the membership event itself and skip the process defined
here. However, when a user invites another user on a different homeserver, a request
to that homeserver to have the event signed and verified must be made.

{{invites_ss_http_api}}

Leaving Rooms (Rejecting Invites)
---------------------------------

Normally homeservers can send appropriate ``m.room.member`` events to have users
leave the room, or to reject local invites. Remote invites from other homeservers
do not involve the server in the graph and therefore need another approach to 
reject the invite. Joining the room and promptly leaving is not recommended as 
clients and servers will interpret that as accepting the invite, then leaving the
room rather than rejecting the invite.

Similar to the `Joining Rooms`_ handshake, the server which wishes to leave the
room starts with sending a ``/make_leave`` request to a resident server. In the
case of rejecting invites, the resident server may be the server which sent the
invite. After receiving a template event from ``/make_leave``, the leaving server
signs the event and replaces the ``event_id`` with it's own. This is then sent to
the resident server via ``/send_leave``. The resident server will then send the
event to other servers in the room.

{{leaving_ss_http_api}}

Third-party invites
-------------------

When an user wants to invite another user in a room but doesn't know the Matrix
ID to invite, they can do so using a third-party identifier (e.g. an e-mail or a
phone number).

This identifier and its bindings to Matrix IDs are verified by an identity server
implementing the `Identity Service API`_.

Cases where an association exists for a third-party identifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the third-party identifier is already bound to a Matrix ID, a lookup request
on the identity server will return it. The invite is then processed by the inviting
homeserver as a standard ``m.room.member`` invite event. This is the simplest case.

Cases where an association doesn't exist for a third-party identifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the third-party identifier isn't bound to any Matrix ID, the inviting
homeserver will request the identity server to store an invite for this identifier
and to deliver it to whoever binds it to its Matrix ID. It will also send a
``m.room.third_party_invite`` event in the room to specify a display name, a token
and public keys the identity server provided as a response to the invite storage
request.

When a third-party identifier with pending invites gets bound to a Matrix ID,
the identity server will send a POST request to the ID's homeserver as described
in the `Invitation Storage`_ section of the Identity Service API.

The following process applies for each invite sent by the identity server:

The invited homeserver will create a ``m.room.member`` invite event containing
a special ``third_party_invite`` section containing the token and a signed object,
both provided by the identity server.

If the invited homeserver is in the room the invite came from, it can auth the
event and send it.

However, if the invited homeserver isn't in the room the invite came from, it
will need to request the room's homeserver to auth the event.

{{third_party_invite_ss_http_api}}

Verifying the invite
++++++++++++++++++++

When a homeserver receives a ``m.room.member`` invite event for a room it's in
with a ``third_party_invite`` object, it must verify that the association between
the third-party identifier initially invited to the room and the Matrix ID that
claims to be bound to it has been verified without having to rely on a third-party
server.

To do so, it will fetch from the room's state events the ``m.room.third_party_invite``
event for which the state key matches with the value for the ``token`` key in the
``third_party_invite`` object from the ``m.room.member`` event's content to fetch the
public keys initially delivered by the identity server that stored the invite.

It will then use these keys to verify that the ``signed`` object (in the
``third_party_invite`` object from the ``m.room.member`` event's content) was
signed by the same identity server.

Since this ``signed`` object can only be delivered once in the POST request
emitted by the identity server upon binding between the third-party identifier
and the Matrix ID, and contains the invited user's Matrix ID and the token
delivered when the invite was stored, this verification will prove that the
``m.room.member`` invite event comes from the user owning the invited third-party
identifier.

Public Room Directory
---------------------

To compliment the `Client-Server API`_'s room directory, homeservers need a
way to query the public rooms for another server. This can be done by making
a request to the ``/publicRooms`` endpoint for the server the room directory
should be retrieved for.

{{public_rooms_ss_http_api}}


Typing Notifications
--------------------

When a server's users send typing notifications, those notifications need to
be sent to other servers in the room so their users are aware of the same
state. Receiving servers should verify that the user is in the room, and is
a user belonging to the sending server.

{{definition_ss_event_schemas_m_typing}}

Presence
--------
The server API for presence is based entirely on exchange of the following
EDUs. There are no PDUs or Federation Queries involved.

Performing a presence update and poll subscription request::

  EDU type: m.presence

  Content keys:
    push: (optional): list of push operations.
      Each should be an object with the following keys:
        user_id: string containing a User ID
        presence: "offline"|"unavailable"|"online"|"free_for_chat"
        status_msg: (optional) string of free-form text
        last_active_ago: milliseconds since the last activity by the user

    poll: (optional): list of strings giving User IDs

    unpoll: (optional): list of strings giving User IDs

The presence of this combined message is two-fold: it informs the recipient
server of the current status of one or more users on the sending server (by the
``push`` key), and it maintains the list of users on the recipient server that
the sending server is interested in receiving updates for, by adding (by the
``poll`` key) or removing them (by the ``unpoll`` key). The ``poll`` and
``unpoll`` lists apply *changes* to the implied list of users; any existing IDs
that the server sent as ``poll`` operations in a previous message are not
removed until explicitly requested by a later ``unpoll``.

On receipt of a message containing a non-empty ``poll`` list, the receiving
server should immediately send the sending server a presence update EDU of its
own, containing in a ``push`` list the current state of every user that was in
the original EDU's ``poll`` list.

Sending a presence invite::

  EDU type: m.presence_invite

  Content keys:
    observed_user: string giving the User ID of the user whose presence is
      requested (i.e. the recipient of the invite)
    observer_user: string giving the User ID of the user who is requesting to
      observe the presence (i.e. the sender of the invite)

Accepting a presence invite::

  EDU type: m.presence_accept

  Content keys - as for m.presence_invite

Rejecting a presence invite::

  EDU type: m.presence_deny

  Content keys - as for m.presence_invite

.. TODO-doc
  - Explain the timing-based round-trip reduction mechanism for presence
    messages
  - Explain the zero-byte presence inference logic
  See also: docs/client-server/model/presence

Querying for information
------------------------

Queries are a way to retrieve information from a homeserver about a resource,
such as a user or room. The endpoints here are often called in conjunction with
a request from a client on the client-server API in order to complete the call.

There are several types of queries that can be made. The generic endpoint to
represent all queries is described first, followed by the more specific queries
that can be made.

{{query_ss_http_api}}

OpenID
------

Third party services can exchange an access token previously generated by the 
`Client-Server API` for information about a user. This can help verify that a
user is who they say they are without granting full access to the user's account.

Access tokens generated by the OpenID API are only good for the OpenID API and 
nothing else.

{{openid_ss_http_api}}

Send-to-device messaging
------------------------

.. TODO: add modules to the federation spec and make this a module

The server API for send-to-device messaging is based on the following
EDU. There are no PDUs or Federation Queries involved.

Each send-to-device message should be sent to the destination server using
the following EDU::

  EDU type: m.direct_to_device

  Content keys:
    sender: user ID of the sender

    type: event type for the message

    message_id: unique id for the message: used for idempotence

    messages: The messages to send. A map from user ID, to a map from device ID
        to message body. The device ID may also be *, meaning all known devices
        for the user


Content Repository
------------------

Attachments to events (images, files, etc) are uploaded to a homeserver via the
Content Repository described in the `Client-Server API`_. When a server wishes
to serve content originating from a remote server, it needs to ask the remote
server for the media.

Servers should use the server described in the Matrix Content URI, which has the
format ``mxc://{ServerName}/{MediaID}``. Servers should use the download endpoint
described in the `Client-Server API`_, being sure to use the ``allow_remote``
parameter (set to ``false``).


Signing Events
--------------

Signing events is complicated by the fact that servers can choose to redact
non-essential parts of an event.

Before signing the event, the ``unsigned`` and ``signature`` members are
removed, it is encoded as `Canonical JSON`_, and then hashed using SHA-256. The
resulting hash is then stored in the event JSON in a ``hash`` object under a
``sha256`` key.

.. code:: python

    def hash_event(event_json_object):

        # Keys under "unsigned" can be modified by other servers.
        # They are useful for conveying information like the age of an
        # event that will change in transit.
        # Since they can be modifed we need to exclude them from the hash.
        unsigned = event_json_object.pop("unsigned", None)

        # Signatures will depend on the current value of the "hashes" key.
        # We cannot add new hashes without invalidating existing signatures.
        signatures = event_json_object.pop("signatures", None)

        # The "hashes" key might contain multiple algorithms if we decide to
        # migrate away from SHA-2. We don't want to include an existing hash
        # output in our hash so we exclude the "hashes" dict from the hash.
        hashes = event_json_object.pop("hashes", {})

        # Encode the JSON using a canonical encoding so that we get the same
        # bytes on every server for the same JSON object.
        event_json_bytes = encode_canonical_json(event_json_bytes)

        # Add the base64 encoded bytes of the hash to the "hashes" dict.
        hashes["sha256"] = encode_base64(sha256(event_json_bytes).digest())

        # Add the "hashes" dict back the event JSON under a "hashes" key.
        event_json_object["hashes"] = hashes
        if unsigned is not None:
            event_json_object["unsigned"] = unsigned
        return event_json_object

The event is then stripped of all non-essential keys both at the top level and
within the ``content`` object. Any top-level keys not in the following list
MUST be removed:

.. code::

    auth_events
    depth
    event_id
    hashes
    membership
    origin
    origin_server_ts
    prev_events
    prev_state
    room_id
    sender
    signatures
    state_key
    type

A new ``content`` object is constructed for the resulting event that contains
only the essential keys of the original ``content`` object. If the original
event lacked a ``content`` object at all, a new empty JSON object is created
for it.

The keys that are considered essential for the ``content`` object depend on the
the ``type`` of the event. These are:

.. code::

    type is "m.room.aliases":
      aliases

    type is "m.room.create":
      creator

    type is "m.room.history_visibility":
      history_visibility

    type is "m.room.join_rules":
      join_rule

    type is "m.room.member":
      membership

    type is "m.room.power_levels":
      ban
      events
      events_default
      kick
      redact
      state_default
      users
      users_default

The resulting stripped object with the new ``content`` object and the original
``hashes`` key is then signed using the JSON signing algorithm outlined below:

.. code:: python

    def sign_event(event_json_object, name, key):

        # Make sure the event has a "hashes" key.
        if "hashes" not in event_json_object:
            event_json_object = hash_event(event_json_object)

        # Strip all the keys that would be removed if the event was redacted.
        # The hashes are not stripped and cover all the keys in the event.
        # This means that we can tell if any of the non-essential keys are
        # modified or removed.
        stripped_json_object = strip_non_essential_keys(event_json_object)

        # Sign the stripped JSON object. The signature only covers the
        # essential keys and the hashes. This means that we can check the
        # signature even if the event is redacted.
        signed_json_object = sign_json(stripped_json_object)

        # Copy the signatures from the stripped event to the original event.
        event_json_object["signatures"] = signed_json_oject["signatures"]
        return event_json_object

Servers can then transmit the entire event or the event with the non-essential
keys removed. If the entire event is present, receiving servers can then check
the event by computing the SHA-256 of the event, excluding the ``hash`` object.
If the keys have been redacted, then the ``hash`` object is included when
calculating the SHA-256 hash instead.

New hash functions can be introduced by adding additional keys to the ``hash``
object. Since the ``hash`` object cannot be redacted a server shouldn't allow
too many hashes to be listed, otherwise a server might embed illict data within
the ``hash`` object. For similar reasons a server shouldn't allow hash values
that are too long.

.. TODO
  [[TODO(markjh): We might want to specify a maximum number of keys for the
  ``hash`` and we might want to specify the maximum output size of a hash]]
  [[TODO(markjh) We might want to allow the server to omit the output of well
  known hash functions like SHA-256 when none of the keys have been redacted]]

.. |/query/directory| replace:: ``/query/directory``
.. _/query/directory: #get-matrix-federation-v1-query-directory

.. _`Invitation storage`: ../identity_service/unstable.html#invitation-storage
.. _`Identity Service API`: ../identity_service/unstable.html
.. _`Client-Server API`: ../client_server/unstable.html
.. _`Inviting to a room`: #inviting-to-a-room
.. _`Canonical JSON`: ../appendices.html#canonical-json
.. _`Unpadded Base64`:  ../appendices.html#unpadded-base64
