# MSC4578: Cross-client Shared Search Indexes

For non-encrypted messages the matrix spec has a search api from the server. But for
encrypted messages, provide proper end-to-end encryption, clients are the only ones that
can create search indexes for full text search. Most matrix clients achieve search by
downloading and decrypting all message history and creating and index over that the
user can then query.

This comes two major drawbacks: it is not available right from login (on a new device),
and outright impossible to do on lower powered devices, like mobile phones. As a result
full text search over encrypted messages has never been available on these devices.

This MSC proposes to solve this issue by asking client that build such an index to share
that index with other clients by storing it encrypted in the user's account data.

## Sharing the search index

Search, in most clients, is currently organized by creating a search index per room.
Taking the matrix rust sdk implementation as the example for our case, the proposal is
that the client, that is currently online and added something to the search index locally
also uploads that update to the server under a well-known end-to-end-encrypted key in the
account data.

If a new client, e.g. a mobile phone, logs in, it can download the search index from the
account data, decrypt it and allow the user to search for the messages. If the the user
finds a message in the index it wants to look it, the client can query the message and
the necessary context from the server and display it to the user.

At the moment, the rust sdk creates a search index per room. Thus and to limit the amount
of data that is transferred to the server, it is probably useful to have an entry per
room in the account data as well.

## Encryption and securing

Account data is not encrypted by default, but the matrix spec already knows about
"secure secret storage and sharing" (SSSS) in which an encryption key is shared between
devices that is used to encrypt the account data before uploading it. The MSC proposes
to reuse that mechanism with the existing keys and a predictable account data key per room.

## Unstable prefix

This MSC proposes that you use unstable `msc4578.$implName.$roomId` key for the
account keys. Where `$implName` is the name of the custom name given to the specific
implementation by the implementor and `$roomId` is the room ID. Thus different search
index implementations can coexist and be shared between devices. The MSC recommends
to come up with a rather unique `$implName` rather than a generic one to avoid
conflicts with other implementations.

## Open Questions and points for discussion

While in concept this seems rather trivial from high above, there are several technical
challenges and questions, the author doesn't have a definite answer for but wants to
open the discussion about:

### Conflict resolution: versioned or append-only-logs?

[MSC4573](https://github.com/matrix-org/matrix-spec-proposals/pull/4573) already proposes
a simple mechanism of server-controlled increased versioning of account data to avoid
conflicts and missing updates. But the authors wonders if that is enough for this case
as, depending on the implementation, the search index may need to be overwritten completely
for every update - a constantly growing blob that is sent over the network constantly.
This becomes especially nasty once you consider having multiple devices that constantly
update the search index when a new message arrives, and then constantly conflict, read
the update from the server only to find their changes has already been applied.

So it stands to reason that maybe some local thresholds and caching limits should be
introduced, that limit the number of times the search index is actually written (e.g. only
every 10 updates?!?) and leave searching the missing entries to the client.

Or whether some other clever mechanism could be used to avoid sending the full search index
like extending the account-data to support append-log like value [types similar to redis](https://redis.io/docs/latest/commands/append/)
that could even be deduplicated, so if multiple devices are updating the search index
with the same message it only remains once.

### What search index format to use?

This MSC explicitly doesn't yet try to define the specific format of the search indexes
but wants to discuss the higher level impacts and potential problems. The idea of this
MSC is also to encourage implementors to take a stab at it, so we learn more about the
benefits and drawbacks of different search index formats.

### Search index size, growth and filtering

One problem all search index formats, and thus this proposal, faces is that the search
index constantly grows over time. Some indexes deal with that better than others but
given a history large enough this will always become a problem in several aspects:

1. Storage space: currently servers don't limit the size of account data, but depending
   on the specific format used, this storage space might not be available on the client
   either
2. Traffic: sending full search index or even only the updates to the client creates a
   lot more traffic. In particular on initial sync, if the client can't specify that it
   doesn't want to know about this yet.
3. But also when querying the search index, if the indexes are very large, a low-performance
   client might chooses to not download that ahead of time but instead download them on-demand
   only. Here it might be useful to allow for some other forms of filtering or streaming
   to allow the client to query more efficiently.
