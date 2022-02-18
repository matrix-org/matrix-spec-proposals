---
title: "Server-Server API"
weight: 20
type: docs
---

Matrix homeservers use the Federation APIs (also known as server-server
APIs) to communicate with each other. Homeservers use these APIs to push
messages to each other in real-time, to retrieve historic messages from
each other, and to query profile and presence information about users on
each other's servers.

The APIs are implemented using HTTPS requests between each of the
servers. These HTTPS requests are strongly authenticated using public
key signatures at the TLS transport layer and using public key
signatures in HTTP Authorization headers at the HTTP layer.

There are three main kinds of communication that occur between
homeservers:

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
servers, initiated by one side sending an HTTPS GET request to obtain
some information, and responded by the other. They are not persisted and
contain no long-term significant history. They simply request a snapshot
state at the instant the query is made.

EDUs and PDUs are further wrapped in an envelope called a Transaction,
which is transferred from the origin to the destination homeserver using
an HTTPS PUT request.

## API standards

The mandatory baseline for client-server communication in Matrix is
exchanging JSON objects over HTTP APIs. More efficient optional
transports will in future be supported as optional extensions - e.g. a
packed binary encoding over stream-cipher encrypted TCP socket for
low-bandwidth/low-roundtrip mobile usage. For the default HTTP
transport, all API calls use a Content-Type of `application/json`. In
addition, all strings MUST be encoded as UTF-8.

## Server discovery

### Resolving server names

Each Matrix homeserver is identified by a server name consisting of a
hostname and an optional port, as described by the
[grammar](/appendices#server-name). Where applicable, a delegated
server name uses the same grammar.

Server names are resolved to an IP address and port to connect to, and
have various conditions affecting which certificates and `Host` headers
to send. The process overall is as follows:

1.  If the hostname is an IP literal, then that IP address should be
    used, together with the given port number, or 8448 if no port is
    given. The target server must present a valid certificate for the IP
    address. The `Host` header in the request should be set to the
    server name, including the port if the server name included one.
2.  If the hostname is not an IP literal, and the server name includes
    an explicit port, resolve the IP address using AAAA or A records.
    Requests are made to the resolved IP address and given port with a
    `Host` header of the original server name (with port). The target
    server must present a valid certificate for the hostname.
3.  If the hostname is not an IP literal, a regular HTTPS request is
    made to `https://<hostname>/.well-known/matrix/server`, expecting
    the schema defined later in this section. 30x redirects should be
    followed, however redirection loops should be avoided. Responses
    (successful or otherwise) to the `/.well-known` endpoint should be
    cached by the requesting server. Servers should respect the cache
    control headers present on the response, or use a sensible default
    when headers are not present. The recommended sensible default is 24
    hours. Servers should additionally impose a maximum cache time for
    responses: 48 hours is recommended. Errors are recommended to be
    cached for up to an hour, and servers are encouraged to
    exponentially back off for repeated failures. The schema of the
    `/.well-known` request is later in this section. If the response is
    invalid (bad JSON, missing properties, non-200 response, etc), skip
    to step 4. If the response is valid, the `m.server` property is
    parsed as `<delegated_hostname>[:<delegated_port>]` and processed as
    follows:
    -   If `<delegated_hostname>` is an IP literal, then that IP address
        should be used together with the `<delegated_port>` or 8448 if
        no port is provided. The target server must present a valid TLS
        certificate for the IP address. Requests must be made with a
        `Host` header containing the IP address, including the port if
        one was provided.
    -   If `<delegated_hostname>` is not an IP literal, and
        `<delegated_port>` is present, an IP address is discovered by
        looking up an AAAA or A record for `<delegated_hostname>`. The
        resulting IP address is used, alongside the `<delegated_port>`.
        Requests must be made with a `Host` header of
        `<delegated_hostname>:<delegated_port>`. The target server must
        present a valid certificate for `<delegated_hostname>`.
    -   If `<delegated_hostname>` is not an IP literal and no
        `<delegated_port>` is present, an SRV record is looked up for
        `_matrix._tcp.<delegated_hostname>`. This may result in another
        hostname (to be resolved using AAAA or A records) and port.
        Requests should be made to the resolved IP address and port with
        a `Host` header containing the `<delegated_hostname>`. The
        target server must present a valid certificate for
        `<delegated_hostname>`.
    -   If no SRV record is found, an IP address is resolved using AAAA
        or A records. Requests are then made to the resolve IP address
        and a port of 8448, using a `Host` header of
        `<delegated_hostname>`. The target server must present a valid
        certificate for `<delegated_hostname>`.
4.  If the `/.well-known` request resulted in an error response, a
    server is found by resolving an SRV record for
    `_matrix._tcp.<hostname>`. This may result in a hostname (to be
    resolved using AAAA or A records) and port. Requests are made to the
    resolved IP address and port, using 8448 as a default port, with a
    `Host` header of `<hostname>`. The target server must present a
    valid certificate for `<hostname>`.
5.  If the `/.well-known` request returned an error response, and the
    SRV record was not found, an IP address is resolved using AAAA and A
    records. Requests are made to the resolved IP address using port
    8448 and a `Host` header containing the `<hostname>`. The target
    server must present a valid certificate for `<hostname>`.

{{% boxes/note %}}
The reasons we require `<hostname>` rather than `<delegated_hostname>` for SRV
delegation are:
  1. DNS is insecure (not all domains have DNSSEC), so the target of the delegation
      must prove that it is a valid delegate for `<hostname>` via TLS.
  2. Consistency with the recommendations in [RFC6125](https://datatracker.ietf.org/doc/html/rfc6125#section-6.2.1)
     and other applications using SRV records such [XMPP](https://datatracker.ietf.org/doc/html/rfc6120#section-13.7.2.1).
{{% /boxes/note %}}

The TLS certificate provided by the target server must be signed by a
known Certificate Authority. Servers are ultimately responsible for
determining the trusted Certificate Authorities, however are strongly
encouraged to rely on the operating system's judgement. Servers can
offer administrators a means to override the trusted authorities list.
Servers can additionally skip the certificate validation for a given
whitelist of domains or netmasks for the purposes of testing or in
networks where verification is done elsewhere, such as with `.onion`
addresses. Servers should respect SNI when making requests where
possible: a SNI should be sent for the certificate which is expected,
unless that certificate is expected to be an IP address in which case
SNI is not supported and should not be sent.

Servers are encouraged to make use of the [Certificate
Transparency](https://www.certificate-transparency.org/) project.

{{% http-api spec="server-server" api="wellknown" %}}

### Server implementation

{{% http-api spec="server-server" api="version" %}}

### Retrieving server keys

{{% boxes/note %}}
There was once a "version 1" of the key exchange. It has been removed
from the specification due to lack of significance. It may be reviewed
[from the historical
draft](https://github.com/matrix-org/matrix-doc/blob/51faf8ed2e4a63d4cfd6d23183698ed169956cc0/specification/server_server_api.rst#232version-1).
{{% /boxes/note %}}

Each homeserver publishes its public keys under
`/_matrix/key/v2/server/{keyId}`. Homeservers query for keys by either
getting `/_matrix/key/v2/server/{keyId}` directly or by querying an
intermediate notary server using a
`/_matrix/key/v2/query/{serverName}/{keyId}` API. Intermediate notary
servers query the `/_matrix/key/v2/server/{keyId}` API on behalf of
another server and sign the response with their own key. A server may
query multiple notary servers to ensure that they all report the same
public keys.

This approach is borrowed from the [Perspectives
Project](https://web.archive.org/web/20170702024706/https://perspectives-project.org/),
but modified to include the NACL keys and to use JSON instead of XML. It
has the advantage of avoiding a single trust-root since each server is
free to pick which notary servers they trust and can corroborate the
keys returned by a given notary server by querying other servers.

#### Publishing Keys

Homeservers publish their signing keys in a JSON object at
`/_matrix/key/v2/server/{key_id}`. The response contains a list of
`verify_keys` that are valid for signing federation requests made by the
homeserver and for signing events. It contains a list of
`old_verify_keys` which are only valid for signing events.

{{% http-api spec="server-server" api="keys_server" %}}

#### Querying Keys Through Another Server

Servers may query another server's keys through a notary server. The
notary server may be another homeserver. The notary server will retrieve
keys from the queried servers through use of the
`/_matrix/key/v2/server/{keyId}` API. The notary server will
additionally sign the response from the queried server before returning
the results.

Notary servers can return keys for servers that are offline or having
issues serving their own keys by using cached responses. Keys can be
queried from multiple servers to mitigate against DNS spoofing.

{{% http-api spec="server-server" api="keys_query" %}}

## Authentication

### Request Authentication

Every HTTP request made by a homeserver is authenticated using public
key digital signatures. The request method, target and body are signed
by wrapping them in a JSON object and signing it using the JSON signing
algorithm. The resulting signatures are added as an Authorization header
with an auth scheme of `X-Matrix`. Note that the target field should
include the full path starting with `/_matrix/...`, including the `?`
and any query parameters if present, but should not include the leading
`https:`, nor the destination server's hostname.

Step 1 sign JSON:

```
{
    "method": "GET",
    "uri": "/target",
    "origin": "origin.hs.example.com",
    "destination": "destination.hs.example.com",
    "content": <JSON-parsed request body>,
    "signatures": {
        "origin.hs.example.com": {
            "ed25519:key1": "ABCDEF..."
        }
    }
}
```

The server names in the JSON above are the server names for each
homeserver involved. Delegation from the [server name resolution
section](#resolving-server-names) above do not affect these - the server
names from before delegation would take place are used. This same
condition applies throughout the request signing process.

Step 2 add Authorization header:

    GET /target HTTP/1.1
    Authorization: X-Matrix origin=origin.example.com,key="ed25519:key1",sig="ABCDEF..."
    Content-Type: application/json

    <JSON-encoded request body>

Example python code:

```py
def authorization_headers(origin_name, origin_signing_key,
                          destination_name, request_method, request_target,
                          content=None):
    request_json = {
         "method": request_method,
         "uri": request_target,
         "origin": origin_name,
         "destination": destination_name,
    }

    if content is not None:
        # Assuming content is already parsed as JSON
        request_json["content"] = content

    signed_json = sign_json(request_json, origin_name, origin_signing_key)

    authorization_headers = []

    for key, sig in signed_json["signatures"][origin_name].items():
        authorization_headers.append(bytes(
            "X-Matrix origin=%s,key=\"%s\",sig=\"%s\"" % (
                origin_name, key, sig,
            )
        ))

    return ("Authorization", authorization_headers)
```

### Response Authentication

Responses are authenticated by the TLS server certificate. A homeserver
should not send a request until it has authenticated the connected
server to avoid leaking messages to eavesdroppers.

### Client TLS Certificates

Requests are authenticated at the HTTP layer rather than at the TLS
layer because HTTP services like Matrix are often deployed behind load
balancers that handle the TLS and these load balancers make it difficult
to check TLS client certificates.

A homeserver may provide a TLS client certificate and the receiving
homeserver may check that the client certificate matches the certificate
of the origin homeserver.

## Transactions

The transfer of EDUs and PDUs between homeservers is performed by an
exchange of Transaction messages, which are encoded as JSON objects,
passed over an HTTP PUT request. A Transaction is meaningful only to the
pair of homeservers that exchanged it; they are not globally-meaningful.

Transactions are limited in size; they can have at most 50 PDUs and 100
EDUs.

{{% http-api spec="server-server" api="transactions" %}}

## PDUs

Each PDU contains a single Room Event which the origin server wants to
send to the destination.

The `prev_events` field of a PDU identifies the "parents" of the event,
and thus establishes a partial ordering on events within the room by
linking them into a Directed Acyclic Graph (DAG). The sending server
should populate this field with all of the events in the room for which
it has not yet seen a child - thus demonstrating that the event comes
after all other known events.

For example, consider a room whose events form the DAG shown below. A
server creating a new event in this room should populate the new event's
`prev_events` field with both `E4` and `E6`, since neither event yet has
a child:

    E1
    ^
    |
    E2 <--- E5
    ^       ^
    |       |
    E3      E6
    ^
    |
    E4

For a full schema of what a PDU looks like, see the [room version
specification](/rooms).

### Checks performed on receipt of a PDU

Whenever a server receives an event from a remote server, the receiving
server must ensure that the event:

1.  Is a valid event, otherwise it is dropped.
2.  Passes signature checks, otherwise it is dropped.
3.  Passes hash checks, otherwise it is redacted before being processed
    further.
4.  Passes authorization rules based on the event's auth events,
    otherwise it is rejected.
5.  Passes authorization rules based on the state at the event,
    otherwise it is rejected.
6.  Passes authorization rules based on the current state of the room,
    otherwise it is "soft failed".

Further details of these checks, and how to handle failures, are
described below.

The [Signing Events](#signing-events) section has more information on
which hashes and signatures are expected on events, and how to calculate
them.

#### Definitions

**Required Power Level** \
A given event type has an associated *required power level*. This is
given by the current `m.room.power_levels` event. The event type is
either listed explicitly in the `events` section or given by either
`state_default` or `events_default` depending on if the event is a state
event or not.

**Invite Level, Kick Level, Ban Level, Redact Level** \
The levels given by the `invite`, `kick`, `ban`, and `redact` properties
in the current `m.room.power_levels` state. Each defaults to 50 if
unspecified.

**Target User** \
For an `m.room.member` state event, the user given by the `state_key` of
the event.

#### Authorization rules

The rules governing whether an event is authorized depends on a set of
state. A given event is checked multiple times against different sets of
state, as specified above. Each room version can have a different
algorithm for how the rules work, and which rules are applied. For more
detailed information, please see the [room version
specification](/rooms).

##### Auth events selection

The `auth_events` field of a PDU identifies the set of events which give
the sender permission to send the event. The `auth_events` for the
`m.room.create` event in a room is empty; for other events, it should be
the following subset of the room state:

- The `m.room.create` event.

- The current `m.room.power_levels` event, if any.

- The sender's current `m.room.member` event, if any.

- If type is `m.room.member`:

    - The target's current `m.room.member` event, if any.
    - If `membership` is `join` or `invite`, the current
      `m.room.join_rules` event, if any.
    - If membership is `invite` and `content` contains a
      `third_party_invite` property, the current
      `m.room.third_party_invite` event with `state_key` matching
      `content.third_party_invite.signed.token`, if any.
    - If `content.join_authorised_via_users_server` is present,
      and the [room version supports restricted rooms](/rooms/#feature-matrix),
      then the `m.room.member` event with `state_key` matching
      `content.join_authorised_via_users_server`.

#### Rejection

If an event is rejected it should neither be relayed to clients nor be
included as a prev event in any new events generated by the server.
Subsequent events from other servers that reference rejected events
should be allowed if they still pass the auth rules. The state used in
the checks should be calculated as normal, except not updating with the
rejected event where it is a state event.

If an event in an incoming transaction is rejected, this should not
cause the transaction request to be responded to with an error response.

{{% boxes/note %}}
This means that events may be included in the room DAG even though they
should be rejected.
{{% /boxes/note %}}

{{% boxes/note %}}
This is in contrast to redacted events which can still affect the state
of the room. For example, a redacted `join` event will still result in
the user being considered joined.
{{% /boxes/note %}}

#### Soft failure

{{% boxes/rationale %}}
It is important that we prevent users from evading bans (or other power
restrictions) by creating events which reference old parts of the DAG.
For example, a banned user could continue to send messages to a room by
having their server send events which reference the event before they
were banned. Note that such events are entirely valid, and we cannot
simply reject them, as it is impossible to distinguish such an event
from a legitimate one which has been delayed. We must therefore accept
such events and let them participate in state resolution and the
federation protocol as normal. However, servers may choose not to send
such events on to their clients, so that end users won't actually see
the events.

When this happens it is often fairly obvious to servers, as they can see
that the new event doesn't actually pass auth based on the "current
state" (i.e. the resolved state across all forward extremities). While
the event is technically valid, the server can choose to not notify
clients about the new event.

This discourages servers from sending events that evade bans etc. in
this way, as end users won't actually see the events.
{{% /boxes/rationale %}}

When the homeserver receives a new event over federation it should also
check whether the event passes auth checks based on the current state of
the room (as well as based on the state at the event). If the event does
not pass the auth checks based on the *current state* of the room (but
does pass the auth checks based on the state at that event) it should be
"soft failed".

When an event is "soft failed" it should not be relayed to the client
nor be referenced by new events created by the homeserver (i.e. they
should not be added to the server's list of forward extremities of the
room). Soft failed events are otherwise handled as usual.

{{% boxes/note %}}
Soft failed events participate in state resolution as normal if further
events are received which reference it. It is the job of the state
resolution algorithm to ensure that malicious events cannot be injected
into the room state via this mechanism.
{{% /boxes/note %}}

{{% boxes/note %}}
Because soft failed state events participate in state resolution as
normal, it is possible for such events to appear in the current state of
the room. In that case the client should be told about the soft failed
event in the usual way (e.g. by sending it down in the `state` section
of a sync response).
{{% /boxes/note %}}

{{% boxes/note %}}
A soft failed event should be returned in response to federation
requests where appropriate (e.g. in `/event/<event_id>`). Note that soft
failed events are returned in `/backfill` and `/get_missing_events`
responses only if the requests include events referencing the soft
failed events.
{{% /boxes/note %}}

Example

As an example consider the event graph:

      A
     /
    B

where `B` is a ban of a user `X`. If the user `X` tries to set the topic
by sending an event `C` while evading the ban:

      A
     / \
    B   C

servers that receive `C` after `B` should soft fail event `C`, and so
will neither relay `C` to its clients nor send any events referencing
`C`.

If later another server sends an event `D` that references both `B` and
`C` (this can happen if it received `C` before `B`):

      A
     / \
    B   C
     \ /
      D

then servers will handle `D` as normal. `D` is sent to the servers'
clients (assuming `D` passes auth checks). The state at `D` may resolve
to a state that includes `C`, in which case clients should also to be
told that the state has changed to include `C`. (*Note*: This depends on
the exact state resolution algorithm used. In the original version of
the algorithm `C` would be in the resolved state, whereas in latter
versions the algorithm tries to prioritise the ban over the topic
change.)

Note that this is essentially equivalent to the situation where one
server doesn't receive `C` at all, and so asks another server for the
state of the `C` branch.

Let's go back to the graph before `D` was sent:

      A
     / \
    B   C

If all the servers in the room saw `B` before `C` and so soft fail `C`,
then any new event `D'` will not reference `C`:

      A
     / \
    B   C
    |
    D'

#### Retrieving event authorization information

The homeserver may be missing event authorization information, or wish
to check with other servers to ensure it is receiving the correct auth
chain. These APIs give the homeserver an avenue for getting the
information it needs.

{{% http-api spec="server-server" api="event_auth" %}}

## EDUs

EDUs, by comparison to PDUs, do not have an ID, a room ID, or a list of
"previous" IDs. They are intended to be non-persistent data such as user
presence, typing notifications, etc.

{{% definition path="api/server-server/definitions/edu" %}}

## Room State Resolution

The *state* of a room is a map of `(event_type, state_key)` to
`event_id`. Each room starts with an empty state, and each state event
which is accepted into the room updates the state of that room.

Where each event has a single `prev_event`, it is clear what the state
of the room after each event should be. However, when two branches in
the event graph merge, the state of those branches might differ, so a
*state resolution* algorithm must be used to determine the resultant
state.

For example, consider the following event graph (where the oldest event,
E0, is at the top):

      E0
      |
      E1
     /  \
    E2  E4
    |    |
    E3   |
     \  /
      E5

Suppose E3 and E4 are both `m.room.name` events which set the name of
the room. What should the name of the room be at E5?

The algorithm to be used for state resolution depends on the room
version. For a description of each room version's algorithm, please see
the [room version specification](/rooms).

## Backfilling and retrieving missing events

Once a homeserver has joined a room, it receives all the events emitted
by other homeservers in that room, and is thus aware of the entire
history of the room from that moment onwards. Since users in that room
are able to request the history by the `/messages` client API endpoint,
it's possible that they might step backwards far enough into history
before the homeserver itself was a member of that room.

To cover this case, the federation API provides a server-to-server
analog of the `/messages` client API, allowing one homeserver to fetch
history from another. This is the `/backfill` API.

To request more history, the requesting homeserver picks another
homeserver that it thinks may have more (most likely this should be a
homeserver for some of the existing users in the room at the earliest
point in history it has currently), and makes a `/backfill` request.

Similar to backfilling a room's history, a server may not have all the
events in the graph. That server may use the `/get_missing_events` API
to acquire the events it is missing.

{{% http-api spec="server-server" api="backfill" %}}

## Retrieving events

In some circumstances, a homeserver may be missing a particular event or
information about the room which cannot be easily determined from
backfilling. These APIs provide homeservers with the option of getting
events and the state of the room at a given point in the timeline.

{{% http-api spec="server-server" api="events" %}}

## Joining Rooms

When a new user wishes to join a room that the user's homeserver already
knows about, the homeserver can immediately determine if this is
allowable by inspecting the state of the room. If it is acceptable, it
can generate, sign, and emit a new `m.room.member` state event adding
the user into that room. When the homeserver does not yet know about the
room it cannot do this directly. Instead, it must take a longer
multi-stage handshaking process by which it first selects a remote
homeserver which is already participating in that room, and use it to
assist in the joining process. This is the remote join handshake.

This handshake involves the homeserver of the new member wishing to join
(referred to here as the "joining" server), the directory server hosting
the room alias the user is requesting to join with, and a homeserver
where existing room members are already present (referred to as the
"resident" server).

In summary, the remote join handshake consists of the joining server
querying the directory server for information about the room alias;
receiving a room ID and a list of join candidates. The joining server
then requests information about the room from one of the residents. It
uses this information to construct an `m.room.member` event which it
finally sends to a resident server.

Conceptually these are three different roles of homeserver. In practice
the directory server is likely to be resident in the room, and so may be
selected by the joining server to be the assisting resident. Likewise,
it is likely that the joining server picks the same candidate resident
for both phases of event construction, though in principle any valid
candidate may be used at each time. Thus, any join handshake can
potentially involve anywhere from two to four homeservers, though most
in practice will use just two.

<!--
https://textart.io/sequence

object Client JoiningServer DirectoryServer ResidentServer
Client->JoiningServer: join request
JoiningServer->DirectoryServer: directory request
DirectoryServer->JoiningServer: directory response
JoiningServer->ResidentServer: make_join request
ResidentServer->JoiningServer: make_join response
JoiningServer->ResidentServer: send_join request
ResidentServer->JoiningServer: send_join response
JoiningServer->Client: join response
-->

```
+---------+          +---------------+            +-----------------+ +-----------------+
| Client  |          | JoiningServer |            | DirectoryServer | | ResidentServer  |
+---------+          +---------------+            +-----------------+ +-----------------+
     |                       |                             |                   |
     | join request          |                             |                   |
     |---------------------->|                             |                   |
     |                       |                             |                   |
     |                       | directory request           |                   |
     |                       |---------------------------->|                   |
     |                       |                             |                   |
     |                       |          directory response |                   |
     |                       |<----------------------------|                   |
     |                       |                             |                   |
     |                       | make_join request           |                   |
     |                       |------------------------------------------------>|
     |                       |                             |                   |
     |                       |                             |make_join response |
     |                       |<------------------------------------------------|
     |                       |                             |                   |
     |                       | send_join request           |                   |
     |                       |------------------------------------------------>|
     |                       |                             |                   |
     |                       |                             |send_join response |
     |                       |<------------------------------------------------|
     |                       |                             |                   |
     |         join response |                             |                   |
     |<----------------------|                             |                   |
     |                       |                             |                   |
```

The first part of the handshake usually involves using the directory
server to request the room ID and join candidates through the
[`/query/directory`](/server-server-api/#get_matrixfederationv1querydirectory) API endpoint. In the case of a new user joining a
room as a result of a received invite, the joining user's homeserver
could optimise this step away by picking the origin server of that
invite message as the join candidate. However, the joining server should
be aware that the origin server of the invite might since have left the
room, so should be prepared to fall back on the regular join flow if
this optimisation fails.

Once the joining server has the room ID and the join candidates, it then
needs to obtain enough information about the room to fill in the
required fields of the `m.room.member` event. It obtains this by
selecting a resident from the candidate list, and using the
`GET /make_join` endpoint. The resident server will then reply with
enough information for the joining server to fill in the event.

The joining server is expected to add or replace the `origin`,
`origin_server_ts`, and `event_id` on the templated event received by
the resident server. This event is then signed by the joining server.

To complete the join handshake, the joining server submits this new event
to the resident server it used for `GET /make_join`, using the `PUT /send_join`
endpoint.

The resident homeserver then adds its signature to this event and
accepts it into the room's event graph. The joining server receives
the full set of state for the newly-joined room as well as the freshly
signed membership event. The resident server must also send the event
to other servers participating in the room.

{{% http-api spec="server-server" api="joins-v1" %}}

{{% http-api spec="server-server" api="joins-v2" %}}

### Restricted rooms

Restricted rooms are described in detail in the
[client-server API](/client-server-api/#restricted-rooms) and are available
in room versions [which support restricted join rules](/rooms/#feature-matrix).

A resident server processing a request to join a restricted room must
ensure that the joining server satisfies at least one of the conditions
specified by `m.room.join_rules`. If no conditions are available, or none
match the required schema, then the joining server is considered to have
failed all conditions.

The resident server uses a 400 `M_UNABLE_TO_AUTHORISE_JOIN` error on
`/make_join` and `/send_join` to denote that the resident server is unable
to validate any of the conditions, usually because the resident server
does not have state information about rooms required by the conditions.

The resident server uses a 400 `M_UNABLE_TO_GRANT_JOIN` error on `/make_join`
and `/send_join` to denote that the joining server should try a different
server. This is typically because the resident server can see that the
joining user satisfies one of the conditions, though the resident server
would be unable to meet the auth rules governing `join_authorised_via_users_server`
on the resulting `m.room.member` event.

If the joining server fails all conditions then a 403 `M_FORBIDDEN` error
is used by the resident server.

## Knocking upon a room

Rooms can permit knocking through the join rules, and if permitted this
gives users a way to request to join (be invited) to the room. Users who
knock on a room where the server is already a resident of the room can
just send the knock event directly without using this process, however
much like [joining rooms](/server-server-api/#joining-rooms) the server
must handshake their way into having the knock sent on its behalf.

The handshake is largely the same as the joining rooms handshake, where
instead of a "joining server" there is a "knocking server", and the APIs
to be called are different (`/make_knock` and `/send_knock`).

Servers can retract knocks over federation by leaving the room, as described
below for rejecting invites.

{{% http-api spec="server-server" api="knocks" %}}

## Inviting to a room

When a user on a given homeserver invites another user on the same
homeserver, the homeserver may sign the membership event itself and skip
the process defined here. However, when a user invites another user on a
different homeserver, a request to that homeserver to have the event
signed and verified must be made.

Note that invites are used to indicate that knocks were accepted. As such,
receiving servers should be prepared to manually link up a previous knock
to an invite if the invite event does not directly reference the knock.

{{% http-api spec="server-server" api="invites-v1" %}}

{{% http-api spec="server-server" api="invites-v2" %}}

## Leaving Rooms (Rejecting Invites)

Normally homeservers can send appropriate `m.room.member` events to have
users leave the room, to reject local invites, or to retract a knock.
Remote invites/knocks from other homeservers do not involve the server in the
graph and therefore need another approach to reject the invite. Joining
the room and promptly leaving is not recommended as clients and servers will
interpret that as accepting the invite, then leaving the room rather
than rejecting the invite.

Similar to the [Joining Rooms](#joining-rooms) handshake, the server
which wishes to leave the room starts with sending a `/make_leave`
request to a resident server. In the case of rejecting invites, the
resident server may be the server which sent the invite. After receiving
a template event from `/make_leave`, the leaving server signs the event
and replaces the `event_id` with its own. This is then sent to the
resident server via `/send_leave`. The resident server will then send
the event to other servers in the room.

{{% http-api spec="server-server" api="leaving-v1" %}}

{{% http-api spec="server-server" api="leaving-v2" %}}

## Third-party invites

{{% boxes/note %}}
More information about third party invites is available in the
[Client-Server API](/client-server-api) under
the Third Party Invites module.
{{% /boxes/note %}}

When a user wants to invite another user in a room but doesn't know the
Matrix ID to invite, they can do so using a third-party identifier (e.g.
an e-mail or a phone number).

This identifier and its bindings to Matrix IDs are verified by an
identity server implementing the [Identity Service
API](/identity-service-api).

### Cases where an association exists for a third-party identifier

If the third-party identifier is already bound to a Matrix ID, a lookup
request on the identity server will return it. The invite is then
processed by the inviting homeserver as a standard `m.room.member`
invite event. This is the simplest case.

### Cases where an association doesn't exist for a third-party identifier

If the third-party identifier isn't bound to any Matrix ID, the inviting
homeserver will request the identity server to store an invite for this
identifier and to deliver it to whoever binds it to its Matrix ID. It
will also send an `m.room.third_party_invite` event in the room to
specify a display name, a token and public keys the identity server
provided as a response to the invite storage request.

When a third-party identifier with pending invites gets bound to a
Matrix ID, the identity server will send a POST request to the ID's
homeserver as described in the [Invitation
Storage](/identity-service-api#invitation-storage)
section of the Identity Service API.

The following process applies for each invite sent by the identity
server:

The invited homeserver will create an `m.room.member` invite event
containing a special `third_party_invite` section containing the token
and a signed object, both provided by the identity server.

If the invited homeserver is in the room the invite came from, it can
auth the event and send it.

However, if the invited homeserver isn't in the room the invite came
from, it will need to request the room's homeserver to auth the event.

{{% http-api spec="server-server" api="third_party_invite" %}}

#### Verifying the invite

When a homeserver receives an `m.room.member` invite event for a room
it's in with a `third_party_invite` object, it must verify that the
association between the third-party identifier initially invited to the
room and the Matrix ID that claims to be bound to it has been verified
without having to rely on a third-party server.

To do so, it will fetch from the room's state events the
`m.room.third_party_invite` event for which the state key matches with
the value for the `token` key in the `third_party_invite` object from
the `m.room.member` event's content to fetch the public keys initially
delivered by the identity server that stored the invite.

It will then use these keys to verify that the `signed` object (in the
`third_party_invite` object from the `m.room.member` event's content)
was signed by the same identity server.

Since this `signed` object can only be delivered once in the POST
request emitted by the identity server upon binding between the
third-party identifier and the Matrix ID, and contains the invited
user's Matrix ID and the token delivered when the invite was stored,
this verification will prove that the `m.room.member` invite event comes
from the user owning the invited third-party identifier.

## Public Room Directory

To complement the [Client-Server
API](/client-server-api)'s room directory,
homeservers need a way to query the public rooms for another server.
This can be done by making a request to the `/publicRooms` endpoint for
the server the room directory should be retrieved for.

{{% http-api spec="server-server" api="public_rooms" %}}

## Spaces

To complement the [Client-Server API's Spaces module](/client-server-api/#spaces),
homeservers need a way to query information about spaces from other servers.

{{% http-api spec="server-server" api="space_hierarchy" %}}

## Typing Notifications

When a server's users send typing notifications, those notifications
need to be sent to other servers in the room so their users are aware of
the same state. Receiving servers should verify that the user is in the
room, and is a user belonging to the sending server.

{{% definition path="api/server-server/definitions/event-schemas/m.typing" %}}

## Presence

The server API for presence is based entirely on exchange of the
following EDUs. There are no PDUs or Federation Queries involved.

Servers should only send presence updates for users that the receiving
server would be interested in. Such as the receiving server sharing a
room with a given user.

{{% definition path="api/server-server/definitions/event-schemas/m.presence" %}}

## Receipts

Receipts are EDUs used to communicate a marker for a given event.
Currently the only kind of receipt supported is a "read receipt", or
where in the event graph the user has read up to.

Read receipts for events that a user sent do not need to be sent. It is
implied that by sending the event the user has read up to the event.

{{% definition path="api/server-server/definitions/event-schemas/m.receipt" %}}

## Querying for information

Queries are a way to retrieve information from a homeserver about a
resource, such as a user or room. The endpoints here are often called in
conjunction with a request from a client on the client-server API in
order to complete the call.

There are several types of queries that can be made. The generic
endpoint to represent all queries is described first, followed by the
more specific queries that can be made.

{{% http-api spec="server-server" api="query" %}}

## OpenID

Third party services can exchange an access token previously generated
by the <span class="title-ref">Client-Server API</span> for information
about a user. This can help verify that a user is who they say they are
without granting full access to the user's account.

Access tokens generated by the OpenID API are only good for the OpenID
API and nothing else.

{{% http-api spec="server-server" api="openid" %}}

## Device Management

Details of a user's devices must be efficiently published to other users
and kept up-to-date. This is critical for reliable end-to-end
encryption, in order for users to know which devices are participating
in a room. It's also required for to-device messaging to work. This
section is intended to complement the [Device Management
module](/client-server-api#device-management)
of the Client-Server API.

Matrix currently uses a custom pubsub system for synchronising
information about the list of devices for a given user over federation.
When a server wishes to determine a remote user's device list for the
first time, it should populate a local cache from the result of a
`/user/keys/query` API on the remote server. However, subsequent updates
to the cache should be applied by consuming `m.device_list_update` EDUs.
Each new `m.device_list_update` EDU describes an incremental change to
one device for a given user which should replace any existing entry in
the local server's cache of that device list. Servers must send
`m.device_list_update` EDUs to all the servers who share a room with a
given local user, and must be sent whenever that user's device list
changes (i.e. for new or deleted devices, when that user joins a room
which contains servers which are not already receiving updates for that
user's device list, or changes in device information such as the
device's human-readable name).

Servers send `m.device_list_update` EDUs in a sequence per origin user,
each with a unique `stream_id`. They also include a pointer to the most
recent previous EDU(s) that this update is relative to in the `prev_id`
field. To simplify implementation for clustered servers which could send
multiple EDUs at the same time, the `prev_id` field should include all
`m.device_list_update` EDUs which have not been yet been referenced in a
EDU. If EDUs are emitted in series by a server, there should only ever
be one `prev_id` in the EDU.

This forms a simple directed acyclic graph of `m.device_list_update`
EDUs, showing which EDUs a server needs to have received in order to
apply an update to its local copy of the remote user's device list. If a
server receives an EDU which refers to a `prev_id` it does not
recognise, it must resynchronise its list by calling the
`/user/keys/query API` and resume the process. The response contains a
`stream_id` which should be used to correlate with subsequent
`m.device_list_update` EDUs.

{{% http-api spec="server-server" api="user_devices" %}}

{{% definition path="api/server-server/definitions/event-schemas/m.device_list_update" %}}

## End-to-End Encryption

This section complements the [End-to-End Encryption
module](/client-server-api#end-to-end-encryption)
of the Client-Server API. For detailed information about end-to-end
encryption, please see that module.

The APIs defined here are designed to be able to proxy much of the
client's request through to federation, and have the response also be
proxied through to the client.

{{% http-api spec="server-server" api="user_keys" %}}

{{% definition path="api/server-server/definitions/event-schemas/m.signing_key_update" %}}

## Send-to-device messaging

The server API for send-to-device messaging is based on the
`m.direct_to_device` EDU. There are no PDUs or Federation Queries
involved.

Each send-to-device message should be sent to the destination server
using the following EDU:

{{% definition path="api/server-server/definitions/event-schemas/m.direct_to_device" %}}

## Content Repository

Attachments to events (images, files, etc) are uploaded to a homeserver
via the Content Repository described in the [Client-Server
API](/client-server-api). When a server wishes
to serve content originating from a remote server, it needs to ask the
remote server for the media.

Servers should use the server described in the Matrix Content URI, which
has the format `mxc://{ServerName}/{MediaID}`. Servers should use the
download endpoint described in the [Client-Server
API](/client-server-api), being sure to use
the `allow_remote` parameter (set to `false`).

## Server Access Control Lists (ACLs)

Server ACLs and their purpose are described in the [Server
ACLs](/client-server-api#server-access-control-lists-acls-for-rooms)
section of the Client-Server API.

When a remote server makes a request, it MUST be verified to be allowed
by the server ACLs. If the server is denied access to a room, the
receiving server MUST reply with a 403 HTTP status code and an `errcode`
of `M_FORBIDDEN`.

The following endpoint prefixes MUST be protected:

-   `/_matrix/federation/v1/send` (on a per-PDU basis)
-   `/_matrix/federation/v1/make_join`
-   `/_matrix/federation/v1/make_leave`
-   `/_matrix/federation/v1/send_join`
-   `/_matrix/federation/v2/send_join`
-   `/_matrix/federation/v1/send_leave`
-   `/_matrix/federation/v2/send_leave`
-   `/_matrix/federation/v1/invite`
-   `/_matrix/federation/v2/invite`
-   `/_matrix/federation/v1/make_knock`
-   `/_matrix/federation/v1/send_knock`
-   `/_matrix/federation/v1/state`
-   `/_matrix/federation/v1/state_ids`
-   `/_matrix/federation/v1/backfill`
-   `/_matrix/federation/v1/event_auth`
-   `/_matrix/federation/v1/get_missing_events`

## Signing Events

Signing events is complicated by the fact that servers can choose to
redact non-essential parts of an event.

### Adding hashes and signatures to outgoing events

Before signing the event, the *content hash* of the event is calculated
as described below. The hash is encoded using [Unpadded
Base64](/appendices#unpadded-base64) and stored in the event
object, in a `hashes` object, under a `sha256` key.

The event object is then *redacted*, following the [redaction
algorithm](/client-server-api#redactions).
Finally it is signed as described in [Signing
JSON](/appendices#signing-json), using the server's signing key
(see also [Retrieving server keys](#retrieving-server-keys)).

The signature is then copied back to the original event object.

For an example of a signed event, see the [room version
specification](/rooms).

### Validating hashes and signatures on received events

When a server receives an event over federation from another server, the
receiving server should check the hashes and signatures on that event.

First the signature is checked. The event is redacted following the
[redaction
algorithm](/client-server-api#redactions), and
the resultant object is checked for a signature from the originating
server, following the algorithm described in [Checking for a
signature](/appendices#checking-for-a-signature). Note that this
step should succeed whether we have been sent the full event or a
redacted copy.

The signatures expected on an event are:

-   The `sender`'s server, unless the invite was created as a result of
    3rd party invite. The sender must already match the 3rd party
    invite, and the server which actually sends the event may be a
    different server.
-   For room versions 1 and 2, the server which created the `event_id`.
    Other room versions do not track the `event_id` over federation and
    therefore do not need a signature from those servers.

If the signature is found to be valid, the expected content hash is
calculated as described below. The content hash in the `hashes` property
of the received event is base64-decoded, and the two are compared for
equality.

If the hash check fails, then it is assumed that this is because we have
only been given a redacted version of the event. To enforce this, the
receiving server should use the redacted copy it calculated rather than
the full copy it received.

### Calculating the reference hash for an event

The *reference hash* of an event covers the essential fields of an
event, including content hashes. It is used for event identifiers in
some room versions. See the [room version
specification](/rooms) for more information. It is
calculated as follows.

1.  The event is put through the redaction algorithm.
2.  The `signatures`, `age_ts`, and `unsigned` properties are removed
    from the event, if present.
3.  The event is converted into [Canonical
    JSON](/appendices#canonical-json).
4.  A sha256 hash is calculated on the resulting JSON object.

### Calculating the content hash for an event

The *content hash* of an event covers the complete event including the
*unredacted* contents. It is calculated as follows.

First, any existing `unsigned`, `signature`, and `hashes` members are
removed. The resulting object is then encoded as [Canonical
JSON](/appendices#canonical-json), and the JSON is hashed using
SHA-256.

### Example code

```py
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
    # Since they can be modified we need to exclude them from the hash.
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
```

## Security considerations

When a domain's ownership changes, the new controller of the domain can
masquerade as the previous owner, receiving messages (similarly to
email) and request past messages from other servers. In the future,
proposals like
[MSC1228](https://github.com/matrix-org/matrix-doc/issues/1228) will
address this issue.
