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

- Notaries may never have been present in the rooms that a server is
  trying to join. This is especially true of matrix.org which is the
  notary used by default in synapse. If no notary has the key history
  for a given server, none of the events can be verified.

- As server keys are domain scoped and the domain name provides the
  identity of servers in the DAG, verifying authenticity of events is
  a crossed concern with verification of ownership of a domain.

This MSC is inspired the work of @kegsay in
[MSC4243](https://github.com/matrix-org/matrix-spec-proposals/pull/4243).

Additionally, this MSC uses terminology from [MSC4349: Causal barriers
and
enforcement](https://github.com/matrix-org/matrix-spec-proposals/pull/4349):
ie _causal barrier_ and _causal enforcement_.

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

In addition to this, we strengthen the conditions of server
participation in the DAG:

- We also introduce server participation, which allows servers to be
  denied access to the room at the DAG level. This allows both public
  and private rooms to benefit from DAG reproducibility and preemptive
  access control. Denied participation forms a _casual barrier_.

- Servers are unable to participate within a room until their key has
  been added by an existing participant. This principally ensures the
  introduction of server keys is traceable to existing
  participants. Without this traceability, the ability to add an
  infinite number of new server keys is available ambiently to anyone
  who is able to federate with a by-standing participant or malicious
  leaky server. In addition, this provides participants that have
  invite permission the opportunity to challenge previously
  undiscovered homeservers. Whereas there is no current protocol step
  to enable this for public rooms.

We make no attempt to change the relationship of users to the DAG and
servers within this MSC. [MSC4348: Portable and serverless accounts in
rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/4348)
is an MSC that does explore changing the relationship of users to
servers that builds upon this proposal. Servers still have to send
events through their users in both MSCs and we don't intend to change
that in future MSCs in this series either.

### Terminiology

- A server's _ambient power level_ is the highest power level of any
  user that is resident to the server.

- A _causal barrier_ is an event which excludes all concurrent events
  from _consideration_. A ban event is a causal barrier that is
  enforced locally by soft failure. A causal barrier can be scoped to
  a specific sender, like the ban event is. In this proposal, we
  introduce a barrier scoped to a specific server. Which is an
  `m.server.participation` event with a `participation` of `denied`.

#### A note on _causal barriers_

This MSC does not propose changes to the enforcement of _causal
barriers_. But its security is greatly enhanced with different
enforcement tehniques to soft failure, such as a trusted authority in
a policy server. Alternative options for _causal enforcement_ are
discussed in [MSC4349: Causal barriers and
enforcement](https://github.com/matrix-org/matrix-spec-proposals/pull/4349).

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

### Participation semantics

In this section, we describe the semantics of server participation.
Later, we make an attempt of implementing these in authorization
rules, but auth rules are difficult to parse, and the intent and
context of statments is lost. Where authorization rules are
inconsistent this text takes precedence.

- Reminder: In this MSC _Server_ refers to the controller of a ed25519
  keypair, not a particular domain or deployment.

#### Accepted participation

The purpose of the `accepted` participation state is to bring the
`m.server.participation` event into a _subject controlled state_.
This means that only the controller of the keypair for which the
participation describes can change the `advertised_domain` in the
event.

This stops other room participants with the _invite_ power level from
changing the `advertised_domain`.

#### Permitted participation

The purpose of the `permitted` participation state is for a user to
permit another server to begin participaiting in the room.  This adds
traceability to the origin of keys within a room. Without this
traceability, the ability to add an infinite number of new server keys
is available ambiently to anyone who is able to federate with a
by-standing participant or malicious leaky server. In addition, this
provides participants that have invite permission the opportunity to
challenge previously undiscovered homeservers. Whereas there is no
current protocol step to enable this for public rooms.

#### Denied participation when set by room admins

A user with the _ban_ power level, may change the
`m.server.participation` event of any server with less ambient power
level to `denied`. This power level comparison is the sending user's
power level compared to the denied server's ambient power level.

Once a key is denied, if a Matrix homeserver is to participate again
it must rejoin the room with a new keypair.

#### Denied participation when set by the key controller

The server may revoke its own key at any time by setting its own
participation to `denied`. A server can do this even if its current
participation is already `denied` becasue a server admin banned them.
This allows for keys that have been stolen by room admins to still be
revoked.  The effect of a server setting its own participation to
`denied` is permanent, to rejoin the room, a new keypair must be
created. If keys are stolen to invoke revoction maliciously, then that
is a good thing that they only stole the key for that purpose.

#### Are clients responsible for `m.server.participation` ?

Almost always the server sends the event on behalf of a user
indirectly as a part of another client-server API interaction, such as
accepting an invitation. Most flows have no need for dedicated client
UI or management with exception of:

- Banning servers via setting the state to `denied`.
- Revoking the server key.

In these situations, the event is sent as a direct result of a user's
action communicated in client UI.

#### Room creation flow

After creating the room, the room creator's origin server should set
its own `participation` via the room creator's account to `accepted`,
and set the advertised `advertised_domain` property of their
participation event to include a domain for which they can prove
ownership.

#### Room join flow

In order to join a room, the `/request_participation` endpoint is used
to first ensure that a participation event exists in the room for the
joining server's public key.

The joining server uses the response from this endpoint to create a
`participation` event that sets the current participation to
`accepted`. The joining server should also set the `advertised_domain`
that they are advertising their public key from.

Servers MUST accept or deny their own participation before emitting
any events to the room. This is enforced by authorization rules.

#### Room invitation flow

To invite participants, prior to sending the invite membership events,
the public key of the target user's resident server will need to have
a `m.server.participation` event in the room's current state with a
`participation` of `permited` or `accepted`.  If there is no current
participation, an `m.server.participation` event will need to be sent
by the inviter to ensure the invited user's resident server can accept
participation. This event will have a `participation` of `permitted`.

Servers can only accept invitations and emit a join event when their
current participation state in the room is set to `accepted`.

### Key revocation

We define a _key revocation event_ to be an `m.server.participation`
event with the following properties:

1. The event's signature can be verified with the key found in the `state_key`.
2. The event's `participation` is `denied`.

Key revocations are enforced by auth rules to be immutable.

### Additional causal restrictions on `m.server.participation` when participation is `denied`

These restrictions can be enforced locally or by another causal
authority. See
[MSC4349](https://github.com/matrix-org/matrix-spec-proposals/pull/4349).

- The considered event MUST NOT be conflicting to the known _vector
  clock frontier_ of the sender.

### The `m.server.participation` authorization rule

These rules are to be inserted before rule 4 in [version
12](https://spec.matrix.org/v1.10/rooms/v11/#authorization-rules), the
check for `m.room.member`.

1. If type is `m.server.participation`:
   1. If the sender's signature matches the `state_key` of the
      considered event:
      1. If the `participation` field of the considered event is
         `denied` AND the current participation is not `denied`, allow.
      2. If the `participation` field of the considered event is not
         `accepted`, reject.
      3. If the sender is a room creator, allow[^room-creator].
      4. If the current participation state for the target is `permitted`
         or `accepted`, allow.
      5. Otherwise, reject.
   2. If `participation` is `accepted`, reject[^participation-accept].
   3. If `partcipation` is `denied`:
      1. If the origin of the current participation state is the target key, reject[^revocation].
	  2. If the `sender`'s power level is greater than or equal to the _ban level_,
            is greater than or equal to the target server's ambient power level, allow.
	  3. Otherwise, reject.
   4. If `participation` is `permitted`:
      1. If the _target server_'s current participation state is `accepted`, reject.
      2. If the _target server_'s current participation state is `denied`, reject[^revocation].
      3. If the `sender`'s power level is greater than or equal to
         the _invite level_, allow.
	  4. Otherwise, reject.
   5. Otherwise, reject.
2. If the `sender`'s current participation state is not `accepted`, reject.

[^room-creator]:
	This rule allows the room creator to set their own participation.

[^participation-accept]:
    This rule prevents anyone but the owner of
    the key from setting the participation to accept

[^revocation]:
    This rule enforces that any controller of the key has total
    autonomy over its revocation. Room admins cannot steal a key and
    override this, once the key is denied, it has been permanently
    revoked.


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

### Introducing `/_matrix/key/v3/query`

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
cache the mapping. But may not wish to do so permanently, as the keys
may be stolen or revoked in the future.

The requested server should make sure to only admit ownership of keys
for which the requesting server can access through participation
within a room where the requested server is using said keys.

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

### Why server bans are implemented as key revocation

It's not clear whether Matrix will be able to prevent room admins
becoming a causal authority. In that instance, banning and unbanning a
server can be used to successfully use a stolen identity without the
original controller being able to stop it. See below. If denial is
revocation, then the original key controller can deny their own key in
any branch that the room admins try to create where the key is still
valid.

Room admins as causal authority may successfully use stolen keys to
impersonate if `denied` participation is not key revocation

If a room admin steals a server key, they may still use the stolen key
by denying the key as an admin, and then use the stolen the key to add
events that are concurrent to the deny. If the room admin also serves
as the causal authority in the room, then this would allow them to
fake valid events.

Without being the causal authority this attack would fail. Without
the ability to "unban" a server identity, this attack fails.

## Unstable prefix

`m.server.participation` -> `org.matrix.msc4345.participation`

`_matrix` => `_matrix/msc4345/` or whatever the norm is here.

## Dependencies

None.
