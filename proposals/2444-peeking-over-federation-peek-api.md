# Proposal for implementing peeking over federation (peek API)

## Problem

Currently you can't peek over federation, as it was never designed or
implemented due to time constraints when peeking was originally added to Matrix
in 2016.

As well as stopping users from previewing rooms before joining, the fact that
servers can't participate in remote rooms without joining them first is
inconvenient in many other ways:

 * You can't reliably participate in E2E encryption in rooms you're invited to
   unless the server is actually participating in the room
   (https://github.com/vector-im/riot-web/issues/2713)
 * You can't use rooms as generic pubsub mechanisms for synchronising data like
   profiles, groups, device-lists etc if you can't peek into them remotely.
 * Search engines can't work if they can't peek remote rooms.

## Solution

We let servers participate in peekable rooms (i.e. those with `world_readable`
`m.room.history_visibility`) without having actually joined them.

We do this by subscribing to a room on one or more servers via a new `/peek`
S2S API, which lets users on a given server declare their interest in viewing
events in that room.  Having started peeking into the room, the server(s)
being peeked will relay *all* events it sees in that room to the peeking
server (including ones from other servers).  It will also service the backfill
and event-retrieval APIs as if the peeking server was in the room.

This continues until the peeking server calls DELETE on the peek it initiated.

To start peeking, firstly the peeking server must pick server(s) to peek via.
This is typically the same server you would use to try to join the room via
(i.e. one taken from the alias, or the via param on a matrix.to URL). The
server could also call S2S /state on m.room.members to find other servers
participating in the room and try to peek them from too.

The peeking server starts to peek by PUTting to `/peek` on the peeked server.
The request takes an empty object as a body as a placeholder for future (where
we might put filters). The peeking server selects an ID for the peeking
subscription for the purposes of idempotency. The ID must be 8 or less bytes
of ASCII and should be unique for a given peeking & peeked server.

```
PUT /_matrix/federation/v1/peek/{roomId}/{peekId}
{}

{
    "peek_id": "12345",
}
```

```
DELETE /_matrix/federation/v1/peek/{roomId}/{peekId}
{}
```

If the peeking server hasn't heard any events from the peeked server for a
while, it should attempt to re-PUT the /peek. If the peeked server is
unavailable, it should retry via other servers from the room's members until
it can reestablish.

## Security considerations

The peeked server becomes a centralisation point which could conspire against
the peeking server to withhold events.  This is not that dissimilar to trying
to join a room via a malicious server, however, and can be mitigated somewhat
if the peeking server tries to query missing events from other servers.
The peeking server could also peek to multiple servers for resilience against
this sort of attack.

The peeked server will be able to track the metadata surrounding which servers
are peeking into which of its rooms, and when.  This could be particularly
sensitive for single-person servers peeking at profile rooms.

## Design considerations

This doesn't solve the problem that rooms wink out of existence when all
participants leave (https://github.com/matrix-org/matrix-doc/issues/534),
unlike other approaches to peeking (e.g. MSC1777)

Do we allow filtering the peek? (e.g. if you only care about particular
events, or particular servers - e.g. if load-balancing peeking via multiple
servers). Similarly, is it concerning that this significantly overlaps with
the /sync CS API?

How do we handle backpressure or rate limiting on the event stream (if at
all?)

## Dependencies

This unblocks MSC1769 (profiles as rooms) and MSC1772 (groups as rooms)
and is required for MSC1776 (peeking via /sync) to be of any use.

## History

This would close https://github.com/matrix-org/matrix-doc/issues/913

An earlier rejected solution is MSC1777, which proposed joining a pseudouser
(`@:server`) to a room in order to peek into it.  However, being forced to write
to a room DAG (by joining such a user) in order to perform a read-only operation
(peeking) was deemed inefficient and rejected.
