# MSC4348: Portable and serverless accounts in rooms

This MSC is a more ambitious an adaptation of [MSC4243: User ID
localparts as Account
Keys](https://github.com/matrix-org/matrix-spec-proposals/pull/4243)
for [MSC4345: Server ky identity and room
membership](https://github.com/matrix-org/matrix-spec-proposals/pull/4345)
that achieves the follow up goals immediately and securely.

The following is a quote from MSC4244:

> User IDs should be public keys because:
>  - User IDs as they are today are direct personal data. For [GDPR](https://github.com/matrix-org/matrix-spec/issues/342)
>    reasons we would like to be able to remove direct personal data from the immutable append-only DAG. This proposal
>    replaces user IDs with indirect personal data.
>  - As user IDs are user controlled, spammers set their localpart to abusive messages in order to harass and intimidate others. Redactions
>    do not remove the user ID so these messages persist in the room.

In addition to the above, we go further and remove the server from user ID's completely:

This is desirable because:

- Portable snd serverless accounts accounts are now native to this new room model.
- Pseudo identity is supported in the room model for servers and room
  admins that wish to immediately implement it.
- Servers can immediately be implemented as relays for P2P clients.
- Within the context of MSC4345, the server key can be rotated without
  effecting users or the room.

## Proposal

- User ID's in rooms are replaced with an ed25519 public key:
  an "Account Key". Leaving and rejoining the same room MUST NOT
  change the account key. The account key is encoded as unpadded
  urlsafe base 64. An example user ID is:
  `@l8Hft5qXKn1vfHrg3p4+W8gELQVo8N13JkluMfmn2sQ`

- The private key for this account key signs the event JSON over
  federation. The event is then cosigned by a participating server
  under the terms of
  [MSC4345](https://github.com/matrix-org/matrix-spec-proposals/pull/4345).
  Just like MSC4243, network requests are not required to verify the
  signature of inbound events as all public keys are available in the
  DAG.

- Unlike
  [MSC4243](https://github.com/matrix-org/matrix-spec-proposals/4243),
  no endpoint or network requests are needed for servers or clients to
  verify server ownership over an account, as all events are co-signed
  by the room scoped server key. This is both a security and
  consistency enhancement.

### Changes to room events

Events must always be sent with the account key user ID.

### Changes to room membership

Room membership must use the account key user ID as the `state_key`.

### Obtaining account and profile information as a server

We use the same `POST /_matrix/federation/v1/query/accounts` endpoint
from MSC4243, with the exception that the requested server must verify
that the requesting server is participating in common rooms to those
of the queried account key.

### Obtaining account and profile information as a client

The account name is annotated in `unsigned.account`. This is the
account name only and not the account name user ID.

The domain can be found from MSC4345's `unsigned.server_domain`.

## Potential issues

### Rotation of account keys

It's not clear how we can rotate account keys without a server
attesting to a rotation.

### Profile information in the DAG

How can we remove profile information from the DAG.  The goal is
opposite to the goal of MSC4345 in DAG reproducibility, in an E2EE
context, you don't want that for profile information.

It's not clear either whether this property is also desirable for
public rooms, and that you want an account's cosigning server to
provide this information instead. I believe it likely is desirable for
the profile information to be mostly ephemeral,because people's lives
change.

### Backwards incompatibility of user ID's

The change to user ID's is backwards incompatible, there isn't
avoiding this. We believe even MSC4243 will have to make this change
in the future to enable the same behaviour's in a consistent way.

## Alternatives

### MSC4243: User ID localparts as Account Keys

[MSC4243: User ID
localparts as Account
Keys](https://github.com/matrix-org/matrix-spec-proposals/pull/4243) provides
the prior work for this MSC and much of the inspiration.

The differences between this and is MSC4243 are

- MSC4243 takes an iterative approach towards
  portable identity without exploring its implications or making the
  changes necessary to facilitate it.

- MSC4243 requires use of a policy server in order to keep the room
  secure, whereas this proposal does not, as we depend upon MSC4345
  server participation to provide us security from malicious keys and
  malicious backfill.

- Because MSC4243 takes an iterative approach, the User ID format does
  not need to change. This provides the argument that the MSC is
  non-breaking. But the reality is different because of the security
  implications that the MSC imposes on clients and servers. We believe
  that the MSC still imposes breaking changes on clients that interact
  with power levels and also moderation.  It also mandates changes in
  clients to ensure that unverified users are shown in a safe way.

- MSC4243 embeds the domain into the account key user ID, which always
  allows for that information to be faked at the DAG level. Clients
  must be protected by servers from this with consideration to replace
  User ID's in client formatted events. This likely will be a
  complicating factor for that MSC when events interact with the power
  level and access control mechanism of the room.



## Security considerations

### User accounts can move servers

Users that were resident to denied servers can migrate their account
to servers that are participating in the room. We assess this is
acceptable because we expect completing the same registration
requirements on the new server as they would with a brand new user
account will be required to migrate an account.

We expect servers with weak registration requirements or setup for the
use of ban evasion will be identified and removed as they are
currently. However, with the security enhancements of MSC4345, such
servers can no longer join rooms unanticipated. So we have an
advantage.

## Unstable prefix

- The endpoint `/_matrix/federation/v1/query/accounts` is
  `/_matrix/federation/v1/query/org.matrix.4348.accounts

## Dependencies

- [MSC4345: Server ky identity and room
membership](https://github.com/matrix-org/matrix-spec-proposals/pull/4345)
is a dependency
