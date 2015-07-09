Federation API
==============

Matrix home servers use the Federation APIs (also known as server-server APIs)
to communicate with each other.
Home servers use these APIs to push messages to each other in real-time, to
request historic messages from each other, and to query profile and presence
information about users on each other's servers.

The APIs are implemented using HTTPS GETs and PUTs between each of the
servers. These HTTPS requests are strongly authenticated using public key
signatures at the TLS transport layer and using public key signatures in
HTTP Authorization headers at the HTTP layer.

There are three main kinds of communication that occur between home servers:

Persisted Data Units (PDUs):
    These events are broadcast from one home server to any others that have
    joined the same "context" (namely, a Room ID). They are persisted in
    long-term storage and record the history of messages and state for a
    context.

    Like email, it is the responsibility of the originating server of a PDU
    to deliver that event to its recepient servers. However PDUs are signed
    using the originating server's public key so that it is possible to
    deliver them through third-party servers.

Ephemeral Data Units (EDUs):
    These events are pushed between pairs of home servers. They are not
    persisted and are not part of the history of a "context", nor does the
    receiving home server have to reply to them.

Queries:
    These are single request/response interactions between a given pair of
    servers, initiated by one side sending an HTTPS GET request to obtain some
    information, and responded by the other. They are not persisted and contain
    no long-term significant history. They simply request a snapshot state at
    the instant the query is made.


EDUs and PDUs are further wrapped in an envelope called a Transaction, which is
transferred from the origin to the destination home server using an HTTPS PUT
request.

Server Discovery
----------------

Resolving Server Names
~~~~~~~~~~~~~~~~~~~~~~

Each matrix home server is identified by a server name consisting of a DNS name
and an optional TLS port.

.. code::

    server_name = dns_name [ ":" tls_port]
    dns_name = <host, see [RFC 3986], Section 3.2.2>
    tls_port = *DIGIT

.. **

If the port is present then the server is discovered by looking up an A record
for the DNS name and connecting to the specified TLS port. If the port is
absent then the server is discovered by looking up a ``_matrix._tcp``
SRV record for the DNS name.

Home servers may use SRV records to load balance requests between multiple TLS
endpoints or to failover to another endpoint if an endpoint fails.

Retrieving Server Keys
~~~~~~~~~~~~~~~~~~~~~~

Version 2
+++++++++

Each home server publishes its public keys under ``/_matrix/key/v2/server/``.
Home servers query for keys by either getting ``/_matrix/key/v2/server/``
directly or by querying an intermediate perspective server using a
``/_matrix/key/v2/query`` API. Intermediate perspective servers query the
``/_matrix/key/v2/server/`` API on behalf of another server and sign the
response with their own key. A server may query multiple perspective servers
to ensure that they all report the same public keys.

This approach is borrowed from the Perspectives Project
(http://perspectives-project.org/), but modified to include the NACL keys and to
use JSON instead of XML. It has the advantage of avoiding a single trust-root
since each server is free to pick which perspective servers they trust and can
corroborate the keys returned by a given perspective server by querying other
servers.

Publishing Keys
_______________

Home servers publish the allowed TLS fingerprints and signing keys in a JSON
object at ``/_matrix/key/v2/server/${key_id}``. The response contains a list of
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
until the millisecond POSIX timestamp in ``valid_until_ts``. If a Home Server
receives an event with a ``origin_server_ts`` after the ``valid_until_ts`` then
it should request that ``key_id`` for the originating server to check whether
the key has expired.

The ``old_verify_keys`` can be used to sign events with an ``origin_server_ts``
before the ``expired_ts``. The ``expired_ts`` is a millisecond POSIX timestamp
of when the originating server stopped using that key.

Intermediate perspective servers should cache a response for half of its
remaining life time to avoid serving a stale response. Originating servers should
avoid returning responses that expire in less than an hour to avoid repeated
requests for an about to expire certificate. Requesting servers should limit how
frequently they query for certificates to avoid flooding a server with requests.

If a server goes offline intermediate perspective servers should continue to
return the last response they received from that server so that the signatures
of old events sent by that server can still be checked.

==================== =================== ======================================
    Key                    Type                         Description
==================== =================== ======================================
``server_name``      String              DNS name of the home server.
``verify_keys``      Object              Public keys of the home server for
                                         verifying digital signatures.
``old_verify_keys``  Object              The public keys that the server used
                                         to use and when it stopped using them.
``signatures``       Object              Digital signatures for this object
                                         signed using the ``verify_keys``.
``tls_fingerprints`` Array of Objects    Hashes of X.509 TLS certificates used
                                         by this this server encoded as base64.
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
____________________________________

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
an intermediate perspectives server to give a prompt cached response even if
the originating server is offline.

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


Home servers publish their TLS certificates and signing keys in a JSON object
at ``/_matrix/key/v1``.

==================== =================== ======================================
    Key                    Type                         Description
==================== =================== ======================================
``server_name``      String              DNS name of the home server.
``verify_keys``      Object              Public keys of the home server for
                                         verifying digital signatures.
``signatures``       Object              Digital signatures for this object
                                         signed using the ``verify_keys``.
``tls_certificate``  String              The X.509 TLS certificate used by this
                                         this server encoded as base64.
==================== =================== ======================================

.. code:: json

    {
        "server_name": "example.org",
        "signatures": {
            "example.org": {
                "ed25519:auto": "Base+64+Encoded+Signature"
            }
        },
        "tls_certificate": "Base+64+Encoded+DER+Encoded+X509+TLS+Certificate"
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
.. WARNING::
  This section may be misleading or inaccurate.

The transfer of EDUs and PDUs between home servers is performed by an exchange
of Transaction messages, which are encoded as JSON objects, passed over an HTTP
PUT request. A Transaction is meaningful only to the pair of home servers that
exchanged it; they are not globally-meaningful.

Each transaction has:
 - An opaque transaction ID.
 - A timestamp (UNIX epoch time in milliseconds) generated by its origin
   server.
 - An origin and destination server name.
 - A list of "previous IDs".
 - A list of PDUs and EDUs - the actual message payload that the Transaction
   carries.

Transaction Fields
~~~~~~~~~~~~~~~~~~

==================== =================== ======================================
    Key              Type                         Description
==================== =================== ======================================
``origin``           String              DNS name of homeserver making this
                                         transaction.
``origin_server_ts`` Integer             Timestamp in milliseconds on
                                         originating homeserver when this
                                         transaction started.
``previous_ids``     List of Strings     List of transactions that were sent
                                         immediately prior to this transaction.
``pdus``             List of Objects     List of persistent updates to rooms.
``edus``             List of Objects     List of ephemeral messages.
==================== =================== ======================================

.. code:: json

 {
  "transaction_id":"916d630ea616342b42e98a3be0b74113",
  "ts":1404835423000,
  "origin":"red",
  "prev_ids":["e1da392e61898be4d2009b9fecce5325"],
  "pdus":[...],
  "edus":[...]
 }

The ``prev_ids`` field contains a list of previous transaction IDs that the
``origin`` server has sent to this ``destination``. Its purpose is to act as a
sequence checking mechanism - the destination server can check whether it has
successfully received that Transaction, or ask for a re-transmission if not.

The ``pdus`` field of a transaction is a list, containing zero or more PDUs.[*]
Each PDU is itself a JSON object containing a number of keys, the exact details
of which will vary depending on the type of PDU. Similarly, the ``edus`` field
is another list containing the EDUs. This key may be entirely absent if there
are no EDUs to transfer.

(* Normally the PDU list will be non-empty, but the server should cope with
receiving an "empty" transaction, as this is useful for informing peers of other
transaction IDs they should be aware of. This effectively acts as a push
mechanism to encourage peers to continue to replicate content.)

PDUs
----

All PDUs have:

- An ID
- A context
- A declaration of their type
- A list of other PDU IDs that have been seen recently on that context
  (regardless of which origin sent them)


Required PDU Fields
~~~~~~~~~~~~~~~~~~~

==================== ================== =======================================
 Key                  Type               Description
==================== ================== =======================================
``context``          String             Event context identifier
``user_id``          String             The ID of the user sending the PDU
``origin``           String             DNS name of homeserver that created
                                        this PDU
``pdu_id``           String             Unique identifier for PDU on the
                                        originating homeserver
``origin_server_ts`` Integer            Timestamp in milliseconds on origin
                                        homeserver when this PDU was created.
``pdu_type``         String             PDU event type
``content``          Object             The content of the PDU.
``prev_pdus``        List of (String,   The originating homeserver, PDU ids and
                     String, Object)    hashes of the most recent PDUs the
                     Triplets           homeserver was aware of for the context
                                        when it made this PDU
``depth``            Integer            The maximum depth of the previous PDUs
                                        plus one
``is_state``         Boolean            True if this PDU is updating room state
==================== ================== =======================================

.. code:: json

 {
  "context":"#example:green.example.com",
  "origin":"green.example.com",
  "pdu_id":"a4ecee13e2accdadf56c1025af232176",
  "origin_server_ts":1404838188000,
  "pdu_type":"m.room.message",
  "prev_pdus":[
    ["blue.example.com","99d16afbc8",
        {"sha256":"abase64encodedsha256hashshouldbe43byteslong"}]
  ],
  "hashes":{"sha256":"thishashcoversallfieldsincasethisisredacted"},
  "signatures":{
    "green.example.com":{
      "ed25519:key_version:":"these86bytesofbase64signaturecoveressentialfieldsincludinghashessocancheckredactedpdus"
    }
  },
  "is_state":false,
  "content": {...}
 }

In contrast to Transactions, it is important to note that the ``prev_pdus``
field of a PDU refers to PDUs that any origin server has sent, rather than
previous IDs that this ``origin`` has sent. This list may refer to other PDUs
sent by the same origin as the current one, or other origins.

Because of the distributed nature of participants in a Matrix conversation, it
is impossible to establish a globally-consistent total ordering on the events.
However, by annotating each outbound PDU at its origin with IDs of other PDUs
it has received, a partial ordering can be constructed allowing causality
relationships to be preserved. A client can then display these messages to the
end-user in some order consistent with their content and ensure that no message
that is semantically in reply of an earlier one is ever displayed before it.

State Update PDU Fields
~~~~~~~~~~~~~~~~~~~~~~~

PDUs fall into two main categories: those that deliver Events, and those that
synchronise State. For PDUs that relate to State synchronisation, additional
keys exist to support this:

======================== ============ =========================================
 Key                      Type         Description
======================== ============ =========================================
``state_key``            String       Combined with the ``pdu_type`` this
                                      identifies the which part of the room
                                      state is updated
``required_power_level`` Integer      The required power level needed to
                                      replace this update.
``prev_state_id``        String       The homeserver of the update this
                                      replaces
``prev_state_origin``    String       The PDU id of the update this replaces.
``user_id``              String       The user updating the state.
======================== ============ =========================================

.. code:: json

 {...,
  "is_state":true,
  "state_key":TODO-doc
  "required_power_level":TODO-doc
  "prev_state_id":TODO-doc
  "prev_state_origin":TODO-doc
 }


EDUs
----

EDUs, by comparison to PDUs, do not have an ID, a context, or a list of
"previous" IDs. The only mandatory fields for these are the type, origin and
destination home server names, and the actual nested content.

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


To fetch a particular PDU::

  GET .../pdu/<origin>/<pdu_id>/
    Response: JSON encoding of a single Transaction containing one PDU

Retrieves a given PDU from the server. The response will contain a single new
Transaction, inside which will be the requested PDU.


To fetch all the state of a given context::

  GET .../state/<context>/
    Response: JSON encoding of a single Transaction containing multiple PDUs

Retrieves a snapshot of the entire current state of the given context. The
response will contain a single Transaction, inside which will be a list of PDUs
that encode the state.

To backfill events on a given context::

  GET .../backfill/<context>/
    Query args: v, limit
    Response: JSON encoding of a single Transaction containing multiple PDUs

Retrieves a sliding-window history of previous PDUs that occurred on the given
context. Starting from the PDU ID(s) given in the "v" argument, the PDUs that
preceeded it are retrieved, up to a total number given by the "limit" argument.
These are then returned in a new Transaction containing all of the PDUs.


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

Performs a single query request on the receiving home server. The Query Type
part of the path specifies the kind of query being made, and its query
arguments have a meaning specific to that kind of query. The response is a
JSON-encoded object whose meaning also depends on the kind of query.

Backfilling
-----------
.. NOTE::
  This section is a work in progress.

.. TODO-doc
  - What it is, when is it used, how is it done


Authentication
--------------

Request Authentication
~~~~~~~~~~~~~~~~~~~~~~

Every HTTP request made by a homeserver is authenticated using public key
digital signatures. The request method, target and body are signed by wrapping
them in a JSON object and signing it using the JSON signing algorithm. The
resulting signatures are added as an Authorization header with an auth scheme
of X-Matrix.

Note that the target field should include the full path starting with
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
        "content": { JSON content ... },
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

    { JSON content ... }


Example python code:

.. code:: python

    def authorization_headers(origin_name, origin_signing_key,
                              destination_name, request_method, request_target,
                              content_json=None):
        request_json = {
             "method": request_method,
             "uri": request_target,
             "origin": origin_name,
             "destination": destination_name,
        }

        if content_json is not None:
            request["content"] = content_json

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

A home server may provide a TLS client certficate and the receiving home server
may check that the client certificate matches the certificate of the origin
home server.

Server-Server Authorization
---------------------------

.. TODO-doc
  - PDU signing (see the Event signing section earlier)
  - State conflict resolution (see below)

State Conflict Resolution
-------------------------
.. NOTE::
  This section is a work in progress.
  
.. TODO-doc
  - How do conflicts arise (diagrams?)
  - How are they resolved (incl tie breaks)
  - How does this work with deleting current state
  - How do we reject invalid federation traffic?

[[TODO(paul): At this point we should probably have a long description of how
State management works, with descriptions of clobbering rules, power levels, etc
etc... But some of that detail is rather up-in-the-air, on the whiteboard, and
so on. This part needs refining. And writing in its own document as the details
relate to the server/system as a whole, not specifically to server-server
federation.]]

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
        status_msg: (optional) string of freeform text
        last_active_ago: miliseconds since the last activity by the user

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
the orginal EDU's ``poll`` list.

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
  - Explain the timing-based roundtrip reduction mechanism for presence
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
    displayname: string of freeform text
    avatar_url: string containing an http-scheme URL

If the query contains the optional ``field`` key, it should give the name of a
result field. If such is present, then the result should contain only a field
of that name, with no others present. If not, the result should contain as much
of the user's profile as the home server has available and can make public.

Directory
---------

The server API for directory queries is also based on Federation Queries.

Querying directory information::

  Query type: directory

  Arguments:
    room_alias: the room alias to query

  Returns: JSON object containing the following keys:
    room_id: string giving the underlying room ID the alias maps to
    servers: list of strings giving the join candidates

The list of join candidates is a list of server names that are likely to hold
the given room; these are servers that the requesting server may wish to try
joining with. This list may or may not include the server answering the query.
