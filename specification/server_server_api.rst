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

Changelog
---------

.. topic:: Version: %SERVER_RELEASE_LABEL%
{{server_server_changelog}}

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

For the full historical changelog, see
https://github.com/matrix-org/matrix-doc/blob/master/changelogs/server_server.rst


Other versions of this specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following other versions are also available, in reverse chronological order:

- `HEAD <https://matrix.org/docs/spec/server_server/unstable.html>`_: Includes all changes since the latest versioned release.

Server discovery
----------------

Resolving server names
~~~~~~~~~~~~~~~~~~~~~~

Each matrix homeserver is identified by a server name consisting of a hostname
and an optional port, as described by the `grammar
<../appendices.html#server-name>`_.  Server names should be resolved to an IP
address and port using the following process:

* If the hostname is an IP literal, then that IP address should be used,
  together with the given port number, or 8448 if no port is given.

* Otherwise, if the port is present, then an IP address is discovered by
  looking up an AAAA or A record for the hostname, and the specified port is
  used.

* If the hostname is not an IP literal and no port is given, the server is
  discovered by first looking up a ``_matrix._tcp`` SRV record for the
  hostname, which may give a hostname (to be looked up using AAAA or A queries)
  and port.  If the SRV record does not exist, then the server is discovered by
  looking up an AAAA or A record on the hostname and taking the default
  fallback port number of 8448.

  Homeservers may use SRV records to load balance requests between multiple TLS
  endpoints or to failover to another endpoint if an endpoint fails.

When making requests to servers, use the hostname of the target server in the
``Host`` header, regardless of any hostname given in the SRV record. For
example, if the server name is ``example.org``, and the SRV record resolves to
``matrix.example.org``, the ``Host`` header in the request should be
``example.org``.  If an explicit port was given in the server name, it should be
included in the ``Host`` header; otherwise, no port number should be given in
the ``Host`` header.

Server implementation
~~~~~~~~~~~~~~~~~~~~~~

{{version_ss_http_api}}

Retrieving server keys
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

Transactions are limited in size; they can have at most 50 PDUs and 100 EDUs.

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

.. _`auth events selection`:

The ``auth_events`` field of a PDU identifies the set of events which give the
sender permission to send the event. The ``auth_events`` for the
``m.room.create`` event in a room is empty; for other events, it should be the
following subset of the room state:

- The ``m.room.create`` event.
- The current ``m.room.power_levels`` event, if any.
- The sender's current ``m.room.member`` event, if any.
- If type is ``m.room.member``:

    - The target's current ``m.room.member`` event, if any.
    - If ``membership`` is ``join`` or ``invite``, the current
      ``m.room.join_rules`` event, if any.
    - If membership is ``invite`` and ``content`` contains a
      ``third_party_invite`` property, the current
      ``m.room.third_party_invite`` event with ``state_key`` matching
      ``content.third_party_invite.signed.token``, if any.

{{definition_ss_pdu}}

Checks performed on receipt of a PDU
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Whenever a server receives an event from a remote server, the receiving server
must ensure that the event:

1. Is a valid event, otherwise it is dropped.
2. Passes signature checks, otherwise it is dropped.
3. Passes hash checks, otherwise it is redacted before being processed
   further.
4. Passes authorization rules based on the event's auth events, otherwise it
   is rejected.
5. Passes authorization rules based on the state at the event, otherwise it
   is rejected.
6. Passes authorization rules based on the current state of the room, otherwise it
   is "soft failed".

Further details of these checks, and how to handle failures, are described
below.


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

Authorization rules
+++++++++++++++++++

The rules governing whether an event is authorized depends on a set of state. A
given event is checked multiple times against different sets of state, as
specified above. The types of state events that affect authorization are:

- ``m.room.create``
- ``m.room.member``
- ``m.room.join_rules``
- ``m.room.power_levels``
- ``m.room.third_party_invite``

The rules are as follows:

1. If type is ``m.room.create``:

   a. If it has any previous events, reject.
   b. If the domain of the ``room_id`` does not match the domain of the
      ``sender``, reject.
   c. If ``content.room_version`` is present and is not a recognised version,
      reject.
   d. If ``content`` has no ``creator`` field, reject.
   e. Otherwise, allow.

#. Reject if event has ``auth_events`` that:

   a. have duplicate entries for a given ``type`` and ``state_key`` pair
   #. have entries whose ``type`` and ``state_key`` don't match those
      specified by the `auth events selection`_ algorithm described above.

#. If event does not have a ``m.room.create`` in its ``auth_events``, reject.

#. If type is ``m.room.aliases``:

   a. If event has no ``state_key``, reject.
   b. If sender's domain doesn't matches ``state_key``, reject.
   c. Otherwise, allow.

#. If type is ``m.room.member``:

   a. If no ``state_key`` key or ``membership`` key in ``content``, reject.

   #. If ``membership`` is ``join``:

      i. If the only previous event is an ``m.room.create``
         and the ``state_key`` is the creator, allow.

      #. If the ``sender`` does not match ``state_key``, reject.

      #. If the ``sender`` is banned, reject.

      #. If the ``join_rule`` is ``invite`` then allow if membership state
         is ``invite`` or ``join``.

      #. If the ``join_rule`` is ``public``, allow.

      #. Otherwise, reject.

   #. If ``membership`` is ``invite``:

      i. If ``content`` has ``third_party_invite`` key:

         #. If *target user* is banned, reject.

         #. If ``content.third_party_invite`` does not have a
            ``signed`` key, reject.

         #. If ``signed`` does not have ``mxid`` and ``token`` keys, reject.

         #. If ``mxid`` does not match ``state_key``, reject.

         #. If there is no ``m.room.third_party_invite`` event in the
            current room state with ``state_key`` matching ``token``, reject.

         #. If ``sender`` does not match ``sender`` of the
            ``m.room.third_party_invite``, reject.

         #. If any signature in ``signed`` matches any public key in the
            ``m.room.third_party_invite`` event, allow. The public keys are
            in ``content`` of ``m.room.third_party_invite`` as:

            #. A single public key in the ``public_key`` field.
            #. A list of public keys in the ``public_keys`` field.

         #. Otherwise, reject.

      #. If the ``sender``'s current membership state is not ``join``, reject.

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

#. If type is ``m.room.third_party_invite``:

   a. Allow if and only if ``sender``'s current power level is greater than
      or equal to the *invite level*.

#. If the event type's *required power level* is greater than the ``sender``'s power
   level, reject.

#. If the event has a ``state_key`` that starts with an ``@`` and does not match
   the ``sender``, reject.

#. If type is ``m.room.power_levels``:

   a. If ``users`` key in ``content`` is not a dictionary with keys that are
      valid user IDs with values that are integers (or a string that is an
      integer), reject.

   #. If there is no previous ``m.room.power_levels`` event in the room, allow.

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

   a. If the ``sender``'s power level is greater than or equal to the *redact
      level*, allow.

   #. If the domain of the ``event_id`` of the event being redacted is the same
      as the domain of the ``event_id`` of the ``m.room.redaction``, allow.

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


Rejection
+++++++++

If an event is rejected it should neither be relayed to clients nor be included
as a prev event in any new events generated by the server. Subsequent events
from other servers that reference rejected events should be allowed if they
still pass the auth rules. The state used in the checks should be calculated as
normal, except not updating with the rejected event where it is a state event.

If an event in an incoming transaction is rejected, this should not cause the
transaction request to be responded to with an error response.

.. NOTE::

    This means that events may be included in the room DAG even though they
    should be rejected.

.. NOTE::

    This is in contrast to redacted events which can still affect the
    state of the room. For example, a redacted ``join`` event will still
    result in the user being considered joined.


Soft failure
++++++++++++

.. admonition:: Rationale

  It is important that we prevent users from evading bans (or other power
  restrictions) by creating events which reference old parts of the DAG. For
  example, a banned user could continue to send messages to a room by having
  their server send events which reference the event before they were banned.
  Note that such events are entirely valid, and we cannot simply reject them, as
  it is impossible to distinguish such an event from a legitimate one which has
  been delayed. We must therefore accept such events and let them participate in
  state resolution and the federation protocol as normal. However, servers may
  choose not to send such events on to their clients, so that end users won't
  actually see the events.

  When this happens it is often fairly obvious to servers, as they can see that
  the new event doesn't actually pass auth based on the "current state" (i.e.
  the resolved state across all forward extremities). While the event is
  technically valid, the server can choose to not notify clients about the new
  event.

  This discourages servers from sending events that evade bans etc. in this way,
  as end users won't actually see the events.


When the homeserver receives a new event over federation it should also check
whether the event passes auth checks based on the current state of the room (as
well as based on the state at the event). If the event does not pass the auth
checks based on the *current state* of the room (but does pass the auth checks
based on the state at that event) it should be "soft failed".

When an event is "soft failed" it should not be relayed to the client nor be
referenced by new events created by the homeserver (i.e. they should not be
added to the server's list of forward extremities of the room). Soft failed
events are otherwise handled as usual.


.. NOTE::

  Soft failed events participate in state resolution as normal if further events
  are received which reference it. It is the job of the state resolution
  algorithm to ensure that malicious events cannot be injected into the room
  state via this mechanism.


.. NOTE::

  Because soft failed state events participate in state resolution as normal, it
  is possible for such events to appear in the current state of the room. In
  that case the client should be told about the soft failed event in the usual
  way (e.g. by sending it down in the ``state`` section of a sync response).


.. NOTE::

  A soft failed event should be returned in response to federation requests
  where appropriate (e.g. in ``/event/<event_id>``). Note that soft failed
  events are returned in ``/backfill`` and ``/get_missing_events`` responses
  only if the requests include events referencing the soft failed events.


.. admonition:: Example

  As an example consider the event graph::

      A
     /
    B

  where ``B`` is a ban of a user ``X``. If the user ``X`` tries to set the topic
  by sending an event ``C`` while evading the ban::

      A
     / \
    B   C

  servers that receive ``C`` after ``B`` should soft fail event ``C``, and so
  will neither relay ``C`` to its clients nor send any events referencing ``C``.

  If later another server sends an event ``D`` that references both ``B`` and
  ``C`` (this can happen if it received ``C`` before ``B``)::

      A
     / \
    B   C
     \ /
      D

  then servers will handle ``D`` as normal. ``D`` is sent to the servers'
  clients (assuming ``D`` passes auth checks). The state at ``D`` may resolve to
  a state that includes ``C``, in which case clients should also to be told that
  the state has changed to include ``C``. (*Note*: This depends on the exact
  state resolution algorithm used. In the original version of the algorithm
  ``C`` would be in the resolved state, whereas in latter versions the algorithm
  tries to prioritise the ban over the topic change.)

  Note that this is essentially equivalent to the situation where one server
  doesn't receive ``C`` at all, and so asks another server for the state of the
  ``C`` branch.

  Let's go back to the graph before ``D`` was sent::

      A
     / \
    B   C

  If all the servers in the room saw ``B`` before ``C`` and so soft fail ``C``,
  then any new event ``D'`` will not reference ``C``::

      A
     / \
    B   C
    |
    D


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

Servers should follow one of the following recursively-defined algorithms,
depending on the room version, to determine the room state at a given point on
the DAG.

State resolution algorithm for version 2 rooms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The room state :math:`S'(E)` after an event :math:`E` is defined in terms of
the room state :math:`S(E)` before :math:`E`, and depends on whether
:math:`E` is a state event or a message event:

* If :math:`E` is a message event, then :math:`S'(E) = S(E)`.

* If :math:`E` is a state event, then :math:`S'(E)` is :math:`S(E)`, except
  that its entry corresponding to :math:`E`'s ``event_type`` and ``state_key``
  is replaced by :math:`E`'s ``event_id``.

The room state :math:`S(E)` before :math:`E` is the *resolution* of the set of
states :math:`\{ S'(E_1), S'(E_2), … \}` consisting of the states after each of
:math:`E`'s ``prev_event``\s :math:`\{ E_1, E_2, … \}`, where the resolution of
a set of states is given in the algorithm below.

Definitions
+++++++++++

The state resolution algorithm for version 2 rooms uses the following
definitions, given the set of room states :math:`\{ S_1, S_2, \ldots \}`:

Power events
  A *power event* is a state event with type ``m.room.power_levels`` or
  ``m.room.join_rules``, or a state event with type ``m.room.member`` where the
  ``membership`` is ``leave`` or ``ban`` and the ``sender`` does not match the
  ``state_key``. The idea behind this is that power events are events that have
  may remove someone's ability to do something in the room.

Unconflicted state map and conflicted state set
  The *unconflicted state map* is the state where the value of each key exists
  and is the same in each state :math:`S_i`.  The *conflicted state set* is the
  set of all other state events. Note that the unconflicted state map only has
  one event per ``(event_type, state_key)``, whereas the conflicted state set
  may have multiple events.

Auth difference
  The *auth difference* is calculated by first calculating the full auth chain
  for each state :math:`S_i`, that is the union of the auth chains for each
  event in :math:`S_i`, and then taking every event that doesn't appear in
  every auth chain. If :math:`C_i` is the full auth chain of :math:`S_i`, then
  the auth difference is :math:`\cup C_i - \cap C_i`.

Full conflicted set
  The *full conflicted set* is the union of the conflicted state set and the
  auth difference.

Reverse topological power ordering
  The *reverse topological power ordering* of a set of events is the
  lexicographically smallest topological ordering based on the DAG formed by
  auth events. The reverse topological power ordering is ordered from earliest
  event to latest. For comparing two topological orderings to determine which
  is the lexicographically smallest, the following comparison relation on
  events is used: for events :math:`x` and :math:`y`, :math:`x<y` if

  1. :math:`x`'s sender has *greater* power level than :math:`y`'s sender,
     when looking at their respective ``auth_event``\s; or
  2. the senders have the same power level, but :math:`x`'s
     ``origin_server_ts`` is *less* than :math:`y`'s ``origin_server_ts``; or
  3. the senders have the same power level and the events have the same
     ``origin_server_ts``, but :math:`x`'s ``event_id`` is *less* than
     :math:`y`'s ``event_id``.

  The reverse topological power ordering can be found by sorting the events
  using Kahn's algorithm for topological sorting, and at each step selecting,
  among all the candidate vertices, the smallest vertex using the above
  comparison relation.

Mainline ordering
  Given an ``m.room.power_levels`` event :math:`P`, the *mainline of* :math:`P`
  is the list of events generated by starting with :math:`P` and recursively
  taking the ``m.room.power_levels`` events from the ``auth_events``, ordered
  such that :math:`P` is last. Given another event :math:`e`, the *closest
  mainline event to* :math:`e` is the first event encountered in the mainline
  when iteratively descending through the ``m.room.power_levels`` events in the
  ``auth_events`` starting at :math:`e`. If no mainline event is encountered
  when iteratively descending through the ``m.room.power_levels`` events, then
  the closest mainline event to :math:`e` can be considered to be a dummy event
  that is before any other event in the mainline of :math:`P` for the purposes
  of condition 1 below.

  The *mainline ordering based on* :math:`P` of a set of events is the
  ordering, from smallest to largest, using the following comparision relation
  on events: for events :math:`x` and :math:`y`, :math:`x<y` if

  1. the closest mainline event to :math:`x` appears *before* the closest
     mainline event to :math:`y`; or
  2. the closest mainline events are the same, but :math:`x`\'s
     ``origin_server_ts`` is *less* than :math:`y`\'s ``origin_server_ts``; or
  3. the closest mainline events are the same and the events have the same
     ``origin_server_ts``, but :math:`x`\'s ``event_id`` is *less* than
     :math:`y`\'s ``event_id``.

Iterative auth checks
  The *iterative auth checks algorithm* takes as input an initial room state
  and a sorted list of state events, and constructs a new room state by
  iterating through the event list and applying the state event to the room
  state if the state event is allowed by the `authorization rules`_. If the
  state event is not allowed by the authorization rules, then the event is
  ignored. If a ``(event_type, state_key)`` key that is required for checking
  the authorization rules is not present in the state, then the appropriate
  state event from the event's ``auth_events`` is used.

Algorithm
+++++++++

The *resolution* of a set of states is obtained as follows:

1. Take all *power events* and any events in their auth chains, recursively,
   that appear in the *full conflicted set* and order them by the *reverse
   topological power ordering*.
2. Apply the *iterative auth checks algorithm* on the *unconflicted state map*
   and the list of events from the previous step to get a partially resolved
   state.
3. Take all remaining events that weren't picked in step 1 and order them by
   the mainline ordering based on the power level in the partially resolved
   state obtained in step 2.
4. Apply the *iterative auth checks algorithm* on the partial resolved
   state and the list of events from the previous step.
5. Update the result by replacing any event with the event with the same key
   from the *unconflicted state map*, if such an event exists, to get the final
   resolved state.

State resolution algorithm for version 1 rooms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

.. NOTE::
   More information about third party invites is available in the `Client-Server API`_
   under the Third Party Invites module.

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

To complement the `Client-Server API`_'s room directory, homeservers need a
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

Servers should only send presence updates for users that the receiving server
would be interested in. This can include the receiving server sharing a room
with a given user, or a user on the receiving server has added one of the
sending server's users to their presence list.

Clients may define lists of users that they are interested in via "Presence
Lists" through the `Client-Server API`_. When users are added to a presence
list, a ``m.presence_invite`` EDU is sent to them. The user may then accept
or deny their involvement in the list by sending either an ``m.presence_accept``
or ``m.presence_deny`` EDU back.

.. TODO-doc
  - Explain the timing-based round-trip reduction mechanism for presence
    messages
  - Explain the zero-byte presence inference logic
  See also: docs/client-server/model/presence

{{definition_ss_event_schemas_m_presence}}

{{definition_ss_event_schemas_m_presence_invite}}

{{definition_ss_event_schemas_m_presence_accept}}

{{definition_ss_event_schemas_m_presence_deny}}


Receipts
--------

Receipts are EDUs used to communicate a marker for a given event. Currently the
only kind of receipt supported is a "read receipt", or where in the event graph
the user has read up to.

Read receipts for events events that a user sent do not need to be sent. It is
implied that by sending the event the user has read up to the event.

{{definition_ss_event_schemas_m_receipt}}

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

Device Management
-----------------

Details of a user's devices must be efficiently published to other users and kept
up-to-date.  This is critical for reliable end-to-end encryption, in order for users
to know which devices are participating in a room.  It's also required for to-device
messaging to work. This section is intended to complement the `Device Management module`_
of the Client-Server API.

Matrix currently uses a custom pubsub system for synchronising information
about the list of devices for a given user over federation.  When a server
wishes to determine a remote user's device list for the first time,
it should populate a local cache from the result of a ``/user/keys/query`` API
on the remote server.  However, subsequent updates to the cache should be applied
by consuming ``m.device_list_update`` EDUs.  Each new ``m.device_list_update`` EDU
describes an incremental change to one device for a given user which should replace
any existing entry in the local server's cache of that device list. Servers must send
``m.device_list_update`` EDUs to all the servers who share a room with a given
local user, and must be sent whenever that user's device list changes (i.e. for new or
deleted devices, when that user joins a room which contains servers which are not
already receiving updates for that user's device list, or changes in device information
such as the device's human-readable name).

Servers send ``m.device_list_update`` EDUs in a sequence per origin user, each with
a unique ``stream_id``.  They also include a pointer to the most recent previous EDU(s)
that this update is relative to in the ``prev_id`` field.  To simplify implementation
for clustered servers which could send multiple EDUs at the same time, the ``prev_id``
field should include all ``m.device_list_update`` EDUs which have not been yet been
referenced in a EDU. If EDUs are emitted in series by a server, there should only ever
be one ``prev_id`` in the EDU.

This forms a simple directed acyclic graph of ``m.device_list_update`` EDUs, showing
which EDUs a server needs to have received in order to apply an update to its local
copy of the remote user's device list.  If a server receives an EDU which refers to
a ``prev_id`` it does not recognise, it must resynchronise its list by calling the
``/user/keys/query API`` and resume the process.  The response contains a ``stream_id``
which should be used to correlate with subsequent ``m.device_list_update`` EDUs.

.. TODO: this whole thing desperately feels like it should just be state in a room,
  rather than inventing a whole different DAG.  The same room could be used for
  profiles, presence lists, etc.

{{user_devices_ss_http_api}}

{{definition_ss_event_schemas_m_device_list_update}}


End-to-End Encryption
---------------------

This section complements the `End-to-End Encryption module`_ of the Client-Server
API. For detailed information about end-to-end encryption, please see that module.

The APIs defined here are designed to be able to proxy much of the client's request
through to federation, and have the response also be proxied through to the client.

{{user_keys_ss_http_api}}


Send-to-device messaging
------------------------

.. TODO: add modules to the federation spec and make this a module

The server API for send-to-device messaging is based on the
``m.direct_to_device`` EDU. There are no PDUs or Federation Queries involved.

Each send-to-device message should be sent to the destination server using
the following EDU:

{{definition_ss_event_schemas_m_direct_to_device}}


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


Server Access Control Lists (ACLs)
----------------------------------

Server ACLs and their purpose are described in the `Server ACLs`_ section of the
Client-Server API.

When a remote server makes a request, it MUST be verified to be allowed by the
server ACLs. If the server is denied access to a room, the receiving server
MUST reply with a 403 HTTP status code and an ``errcode`` of ``M_FORBIDDEN``.

The following endpoint prefixes MUST be protected:

* ``/_matrix/federation/v1/send`` (on a per-PDU basis)
* ``/_matrix/federation/v1/make_join``
* ``/_matrix/federation/v1/make_leave``
* ``/_matrix/federation/v1/send_join``
* ``/_matrix/federation/v1/send_leave``
* ``/_matrix/federation/v1/invite``
* ``/_matrix/federation/v1/state``
* ``/_matrix/federation/v1/state_ids``
* ``/_matrix/federation/v1/backfill``
* ``/_matrix/federation/v1/event_auth``
* ``/_matrix/federation/v1/query_auth``
* ``/_matrix/federation/v1/get_missing_events``


Signing Events
--------------

Signing events is complicated by the fact that servers can choose to redact
non-essential parts of an event.

Adding hashes and signatures to outgoing events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before signing the event, the *content hash* of the event is calculated as
described below. The hash is encoded using `Unpadded Base64`_ and stored in the
event object, in a ``hashes`` object, under a ``sha256`` key.

The event object is then *redacted*, following the `redaction
algorithm`_. Finally it is signed as described in `Signing JSON`_, using the
server's signing key (see also `Retrieving server keys`_).

The signature is then copied back to the original event object.

See `Persistent Data Unit schema`_ for an example of a signed event.


Validating hashes and signatures on received events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When a server receives an event over federation from another server, the
receiving server should check the hashes and signatures on that event.

First the signature is checked. The event is redacted following the `redaction
algorithm`_, and the resultant object is checked for a signature from the
originating server, following the algorithm described in `Checking for a signature`_.
Note that this step should succeed whether we have been sent the full event or
a redacted copy.

If the signature is found to be valid, the expected content hash is calculated
as described below. The content hash in the ``hashes`` property of the received
event is base64-decoded, and the two are compared for equality.

If the hash check fails, then it is assumed that this is because we have only
been given a redacted version of the event. To enforce this, the receiving
server should use the redacted copy it calculated rather than the full copy it
received.

Calculating the content hash for an event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *content hash* of an event covers the complete event including the
*unredacted* contents. It is calculated as follows.

First, any existing ``unsigned``, ``signature``, and ``hashes`` members are
removed. The resulting object is then encoded as `Canonical JSON`_, and the
JSON is hashed using SHA-256.


Example code
~~~~~~~~~~~~

.. code:: python

    def hash_and_sign_event(event_object, signing_key, signing_name):
        # First we need to hash the event object.
        content_hash = compute_content_hash(event_object)
        event_object["hashes"] = {"sha256": encode_unpadded_base64(content_hash)}

        # Strip all the keys that would be removed if the event was redacted.
        # The hashes are not stripped and cover all the keys in the event.
        # This means that we can tell if any of the non-essential keys are
        # modified or removed.
        stripped_object = strip_non_essential_keys(event_object)

        # Sign the stripped JSON object. The signature only covers the
        # essential keys and the hashes. This means that we can check the
        # signature even if the event is redacted.
        signed_object = sign_json(stripped_object, signing_key, signing_name)

        # Copy the signatures from the stripped event to the original event.
        event_object["signatures"] = signed_object["signatures"]

    def compute_content_hash(event_object):
        # take a copy of the event before we remove any keys.
        event_object = dict(event_object)

        # Keys under "unsigned" can be modified by other servers.
        # They are useful for conveying information like the age of an
        # event that will change in transit.
        # Since they can be modifed we need to exclude them from the hash.
        event_object.pop("unsigned", None)

        # Signatures will depend on the current value of the "hashes" key.
        # We cannot add new hashes without invalidating existing signatures.
        event_object.pop("signatures", None)

        # The "hashes" key might contain multiple algorithms if we decide to
        # migrate away from SHA-2. We don't want to include an existing hash
        # output in our hash so we exclude the "hashes" dict from the hash.
        event_object.pop("hashes", None)

        # Encode the JSON using a canonical encoding so that we get the same
        # bytes on every server for the same JSON object.
        event_json_bytes = encode_canonical_json(event_object)

        return hashlib.sha256(event_json_bytes)

.. TODO

   [[TODO(markjh): Since the ``hash`` object cannot be redacted a server
   shouldn't allow too many hashes to be listed, otherwise a server might embed
   illict data within the ``hash`` object.

   We might want to specify a maximum number of keys for the
   ``hash`` and we might want to specify the maximum output size of a hash]]

   [[TODO(markjh) We might want to allow the server to omit the output of well
   known hash functions like SHA-256 when none of the keys have been redacted]]


.. |/query/directory| replace:: ``/query/directory``
.. _/query/directory: #get-matrix-federation-v1-query-directory

.. _`Invitation storage`: ../identity_service/%IDENTITY_RELEASE_LABEL%.html#invitation-storage
.. _`Identity Service API`: ../identity_service/%IDENTITY_RELEASE_LABEL%.html
.. _`Client-Server API`: ../client_server/%CLIENT_RELEASE_LABEL%.html
.. _`Inviting to a room`: #inviting-to-a-room
.. _`Canonical JSON`: ../appendices.html#canonical-json
.. _`Unpadded Base64`:  ../appendices.html#unpadded-base64
.. _`Server ACLs`:  ../client_server/%CLIENT_RELEASE_LABEL%.html#module-server-acls
.. _`redaction algorithm`: ../client_server/%CLIENT_RELEASE_LABEL%.html#redactions
.. _`Signing JSON`: ../appendices.html#signing-json
.. _`Checking for a signature`: ../appendices.html#checking-for-a-signature
.. _`Device Management module`: ../client_server/%CLIENT_RELEASE_LABEL%.html#device-management
.. _`End-to-End Encryption module`: ../client_server/%CLIENT_RELEASE_LABEL%.html#end-to-end-encryption
