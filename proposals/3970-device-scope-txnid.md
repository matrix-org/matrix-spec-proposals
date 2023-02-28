# MSC3970: Scope transaction IDs to devices

Transaction identifiers in the Client-Server API are currently scoped to the
concept of a "client session" which, when refresh tokens are used, can span a
sequence of access tokens.

The spec [reads](https://spec.matrix.org/v1.6/client-server-api/#transaction-identifiers):

> The scope of a transaction ID is a “client session”, where that session is
> identified by a particular access token. When refreshing an access token, the
> transaction ID’s scope is retained. This means that if a client with token `A`
> uses `TXN1` as their transaction ID, refreshes the token to `B`, and uses
> `TXN1` again it’ll be assumed to be a duplicate request and ignored. If the
> client logs out and back in between the `A` and `B` tokens, `TXN1` could be used
> once for each.

The transaction IDs appear in two parts of the Client-Server API spec:

1. As a identifier to allow the homeserver to make some `PUT` endpoints
[idempotent](https://spec.matrix.org/v1.6/client-server-api/#transaction-identifiers)
2. An unsigned field in the event data model for a client to tell if it sent an
event or not. a.k.a. solving the
["local echo"](https://spec.matrix.org/v1.6/client-server-api/#local-echo) problem

For reference, the `PUT` endpoints that have the a `{txnId}` param are:

- [`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`](https://spec.matrix.org/v1.6/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
- [`PUT /_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}`](https://spec.matrix.org/v1.6/client-server-api/#put_matrixclientv3roomsroomidredacteventidtxnid)
- [`PUT /_matrix/client/v3/sendToDevice/{eventType}/{txnId}`](https://spec.matrix.org/v1.6/client-server-api/#put_matrixclientv3sendtodeviceeventtypetxnid)

## Proposal

It is proposed that the scope of transaction identifiers be changed from a
"client session" to a "device".

A "device" is typically represented by a `device_id` elsewhere in the spec.

For idempotency, this means the homeserver changing the method of identifying a
request from:

- (`client session`, `HTTP path of request which includes the transaction ID`)

to:

- (`device_id`, `HTTP path of request which includes the transaction ID`)

For local echo, the homeserver would now include the `transaction_id` in the
event data when it is serving a sync request from the same `device_id` as
determined from the access token.

## Potential issues

### This is technically a breaking change to the spec

The main "issue" I see with this proposal is that this is technically a breaking
change to the spec.

Because a device ID could have multiple sequences of access tokens associated
with it, this proposal would widen the scope of the transaction ID.

Therefore it could potentially lead to a request being treated as "new" where
before it would have been identified as a retransmission and deduplicated.

However, the evidence suggests that nothing would be impacted in reality.

Some evidences have been collated to support this claim:

#### 1. Data from the matrix.org Homeserver suggests the change would have no impact

The matrix.org Homeserver is a reasonable size deployment and could be considered
reasonably representative of the diversity of Matrix client.

The Synapse homeserver that runs matrix.org maintains a `event_txn_id` table
that contains a rolling 24 hour window of
(`user_id`, `token_id`, `room_id`, `txn_id`) tuples.

Having analysed the contents of the table, it appears that there are no repeated
transaction IDs for a given user, token and room.

There are other `PUT` endpoints for which transaction IDs are not in the
`event_txn_id` table, however because the event

As such, the widening of the scope from token to device would not have caused
any issues during the periods sampled.

For reference the following is the schema of the `event_txn_id` table:

```sql
              Table "matrix.event_txn_id"
   Column    |  Type  | Collation | Nullable | Default
-------------+--------+-----------+----------+---------
 event_id    | text   |           | not null |
 room_id     | text   |           | not null |
 user_id     | text   |           | not null |
 token_id    | bigint |           | not null |
 txn_id      | text   |           | not null |
 inserted_ts | bigint |           | not null |
Indexes:
    "event_txn_id_token_id" btree (token_id)
    "event_txn_id_event_id" UNIQUE, btree (event_id)
    "event_txn_id_ts" btree (inserted_ts)
    "event_txn_id_txn_id" UNIQUE, btree (room_id, user_id, token_id, txn_id)
Foreign-key constraints:
    "event_txn_id_event_id_fkey" FOREIGN KEY (event_id) REFERENCES matrix.events(event_id) ON DELETE CASCADE
    "event_txn_id_token_id_fkey" FOREIGN KEY (token_id) REFERENCES matrix.access_tokens(id) ON DELETE CASCADE
```

And the query to look for repeated transaction IDs:

```sql
SELECT e1.txn_id, LEFT(e1.user_id, 5) AS user_id, e1.token_id, e2.token_id, e1.inserted_ts, e2.inserted_ts FROM matrix.event_txn_id e1, matrix.event_txn_id e2 WHERE e1.txn_id = e2.txn_id AND e1.event_id <> e2.event_id AND e1.event_id < e2.event_id AND e1.user_id = e2.user_id AND e1.room_id = e2.room_id ORDER BY e1.token_id;
 txn_id | user_id | token_id | token_id | inserted_ts | inserted_ts
--------+---------+----------+----------+-------------+-------------
(0 rows)
```

#### 2. Conduit homeserver already scopes transaction IDs to devices

As highlighted by the new Complement
[tests](https://github.com/matrix-org/complement/pull/613) the Conduit homeserver
is already scoping transaction IDs to devices.

I can't find a related issue [listed](https://gitlab.com/famedly/conduit/-/issues),
so presumably this non-compliant behaviour isn't causing a known issue for
admins and users of the Conduit homeserver?

#### 3. Synapse homeserver only checks for retransmits over a 30-60 minute window

The Synapse homeserver uses an in-memory cache to check for idempotency of
requests. The cache is vacated after
[30-60 minutes](https://github.com/matrix-org/synapse/blob/adac949a417d064958039ae0918b97388413c824/synapse/rest/client/transactions.py#L50-L52)
and is not persisted between restarts (or across a cluster).

This means that for many existing deployments idempotency is only actually
enforced over a 30-60 minutes and not eternally as the spec might suggest.

#### 4. Synapse homeserver only supports local echo for the previous 24 hours

The Synapse homeserver only supports local echo (by the presence of
`transaction_id` on sync responses) for the previous 24 hours. This is because
the `event_txn_id` table is only kept for 24 hours.

Again, this suggests that in reality the local echo semantics are not preserved
eternally as the spec might suggest.

### Is the "device" concept the right level of abstraction to use?

One way to look at it is that device is already widely used in the end-to-end
encryption parts of the spec and so why isn't it suitable for this use case too?

### What about two clients masquerading as a single device ID?

I don't know if this actually works in practice. If this was a concern then it
could be mitigated by clarifying in the spec that if a client wishes to submit
requests using the same `device_id` as another client session that it should
choose transaction identifiers that are unique to that client session.

## Alternatives

### Do nothing

We could leave the transaction ID scope as is.

However, it makes it difficult to implement a features like
[MSC3861: Matrix architecture change to delegate authentication via OIDC](https://github.com/matrix-org/matrix-spec-proposals/pull/3861)
as the concept of a "client session" doesn't really exist in OIDC.

As noted above, at least one homeserver implementation is also not implementing
the spec as it is today.

It also turns out that the current implementation of refresh tokens in Synapse
breaks the transaction ID semantics already and needs to be
[fixed](https://github.com/matrix-org/synapse/issues/15141).

### Make a backwards compatible change

A backwards compatible alternative could be something like:

1. For idempotency have clients opt-in to a new scope of transaction ID, but
support the current semantics too for compatibility
2. Have clients opt-in (e.g. request param on the sync endpoint) to receiving
transaction ID for all events in the sync response and make the client
responsible for identifying which messages they sent

The disadvantage of this is that we create a load of extra maintenance work to
support both semantics for a period of time for (empirically) no gain in return.

## Security considerations

A malicious client can adopt an existing device ID of a user. This could
possibly allow some kind of denial of service attack.

However, if such an attack where possible it would be possible to do so without
this MSC as device IDs are crucial to the implementation of end-to-end encryption.

## Other recommendations

I'm not suggesting that these recommendations are address in this proposal, but
more notes for future proposals or spec clarifications.

### Clarification on idempotency semantics

I have separately prepared a [spec PR](https://github.com/matrix-org/matrix-spec/pull/1449)
to clarify some of the idempotency semantics that doesn't modify the spec but is
useful to understand the context of this proposal.

### Clarification on transaction ID time scope

I also suggest that the spec be clarified over what time periods the transaction
ID is scoped for such that clients can be aware. This cloud simply be to say
that the time period is not defined and so may vary by implementation.

### Suggest a lease naive transaction ID format

I think we should sense to update the recommendation on the format of
transaction IDs from:

> how is not specified; a monotonically increasing integer is recommended

To something more unique (in my research I have found some clients use a seconds
since epoch which doesn't seem ideal)

## Unstable prefix

None needed.

## Dependencies

None.
