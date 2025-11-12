# MSC4136: Shared retry hints between servers

## Problem

New Matrix servers currently have no idea which other servers are online or not, and so start a retry schedule from
first principles.

This is far from ideal, as joining a room with many participating servers (e.g. 10K in #matrix:matrix.org right now) is
incredibly heavy on the connecting server as the newly joined server will have to make 10K connection attempts as
rapidly as possible (both SRV and .well-known lookups, and then /send attempts) to identify alive servers.  Meanwhile,
dead servers (e.g. domains which no longer run Matrix servers) will be
[hammered](https://mastodon.matrix.org/@mnot@techpolicy.social/112319234007365786) by connection attempts.

Hopefully solves https://github.com/matrix-org/matrix-spec/issues/117

## Proposal

When joining a room, the server which facilitates the join ('resident server' in spec parlance) should propose retry
intervals to the joining server in the `/send_join` response.

Specifically, we add an optional `retry_hints` field to the `/send_join` response which provides optional
recommendations on how long the joining server SHOULD wait in milliseconds before retrying if it cannot connect to the
given domain.  As the field is optional, it does not require a new room version.

If no hint is provided for a given domain, the retry hint MUST be considered to be zero milliseconds.  Retry hints
should be provided whether or not the request had `omit_members` specified (i.e. whether or not faster remote room
joins are in use).

As an example `/send_join` response:

```json
  ...
  "servers_in_room": [
    "matrix.org",
    "example.com",
    "element.io"
  ],
  "retry_hints": {
    "example.com": {
      "retry_after": 3600000,
    },
    "element.io": {
      "retry_after": 604800000000,
    }
  }
```

This means that the joined room has three participating servers, but `example.com` is not reliably responding over
federation, and the resident server recommends that the joining server should wait 1 hour before retrying to connect to
it.  Similarly the recommendation is to wait 1 week before retrying element.io if it's down.

The spec currently does not specify anything about how federation retry schedules: as part of this change, we propose
explicitly adding that:

 * Servers SHOULD follow exponential or geometric backoff schedules (and MUST NOT retry linearly)
 * Servers SHOULD reset their retry schedule for a given domain if they receive traffic from that domain, and immediately retry.
 * On joining a room, servers SHOULD attempt to connect to all newfound servers (sending a no-op transaction if there are
   no other events to be sent), but queued in such a way to prioritise servers with lower `retry_after` value first,
   ensuring alive servers are prioritised over likely dead servers.
     * In other words: first attempting servers without a `retry_hint`, and then attempting servers with lower
       `retry_after` values, and then finally the servers with the largest `retry_after` values.
     * However, if federation fails, then the joining server should seed its retry algorithm with the `retry_after`
       value for that destination (rather than starting a fresh retry schedule).
 * If the joining server has already established a retry schedule for a given domain, it MUST ignore the `retry_hints`
   provided by the resident server for that domain.

## Alternatives

We could be more detailed in the recommended retry schedule (e.g. also specify the last time that a given server was
seen to be working; when it was first seen to have failed; when the last retry was attempted; etc). However, this would
bloat the size of the /send_join response (which we want to be as small as possible, to keep joins fast), and it's
unclear whether the joining server really needs to know this data to seed its retry algorithm: instead, it can assume
that retry_hints are present because the server is currently down and has just failed.  It also avoids risks of
accidentally creating a thundering herd of retry schedules if all servers seed their retry algorithm with precisely the
same schedule.  It also avoids us being too prescriptive on retry schedule algorithms.

Alternatively, we could go the other way, and avoid timing information entirely in `retry_hints` and simply return a
flag to say whether the resident server can currently connect to the destination or not. The joining server would then
use this to prioritise connection attempts. However, it feels useful to recommend how aggressively the joining serevr
should retry, as whether the server is currently up or down (e.g. to decide whether to attempt an immediate retry or
not).

## Security considerations

A malicious resident server could tell the joining server that certain destinations are down when they are not.  This is
mitigated by:

 * The joining server will attempt all servers anyway, just deprioritising ones with higher `retry_after` values.
 * The joining server will reset its retry schedule if it sees traffic from a given destination, letting the destination
   assert its own existence and health whenever its users communicate
 * The joining server will prioritise its own retry schedule over the received hint (if it has one)
 * The joining server has to trust the resident server to say what servers exist in the first place anyway
 * Events will indirectly make their way to destinations by being transitively pulled in via DAG references
   (although E2EE keys may be missing)
 * The resident server may have different connectivity to the destination than the joining server anyway, so this may
   not be malicious behaviour anyway.

## Unstable prefix

While this MSC is in development, the `retry_hints` key should be returned as `org.matrix.msc4136.retry_hints`.

## Dependencies

None