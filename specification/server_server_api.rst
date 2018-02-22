.. Copyright 2016 OpenMarket Ltd
.. Copyright 2017 New Vector Ltd
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

Matrix homeservers use the Federation APIs (also known as server-server APIs)
to communicate with each other. Homeservers use these APIs to push messages to
each other in real-time, to request historic messages from each other, and to
query profile and presence information about users on each other's servers.

The APIs are implemented using HTTPS GETs and PUTs between each of the
servers. These HTTPS requests are strongly authenticated using public key
signatures at the TLS transport layer and using public key signatures in
HTTP Authorization headers at the HTTP layer.

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

Each matrix homeserver is identified by a server name consisting of a DNS name
and an optional TLS port.

.. code::

    server_name = dns_name [ ":" tls_port]
    dns_name = <host, see [RFC 3986], Section 3.2.2>
    tls_port = *DIGIT

.. **

If the port is present then the server is discovered by looking up an AAAA or
A record for the DNS name and connecting to the specified TLS port. If the port
is absent then the server is discovered by looking up a ``_matrix._tcp`` SRV
record for the DNS name. If this record does not exist then the server is
discovered by looking up an AAAA or A record on the DNS name and taking the
default fallback port number of 8448.
Homeservers may use SRV records to load balance requests between multiple TLS
endpoints or to failover to another endpoint if an endpoint fails.

Server implementation
~~~~~~~~~~~~~~~~~~~~~~

{{version_ss_http_api}}

Retrieving Server Keys
~~~~~~~~~~~~~~~~~~~~~~

Version 2
+++++++++

Each homeserver publishes its public keys under ``/_matrix/key/v2/server/``.
Homeservers query for keys by either getting ``/_matrix/key/v2/server/``
directly or by querying an intermediate notary server using a
``/_matrix/key/v2/query`` API. Intermediate notary servers query the
``/_matrix/key/v2/server/`` API on behalf of another server and sign the
response with their own key. A server may query multiple notary servers to
ensure that they all report the same public keys.

This approach is borrowed from the `Perspectives Project`_, but modified to
include the NACL keys and to use JSON instead of XML. It has the advantage of
avoiding a single trust-root since each server is free to pick which notary
servers they trust and can corroborate the keys returned by a given notary
server by querying other servers.

.. _Perspectives Project: https://web.archive.org/web/20170702024706/https://perspectives-project.org/

Publishing Keys
^^^^^^^^^^^^^^^

Homeservers publish the allowed TLS fingerprints and signing keys in a JSON
object at ``/_matrix/key/v2/server/{key_id}``. The response contains a list of
``verify_keys`` that are valid for signing federation requests made by the
server and for signing events. It contains a list of ``old_verify_keys``
which are only valid for signing events. Finally the response contains a list
of TLS certificate fingerprints to validate any connection made to the server.

A server may have multiple keys active at a given time. A server may have any
number of old keys. It is recommended that servers return a single JSON
response listing all of its keys whenever any ``key_id`` is requested to reduce
the number of round trips needed to discover the relevant keys for a server.
However a server may return a different responses for a different ``key_id``.

The ``tls_certificates`` contain a list of hashes of the X.509 TLS certificates
currently used by the server. The list must include SHA-256 hashes for every
certificate currently in use by the server. These fingerprints are valid until
the millisecond POSIX timestamp in ``valid_until_ts``.

The ``verify_keys`` can be used to sign requests and events made by the server
until the millisecond POSIX timestamp in ``valid_until_ts``. If a homeserver
receives an event with a ``origin_server_ts`` after the ``valid_until_ts`` then
it should request that ``key_id`` for the originating server to check whether
the key has expired.

The ``old_verify_keys`` can be used to sign events with an ``origin_server_ts``
before the ``expired_ts``. The ``expired_ts`` is a millisecond POSIX timestamp
of when the originating server stopped using that key.

Intermediate notary servers should cache a response for half of its remaining
life time to avoid serving a stale response. Originating servers should avoid
returning responses that expire in less than an hour to avoid repeated requests
for an about to expire certificate. Requesting servers should limit how
frequently they query for certificates to avoid flooding a server with requests.

If a server goes offline intermediate notary servers should continue to return
the last response they received from that server so that the signatures of old
events sent by that server can still be checked.

==================== =================== ======================================
    Key                    Type                         Description
==================== =================== ======================================
``server_name``      String              DNS name of the homeserver.
``verify_keys``      Object              Public keys of the homeserver for
                                         verifying digital signatures.
``old_verify_keys``  Object              The public keys that the server used
                                         to use and when it stopped using them.
``signatures``       Object              Digital signatures for this object
                                         signed using the ``verify_keys``.
``tls_fingerprints`` Array of Objects    Hashes of X.509 TLS certificates used
                                         by this this server encoded as `Unpadded Base64`_.
``valid_until_ts``   Integer             POSIX timestamp when the list of valid
                                         keys should be refreshed.
==================== =================== ======================================


.. code:: json

    {
        "old_verify_keys": {
            "ed25519:auto1": {
                "expired_ts": 922834800000,
                "key": "Base+64+Encoded+Old+Verify+Key"
            }
        },
        "server_name": "example.org",
        "signatures": {
            "example.org": {
                "ed25519:auto2": "Base+64+Encoded+Signature"
            }
        },
        "tls_fingerprints": [
            {
                "sha256": "Base+64+Encoded+SHA-256-Fingerprint"
            }
        ],
        "valid_until_ts": 1052262000000,
        "verify_keys": {
            "ed25519:auto2": {
                "key": "Base+64+Encoded+Signature+Verification+Key"
            }
        }
    }

Querying Keys Through Another Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Servers may offer a query API ``_matrix/key/v2/query/`` for getting the keys
for another server. This API can be used to GET at list of JSON objects for a
given server or to POST a bulk query for a number of keys from a number of
servers. Either way the response is a list of JSON objects containing the
JSON published by the server under ``_matrix/key/v2/server/`` signed by
both the originating server and by this server.

The ``minimum_valid_until_ts`` is a millisecond POSIX timestamp indicating
when the returned certificate will need to be valid until to be useful to the
requesting server. This can be set using the maximum ``origin_server_ts`` of
an batch of events that a requesting server is trying to validate. This allows
an intermediate notary server to give a prompt cached response even if the
originating server is offline.

This API can return keys for servers that are offline be using cached responses
taken from when the server was online. Keys can be queried from multiple
servers to mitigate against DNS spoofing.

Requests:

.. code::

    GET /_matrix/key/v2/query/${server_name}/${key_id}/?minimum_valid_until_ts=${minimum_valid_until_ts} HTTP/1.1

    POST /_matrix/key/v2/query HTTP/1.1
    Content-Type: application/json

    {
        "server_keys": {
            "$server_name": {
                "$key_id": {
                    "minimum_valid_until_ts": $posix_timestamp
                }
            }
        }
    }


Response:

.. code::

    HTTP/1.1 200 OK
    Content-Type: application/json
    {
        "server_keys": [
           # List of responses with same format as /_matrix/key/v2/server
           # signed by both the originating server and this server.
        ]
    }

Version 1
+++++++++
.. WARNING::
  Version 1 of key distribution is obsolete


Homeservers publish their TLS certificates and signing keys in a JSON object
at ``/_matrix/key/v1``.

==================== =================== ======================================
    Key                    Type                         Description
==================== =================== ======================================
``server_name``      String              DNS name of the homeserver.
``verify_keys``      Object              Public keys of the homeserver for
                                         verifying digital signatures.
``signatures``       Object              Digital signatures for this object
                                         signed using the ``verify_keys``.
``tls_certificate``  String              The X.509 TLS certificate used by this
                                         this server encoded as `Unpadded Base64`_.
==================== =================== ======================================

.. code:: json

    {
        "server_name": "example.org",
        "signatures": {
            "example.org": {
                "ed25519:auto": "Base+64+Encoded+Signature"
            }
        },
        "tls_certificate": "Base+64+Encoded+DER+Encoded+X509+TLS+Certificate",
        "verify_keys": {
            "ed25519:auto": "Base+64+Encoded+Signature+Verification+Key"
        }
    }

When fetching the keys for a server the client should check that the TLS
certificate in the JSON matches the TLS server certificate for the connection
and should check that the JSON signatures are correct for the supplied
``verify_keys``

Transactions
------------

The transfer of EDUs and PDUs between homeservers is performed by an exchange
of Transaction messages, which are encoded as JSON objects, passed over an HTTP
PUT request. A Transaction is meaningful only to the pair of homeservers that
exchanged it; they are not globally-meaningful.

Each transaction has:
 - An opaque transaction ID, unique among transactions from the same origin.
 - A timestamp (UNIX epoch time in milliseconds) generated by its origin
   server.
 - An origin and destination server name.
 - A list of PDUs and EDUs - the actual message payload that the Transaction
   carries.

{{transaction_ss_http_api}}

PDUs
----

Each PDU contains a single Room Event which the origin server wants to send to
the destination.


PDU Fields
~~~~~~~~~~

==================== ================== =======================================
 Key                  Type               Description
==================== ================== =======================================
``room_id``          String             **Required**. Room identifier.
``sender``           String             **Required**. The ID of the user sending
                                        the event.
``origin``           String             **Required**. ``server_name`` of the
                                        homeserver that created this event.
``event_id``         String             **Required**. Unique identifier for the
                                        event being sent.
``origin_server_ts`` Integer            **Required**. Timestamp in milliseconds
                                        on origin homeserver when this event
                                        was created.
``type``             String             **Required**. Event type
``state_key``        String             Optional. If this key is present, the
                                        event is a state event, and it will
                                        replace previous events with the same
                                        ``type`` and ``state_key`` in the room
                                        state.
``content``          Object             **Required**. The content of the event.
``prev_events``      List of (String,   **Required**. Event IDs and hashes of
                     {String: String})  the most recent events in the room that
                     pairs              the homeserver was aware of when it
                                        made this event
``depth``            Integer            **Required**. The maximum depth of the
                                        ``prev_events``, plus one
``auth_events``      List of (String,   **Required**. Event IDs and hashes for
                     {String: String})  the "auth events" of this event.
                     pairs
``hashes``           {String: String}   **Required**. Hashes of the PDU,
                                        following the algorithm specified in
                                        `Signing Events`_.
``signatures``       {String:           **Required**. Signatures of the redacted
                     {String: String}}  PDU, following the algorithm specified
                                        in `Signing Events`_.
``redacts``          String             Optional. For redaction events, the ID
                                        of the event being redacted
``unsigned``         Object             Optional. Additional data added by the
                                        origin server but not covered by the
                                        ``signatures``.
==================== ================== =======================================

Example:

.. code:: json

 {
  "room_id": "!UcYsUzyxTGDxLBEvLy:example.org",
  "sender": "@alice:example.com",
  "origin": "example.com",
  "event_id": "$a4ecee13e2accdadf56c1025:example.com",
  "origin_server_ts": 1404838188000,
  "type": "m.room.message",
  "prev_events": [
    ["$af232176:example.org", {"sha256": "abase64encodedsha256hashshouldbe43byteslong"}]
  ],
  "hashes": {"sha256": "thishashcoversallfieldsincasethisisredacted"},
  "signatures": {
    "example.com": {
      "ed25519:key_version:": "these86bytesofbase64signaturecoveressentialfieldsincludinghashessocancheckredactedpdus"
    }
  },
  "content": {...}
 }

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

1. If type is ``m.room.create``, allow if and only if it has no
   previous events - *i.e.* it is the first event in the room.

#. If type is ``m.room.member``:

   a. If ``membership`` is ``join``:

      i. If the only previous event is an ``m.room.create``
         and the ``state_key`` is the creator, allow.

      #. If the ``sender`` does not match ``state_key``, reject.

      #. If the user's current membership state is ``invite`` or ``join``,
         allow.

      #. If the ``join_rule`` is ``public``, allow.

      #. Otherwise, reject.

   #. If ``membership`` is ``invite``:

      i. If the ``sender``'s current membership state is not ``join``, reject.

      #. If *target user*'s current membership state is ``join`` or ``ban``,
         reject.

      #. If the ``sender``'s power level is greater than or equal to the *invite
         level*, allow.

      #. Otherwise, reject.

   #. If ``membership`` is ``leave``:

      i. If the ``sender`` matches ``state_key``, allow if and only if that user's
         current membership state is ``invite`` or ``join``.

      #. If the ``sender``'s current membership state is not ``join``, reject.

      #. If the *target user*'s current membership state is ``ban``, and the
         ``sender``'s power level is less than the *ban level*, reject.

      #. If the ``sender``'s power level is greater than or equal to the *kick
         level*, and the *target user*'s power level is less than the
         ``sender``'s power level, allow.

      #. Otherwise, reject.

   #. If ``membership`` is ``ban``:

      i. If the ``sender``'s current membership state is not ``join``, reject.

      #. If the ``sender``'s power level is greater than or equal to the *ban
         level*, and the *target user*'s power level is less than the
         ``sender``'s power level, allow.

      #. Otherwise, reject.

   #. Otherwise, the membership is unknown. Reject.

#. If the ``sender``'s current membership state is not ``join``, reject.

#. If the event type's *required power level* is greater than the ``sender``'s power
   level, reject.

#. If type is ``m.room.power_levels``:

   a. If there is no previous ``m.room.power_levels`` event in the room, allow.

   #. For each of the keys ``users_default``, ``events_default``,
      ``state_default``, ``ban``, ``redact``, ``kick``, ``invite``, as well as
      each entry being changed under the ``events`` or ``users`` keys:

      i. If the current value is higher than the ``sender``'s current power level,
         reject.

      #. If the new value is higher than the ``sender``'s current power level,
         reject.

   #. For each entry being changed under the ``users`` key, other than the
      ``sender``'s own entry:

      i. If the current value is equal to the ``sender``'s current power level,
         reject.

   #. Otherwise, allow.

#. If type is ``m.room.redaction``:

   #. If the ``sender``'s power level is greater than or equal to the *redact
      level*, allow.

   #. If the ``sender`` of the event being redacted is the same as the
      ``sender`` of the ``m.room.redaction``, allow.

   #. Otherwise, reject.

#. Otherwise, allow.

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

EDUs
----

.. WARNING::
  This section may be misleading or inaccurate.

EDUs, by comparison to PDUs, do not have an ID, a room ID, or a list of
"previous" IDs. The only mandatory fields for these are the type, origin and
destination homeserver names, and the actual nested content.

======================== ============ =========================================
 Key                      Type          Description
======================== ============ =========================================
``edu_type``             String       The type of the ephemeral message.
``content``              Object       Content of the ephemeral message.
======================== ============ =========================================

.. code:: json

 {
  "edu_type":"m.presence",
  "origin":"blue",
  "destination":"orange",
  "content":{...}
 }

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

Protocol URLs
-------------

.. WARNING::
  This section may be misleading or inaccurate.

All these URLs are name-spaced within a prefix of::

  /_matrix/federation/v1/...

For active pushing of messages representing live activity "as it happens"::

  PUT .../send/<transaction_id>/
    Body: JSON encoding of a single Transaction
    Response: TODO-doc

The transaction_id path argument will override any ID given in the JSON body.
The destination name will be set to that of the receiving server itself. Each
embedded PDU in the transaction body will be processed.


To fetch all the state of a given room::

  GET .../state/<room_id>/
    Response: JSON encoding of a single Transaction containing multiple PDUs

Retrieves a snapshot of the entire current state of the given room. The
response will contain a single Transaction, inside which will be a list of PDUs
that encode the state.


To fetch a particular event::

  GET .../event/<event_id>/
    Response: JSON encoding of a partial Transaction containing the event

Retrieves a single event. The response will contain a partial Transaction,
having just the ``origin``, ``origin_server_ts`` and ``pdus`` fields; the
event will be encoded as the only PDU in the ``pdus`` list.


To backfill events on a given room::

  GET .../backfill/<room_id>/
    Query args: v, limit
    Response: JSON encoding of a single Transaction containing multiple PDUs

Retrieves a sliding-window history of previous PDUs that occurred on the given
room. Starting from the PDU ID(s) given in the "v" argument, the PDUs that
preceded it are retrieved, up to a total number given by the "limit" argument.


To stream events all the events::

  GET .../pull/
    Query args: origin, v
    Response: JSON encoding of a single Transaction consisting of multiple PDUs

Retrieves all of the transactions later than any version given by the "v"
arguments.


To make a query::

  GET .../query/<query_type>
    Query args: as specified by the individual query types
    Response: JSON encoding of a response object

Performs a single query request on the receiving homeserver. The Query Type
part of the path specifies the kind of query being made, and its query
arguments have a meaning specific to that kind of query. The response is a
JSON-encoded object whose meaning also depends on the kind of query.


To join a room::

  GET .../make_join/<room_id>/<user_id>
    Response: JSON encoding of a join proto-event

  PUT .../send_join/<room_id>/<event_id>
    Response: JSON encoding of the state of the room at the time of the event

Performs the room join handshake. For more information, see "Joining Rooms"
below.

Joining Rooms
-------------

When a new user wishes to join room that the user's homeserver already knows
about, the homeserver can immediately determine if this is allowable by
inspecting the state of the room, and if it is acceptable, it can generate,
sign, and emit a new ``m.room.member`` state event adding the user into that
room. When the homeserver does not yet know about the room it cannot do this
directly. Instead, it must take a longer multi-stage handshaking process by
which it first selects a remote homeserver which is already participating in
that room, and uses it to assist in the joining process. This is the remote
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
request the room ID and join candidates. This is covered in more detail on the
directory server documentation, below. In the case of a new user joining a
room as a result of a received invite, the joining user's homeserver could
optimise this step away by picking the origin server of that invite message as
the join candidate. However, the joining server should be aware that the origin
server of the invite might since have left the room, so should be prepared to
fall back on the regular join flow if this optimisation fails.

Once the joining server has the room ID and the join candidates, it then needs
to obtain enough information about the room to fill in the required fields of
the ``m.room.member`` event. It obtains this by selecting a resident from the
candidate list, and requesting the ``make_join`` endpoint using a ``GET``
request, specifying the room ID and the user ID of the new member who is
attempting to join.

The resident server replies to this request with a JSON-encoded object having a
single key called ``event``; within this is an object whose fields contain some
of the information that the joining server will need. Despite its name, this
object is not a full event; notably it does not need to be hashed or signed by
the resident homeserver. The required fields are:

==================== ======== ============
 Key                  Type     Description
==================== ======== ============
``type``             String   The value ``m.room.member``
``auth_events``      List     An event-reference list containing the
                              authorization events that would allow this member
                              to join
``content``          Object   The event content
``depth``            Integer  (this field must be present but is ignored; it
                              may be 0)
``origin``           String   The name of the resident homeserver
``origin_server_ts`` Integer  A timestamp added by the resident homeserver
``prev_events``      List     An event-reference list containing the immediate
                              predecessor events
``room_id``          String   The room ID of the room
``sender``           String   The user ID of the joining member
``state_key``        String   The user ID of the joining member
==================== ======== ============

The ``content`` field itself must be an object, containing:

============== ====== ============
 Key            Type   Description
============== ====== ============
``membership`` String The value ``join``
============== ====== ============

The joining server now has sufficient information to construct the real join
event from these protoevent fields. It copies the values of most of them,
adding (or replacing) the following fields:

==================== ======= ============
 Key                  Type    Description
==================== ======= ============
``event_id``         String  A new event ID specified by the joining homeserver
``origin``           String  The name of the joining homeserver
``origin_server_ts`` Integer A timestamp added by the joining homeserver
==================== ======= ============

This will be a true event, so the joining server should apply the event-signing
algorithm to it, resulting in the addition of the ``hashes`` and ``signatures``
fields.

To complete the join handshake, the joining server must now submit this new
event to an resident homeserver, by using the ``send_join`` endpoint. This is
invoked using the room ID and the event ID of the new member event.

The resident homeserver then accepts this event into the room's event graph,
and responds to the joining server with the full set of state for the newly-
joined room. This is returned as a two-element list, whose first element is the
integer 200, and whose second element is an object which contains the
following keys:

============== ===== ============
 Key            Type  Description
============== ===== ============
``auth_chain`` List  A list of events giving all of the events in the auth
                     chains for the join event and the events in ``state``.
``state``      List  A complete list of the prevailing state events at the
                     instant just before accepting the new ``m.room.member``
                     event.
============== ===== ============

.. TODO-spec
  - (paul) I don't really understand why the full auth_chain events are given
    here. What purpose does it serve expanding them out in full, when surely
    they'll appear in the state anyway?

Backfilling
-----------

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
that it thinks may have more (most likely this should be a homeserver for some
of the existing users in the room at the earliest point in history it has
currently), and makes a ``/backfill`` request. The parameters of this request
give an event ID that the requesting homeserver wishes to obtain, and a number
specifying how many more events of history before that one to return at most.

The response to this request is an object with the following keys:

==================== ======== ============
 Key                  Type     Description
==================== ======== ============
``pdus``             List     A list of events
``origin``           String   The name of the resident homeserver
``origin_server_ts`` Integer  A timestamp added by the resident homeserver
==================== ======== ============

The list of events given in ``pdus`` is returned in reverse chronological
order; having the most recent event first (i.e. the event whose event ID is
that requested by the requestor in the ``v`` parameter).

.. TODO-spec
  Specify (or remark that it is unspecified) how the server handles divergent
  history. DFS? BFS? Anything weirder?

Exchanging room data
---------------------

.. WARNING::
  This section is incomplete and only act as a knowledge holder until it is
  formalized.

Because of the decentralized and federated nature of Matrix, it is very likely
that data is not received in order or delayed in transit.

Matrix provides several proactive flows so homeservers can try to complete their
DAG if they become aware that parts of it are missing.

{{room_get_missing_events_ss_http_api}}

{{room_get_state_ss_http_api}}

Inviting to a room
------------------

When a user wishes to invite an other user to a local room and the other user
is on a different server, the inviting server will send a request to the invited
server::

  PUT .../invite/{roomId}/{eventId}

The required fields in the JSON body are:

==================== ======== ============
 Key                  Type     Description
==================== ======== ============
``room_id``          String   The room ID of the room. Must be the same as the
                              room ID specified in the path.
``event_id``         String   The ID of the event. Must be the same as the event
                              ID specified in the path.
``type``             String   The value ``m.room.member``.
``auth_events``      List     An event-reference list containing the IDs of the
                              authorization events that would allow this member
                              to be invited in the room.
``content``          Object   The content of the event.
``depth``            Integer  The depth of the event.
``origin``           String   The name of the inviting homeserver.
``origin_server_ts`` Integer  A timestamp added by the inviting homeserver.
``prev_events``      List     An event-reference list containing the IDs of the
                              immediate predecessor events.
``sender``           String   The Matrix ID of the user who sent the original
                              `m.room.third_party_invite`.
``state_key``        String   The Matrix ID of the invited user.
``signatures``       Object   The signature of the event from the origin server.
``unsigned``         Object   An object containing the properties that aren't
                              part of the signature's computation.
==================== ======== ============

Where the ``content`` key contains the content for the ``m.room.member`` event
specified in the `Client-Server API`_. Note that the ``membership`` property of
the content must be ``invite``.

Upon receiving this request, the invited homeserver will append its signature to
the event and respond to the request with the following JSON body::

 [
   200,
   "event": {...}
 ]

Where ``event`` contains the event signed by both homeservers, using the same
JSON keys as the initial request on ``/invite/{roomId}/{eventId}``. Note that,
except for the ``signatures`` object (which now contains an additional signature),
all of the event's keys remain the same as in the event initially provided.

This response format is due to a typo in Synapse, the first implementation of
Matrix's APIs, and is preserved to maintain compatibility.

Now that the event has been signed by both the inviting homeserver and the
invited homeserver, it can be sent to all of the users in the room.

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
the identity server will send a ``POST`` request to the ID's homeserver as described
in the `Invitation Storage`_ section of the Identity Service API.

The following process applies for each invite sent by the identity server:

The invited homeserver will create a ``m.room.member`` invite event containing
a special ``third_party_invite`` section containing the token and a signed object,
both provided by the identity server.

If the invited homeserver is in the room the invite came from, it can auth the
event and send it.

However, if the invited homeserver isn't in the room the invite came from, it
will need to request the room's homeserver to auth the event::

  PUT .../exchange_third_party_invite/{roomId}

Where ``roomId`` is the ID of the room the invite is for.

The required fields in the JSON body are:

==================== ======= ==================================================
 Key                  Type   Description
==================== ======= ==================================================
``type``             String  The event type. Must be `m.room.member`.
``room_id``          String  The ID of the room the event is for. Must be the
                             same as the ID specified in the path.
``sender``           String  The Matrix ID of the user who sent the original
                             `m.room.third_party_invite`.
``state_key``        String  The Matrix ID of the invited user.
``content``          Object  The content of the event.
==================== ======= ==================================================

Where the ``content`` key contains the content for the ``m.room.member`` event
as described in the `Client-Server API`_. Its ``membership`` key must be
``invite`` and its content must include the ``third_party_invite`` object.

The inviting homeserver will then be able to authenticate the event. It will send
a fully authenticated event to the invited homeserver as described in the `Inviting
to a room`_ section above.

Once the invited homeserver responded with the event to which it appended its
signature, the inviting homeserver will respond with ``200 OK`` and an empty body
(``{}``) to the initial request on ``/exchange_third_party_invite/{roomId}`` and
send the now verified ``m.room.member`` invite event to the room's members.

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

Since this ``signed`` object can only be delivered once in the ``POST`` request
emitted by the identity server upon binding between the third-party identifier
and the Matrix ID, and contains the invited user's Matrix ID and the token
delivered when the invite was stored, this verification will prove that the
``m.room.member`` invite event comes from the user owning the invited third-party
identifier.

Authentication
--------------

Request Authentication
~~~~~~~~~~~~~~~~~~~~~~

Every HTTP request made by a homeserver is authenticated using public key
digital signatures. The request method, target and body are signed by wrapping
them in a JSON object and signing it using the JSON signing algorithm. The
resulting signatures are added as an Authorization header with an auth scheme
of X-Matrix. Note that the target field should include the full path starting with
``/_matrix/...``, including the ``?`` and any query parameters if present, but
should not include the leading ``https:``, nor the destination server's
hostname.

Step 1 sign JSON:

.. code::

    {
        "method": "GET",
        "uri": "/target",
        "origin": "origin.hs.example.com",
        "destintation": "destination.hs.example.com",
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

Profiles
--------

The server API for profiles is based entirely on the following Federation
Queries. There are no additional EDU or PDU types involved, other than the
implicit ``m.presence`` and ``m.room.member`` events (see section below).

Querying profile information::

  Query type: profile

  Arguments:
    user_id: the ID of the user whose profile to return
    field: (optional) string giving a field name

  Returns: JSON object containing the following keys:
    displayname: string of free-form text
    avatar_url: string containing an HTTP-scheme URL

If the query contains the optional ``field`` key, it should give the name of a
result field. If such is present, then the result should contain only a field
of that name, with no others present. If not, the result should contain as much
of the user's profile as the homeserver has available and can make public.

Directory
---------

The server API for directory queries is also based on Federation Queries.

{{directory_ss_http_api}}

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
        for the user.


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
calculating the SHA-256 instead.

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

.. _`Invitation storage`: ../identity_service/unstable.html#invitation-storage
.. _`Identity Service API`: ../identity_service/unstable.html
.. _`Client-Server API`: ../client_server/unstable.html#m-room-member
.. _`Inviting to a room`: #inviting-to-a-room
.. _`Canonical JSON`: ../appendices.html#canonical-json
.. _`Unpadded Base64`:  ../appendices.html#unpadded-base64
