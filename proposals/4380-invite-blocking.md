# MSC4380: Invite blocking

Users need a way to protect themselves from spammy room invites. There are
various proposals in this area (see
[MSC4192](https://github.com/matrix-org/matrix-spec-proposals/pull/4192) for a
comparison), but they have all proven complex to implement in one way or
another.

This MSC seeks explicitly to provide the simplest possible control, in the hope
that it can be specified and implemented quickly.

It is based on the proposals of
[MSC4155](https://github.com/matrix-org/matrix-spec-proposals/pull/4155), but
significantly cut down.

## Proposal

A new account data event `m.invite_permission_config` is introduced.

The content has a single property, `block_all`. When set to `true`, that
indicates that the user does not wish to receive *any* room invites, and they
should be blocked as described below. Any other value (including omission of
the property) means that the user wants to receive invites as normal (subject
to the constraints of existing mechanisms such as
[`m.ignored_user_list`](https://spec.matrix.org/v1.15/client-server-api/#mignored_user_list)).

When invites to a given user are blocked, the user's
homeserver MUST respond to the following endpoints with an error, if the user
is invited:

 * [`PUT /_matrix/federation/v1/invite/{roomId}/{eventId}`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv1inviteroomideventid)
 * [`PUT /_matrix/federation/v2/invite/{roomId}/{eventId}`](https://spec.matrix.org/v1.15/server-server-api/#put_matrixfederationv2inviteroomideventid)
 * [`POST /_matrix/client/v3/rooms/{roomId}/invite`](https://spec.matrix.org/v1.15/client-server-api/#post_matrixclientv3roomsroomidinvite)
 * [`POST /_matrix/client/v3/createRoom`](https://spec.matrix.org/v1.15/client-server-api/#post_matrixclientv3createroom)
   (checking the invite list)
 * [`PUT /_matrix/client/v3/rooms/{roomId}/state/m.room.member/{stateKey}`](https://spec.matrix.org/v1.15/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
   (for invite membership)

Any rejected requests should result in an HTTP 403 status code, with the Matrix
error code `M_INVITE_BLOCKED`.

In addition, existing events already in the database MUST NOT be served over client synchronisation endpoints such as
[`GET
/_matrix/client/v3/sync`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3sync)
or `/v4/sync` from
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4158). Invite
events received over federation should likewise not be served over `/sync` requests.

Servers MAY return any suppressed invite events over `/sync` if invite
blocking is later disabled.

Other endpoints, such as [`GET
/_matrix/client/v3/rooms/{roomId}/state`](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3roomsroomidstate),
are not affected by invite blocking: invite events are returned as normal.

The Application Services API is also unaffected by invite blocking: invite
events are sent over [`PUT
/_matrix/app/v1/transactions/{txnId}`](https://spec.matrix.org/v1.15/application-service-api/#put_matrixappv1transactionstxnid).

## Potential issues

Complete blocking of invites is something of a blunt instrument: a user is
likely to want more flexibility, for example to allow invites from a set of
trusted servers. As explained in the introduction, those changes are left for
future MSCs.

The user has no way to review any blocked invites, meaning that they might miss
something important.

## Alternatives

* [MSC4192](https://github.com/matrix-org/matrix-spec-proposals/pull/4192)
  presents a comprehensive comparison of alternative proposals. This proposal
  deliberately targets a minimal implementation.

* Drawing from the experience of email, a "spam bin" might be an alternative
  solution, allowing users to review any filtered emails and see if any are
  useful. On the other hand, by rejecting invites as early as possible, we
  provide better protection to the servers.

## Security considerations

None.

## Unstable prefix

| Stable identifier | Purpose | Unstable identifier |
| --- | --- | ---|

## Dependencies

None.
