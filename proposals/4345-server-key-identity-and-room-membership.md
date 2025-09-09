# MSC4345: Server key identity and room membership

Events in Matrix are signed by the sending server's domain-scoped
sigining key, which is also a rotating key. During signature
verification, a server must obtain the public key used to sign an
event. This presents problems when the origin server is offline or has
been decommissioned. As this forces servers to rely on notaries to
supply historical keys.

There are several issues with this system that lead to inconsistent
views of the DAG:

- Centralisation of trust: Signature verification depends on notaries
  being online and honest about historical keys.

- Fragility: Notaries may never have been present in the rooms that a
  server is trying to join. This is especially true of matrix.org
  which is the notary used by default in synapse. If no notary has the
  key history for a given server, none of the events can be verified.

- Complexity and insecurity: Verifying authenticity of events is an
  unnecessarily crossed concern with verification of ownership of a
  domain.

This MSC is inspired the work of @kegsay in
[MSC4243](https://github.com/matrix-org/matrix-spec-proposals/pull/4243).

## Proposal

We propose to make the server's identity within a room solely a long
lived ed25519 public key. This key is explicitly appended to the DAG
via an auth event. This event also sets the terms for routing
information and the server's participation within the room.

This has several advantages:

- The the DAG itself becomes a record of which keys were held by
  participants, which eliminates the need for notaries in public key
  discovery.

- Client UI associates servers with the server key, not the domain.
  We provide a friendly alternative to domain names that can be
  associated with the server key in clients as a substitution for
  servers with unverified domains.

- Verification of domain ownership happens subjectively at any time
  independently of the DAG. Domains are not associated with server
  keys and cannot be accessed by clients until their homeserver has
  independently verified ownership of the domain.

In addition to this, we strengthen the conditions of server participation in the DAG:

- We also introduce server participation, which allows servers to be
  denied access to the room at the DAG level.

- Servers are unable to participate within a room until their key has
  been added by an existing participant. This feature provides room
  participants that have invite permission the opportunity to
  challenge previously undiscovered homeservers. Whereas previously
  for public rooms, there was no protocol step to enable this.

- Rules are introduced that allow servers to be removed without the
  need for soft-failure by canonicalising their history as part of the
  deny event.

This allows both public and private rooms to benefit from DAG
reproducibility and preemptive access control for servers without the
use of a policy server.

### The `m.server.participation` state event, `state_key: ${origin_server_key}`

#### The `advertised_domain` property

This is a string representing the domain of the server. This is not an
attestation that ownership has been verified by the sender of the
event. This property is protected from redaction.

This property is not required, as it may be desirable to hide the
domain when setting the server's participation to `denied`. Particularly
in the event of attempted impersonation or an abusive domain name.

#### The `participation` property

`participation` can be one of `permitted`, `accepted` or
`denied`. `participation` is protected from redaction.

A denied server must not be sent a `m.server.participation` event
unless the targeted server is already present within the room. This is
to prevent malicious servers being made aware of rooms that they have
not yet discovered.

#### The `reason` property

An optional reason property may be present in order to explain the
reason why a server has been denied or permitted to participate.

### Terminology for authorization

The _considered event extremities_ is the set of events provided by
`prev_events` and `auth_events` of the considered event.

The _considered event's acknowledged events_ is the set of events
connected to the `prev_events` of the considered event.

The _origin server's acknowledged extremities_ is the set of events
that are the tips of all DAG fragments which the origin server has
previously referenced in the `prev_events` of any event that has
already been authorized. This set is empty if the origin server has
not sent any prior events to the room.

The _origin server's acknowledged events_ is the set of events that
are connected to the _origin server's acknowledged extremities_ set,
including the _acknowledged extremities_ themselves.

### Key revocation

We define a _key revocation event_ to be an `m.server.participation`
event with the following properties:

1. The event's signature can be verified with the key found in the `state_key`.
2. The event's `participation` is `denied`.
3. The _considered event's acknowledged events_ is not a subset of the
   _origin server's acknowledged events_.
4. If the current `participation` is `denied`:
   1. If the current `participation` is not signed with the same key.
   2. The _considered event's acknowledged events_ is equal to the
      the _origin server's acknowledged events_.

### The `m.server.participation` authorization rule

These rules are to be inserted before rule 4 in [version
12](https://spec.matrix.org/v1.10/rooms/v11/#authorization-rules), the
check for `m.room.member`.

1. If type is `m.server.participation`:
   1. If the sender's signature matches the `state_key` of the
      considered event:
   1. If the `participation` field of the considered event is
      `denied`, allow.
   1. If the `participation` field of the considered event is not
      `accepted`, reject.
   1. If the sender is a room owner, allow.
   1. If the current participation state for the target is `permitted`
      or `accepted`, allow.
   1. Otherwise, reject.
2. If the `sender`'s current participation state is not `accepted`, reject.
3. If `participation` is `accepted`, reject[^participation-accept].
4. If there is no current participation state for the target:
   2. If `partcipation` is `denied`:
      1. If the `sender`'s power level is greater than or equal to the _ban level_,
         is greater than or equal to the target server's ambient power level, allow.
      2. Otherwise, reject.
   3. If `participation` is `permitted`:
      1. If the _target server_'s current participation state is `accepted`, reject.
   4. If the _target server_'s current participation state is `denied`:
      1. If the origin of the current participation state is the target key, reject[^revocation].
      2. If the `sender`'s power level is less than the _ban
         level_ or is less than the target server's ambient power
         level, reject.
   5. if the `sender`'s power level is greater than or equal to
      the _invite level_, allow. 3. Otherwise, reject.

5. If the `sender`'s current participation state is not `accepted`, reject.

[^participation-accept]:
    This rule prevents anyone but the owner of
    the key from setting the participation to accept

### The authorization rule for `denied` participation

This rule should be inserted at the beginning of auth rules and noted
in the description of soft failure
https://spec.matrix.org/latest/server-server-api/#soft-failure.

1. If the `sender`'s current participation is `denied`:
   1. If the considered event is a _key revocation event_, allow[^revocation].
   2. If the the _current participation_ event's _origin server's
      acknowledged events_ does not include the considered event, reject.
   3. Fall-through.

This rule exists to ensure that a consistent history is provided for
the _denied server_. It removes the avenue for the denied server to
reference stale state to append an infinite number of soft failed
events to the DAG. It also prevents the sender of the deny event from
placing the deny earlier in history to remove the target server's
events. Doing so will have the same effect as using the current
state.

[^revocation]:
    This rule enforces that the owner of the key has total
    autonomy over its revocation. Room admins cannot steal a key and
    override this, and even if server admins set the server to deny,
    the key owner can still revoke the key.

### The `/request_participation` endpoint

When a server requests participation, the requested server should
verify that the joining server is claiming ownership of the provided
server key. The request should also be signed using the same server key.

Then, the requested server will emit an `m.server.participation` event
into the room with the key and the `advertised_domain` property filled
for the request origin.

Once this is complete, the requested server will respond with the information
required to begin interacting with the room.

When the joining server gets this response, it should immediately
change its own participation to `accepted` in order to prevent users
from overwriting the `advertised_domain`.

The following endpoint is defined: GET `/_matrix/federation/v1/request_participation/{roomId}/{serverKey}`.

The following query parameters are supported:

- `ver` the room versions the sending server has support for (identical to `make_join`).

- `omit_members` whether to omit members from the response (identical to `send_join`).

The response is identical to `send_join`.

### Changes to `/_matrix/key/v3/query`

`valid_until_ts` is removed. Keys are never time-bounded and
revocation is explicit via DAG state.

To verify domain ownership from an `m.server.participation` event:

1. The event must have a `participation` of `accepted`.
2. The event must contain an `advertised_domain` property.
3. The event must be signed with the private key associated with the
   public key found in the state_key (auth rules also enforce the
   state key is consistent with the origin server key).
4. The same public key is advertised in `/_matrix/key/v3/query` when requested
   from the `advertised_domain`

The server that performed verification of domain ownership may now
permanently cache the mapping.

### Changes to the user ID format

- User ID _server name_'s are replaced with an ed25519 public key,
  called the _server key_[^msc4243-prose].

- The private key for this _server key_ signs event JSON over federation[^msc4243-prose].

[^msc4243-prose]:
    This wording is taken directly from MSC4243 and
    shaped up a little

### Impositions on Client UI

Homeserver's must verify domain ownership before events are annotated
with `unsigned.server_domain`. Clients then use this to show a user's
server domain user ID rather than a user's server key user ID. Clients
should never use the `m.server.participation` `advertised_domain` to
show the origin of events.

Clients should encode the public key for displaying unverified
servers. Clients may also highlight this by deriving a stable colour
identity from the key.

Please suggest specific algorithms to make this consistent.

## Potential issues

## Alternatives

### MSC4243: User ID localparts as Account Keys

This proposal is an alternative to [MSC4243: User ID localparts as
Account
Keys](https://github.com/matrix-org/matrix-spec-proposals/pull/4243)
and borrows several ideas from the same proposal. It is not required
reading. The key difference between these proposals is that this
proposal describes long lived identity for servers as a key pair in
Matrix rooms. Whereas MSC4243 only does so for individual user
accounts.

However, critically this MSC provides traceability to the origin of
usrs, whereas MSC4243 does not unless a policy server is in use to
sign each event.

### MSC4124: Simple Server Authorization

This proposal borrows the principle of constrained server membership
from MSC4124. Specifically changing authorization to stop
unencountered servers from suddenly appending an infinite amount of
data to the DAG.

### MSC4104: Auth Lock: Soft-failure-be-gone!

This proposal encodes a special auth rule for `denied` participation to
avoid soft failure and the problems discussed in MSC4104.

## Security considerations

See [Impositions on client UI](#impositions-on-client-ui).

## Unstable prefix

`m.server.participation` -> `org.matrix.msc4345.participation`

`_matrix` => `_matrix/msc4345/` or whatever the norm is here.

## Dependencies

None.
