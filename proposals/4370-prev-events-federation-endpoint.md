# MSC4370: Federation endpoint for retrieving current extremities

[MSC4284: Policy Servers](https://github.com/matrix-org/matrix-spec-proposals/pull/4284) introduces
an idea for an extremely lightweight server implementation to be developed to reduce the amount of
spam which ends up persisted in a room's DAG. In these server implementations, knowing the "current"
state of the room can be important for factoring into deciding whether an event is spammy.

"Current state" is not a concept which exists over federation, however: servers are expected to calculate
and heal their copy of the DAG to resolve a definition of "current state" for the room. A policy server
might not be persisting or tracking the DAG for a room though, especially because it typically only
concerns itself with impact to *current* users in the room at the time the policy server is asked to
scan an event.

To avoid the burden of persisting (and calculating, healing, resolving, etc) the room DAG, policy
servers have two options:

1. Attach themselves to a full homeserver implementation via the Client-Server API, calling endpoints
   like [`GET /state`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3roomsroomidstate).
2. Wait for a "trusted" server to ask an event to be scanned, then call [`GET /state/:roomId`](https://spec.matrix.org/v1.16/server-server-api/#get_matrixfederationv1stateroomid)
   against that server using the just-scanned event ID as a reference (after waiting a little bit so
   the remote server can persist its now-approved event).

The first option is fiddly for policy servers which operate at the Federation layer natively, like
the Foundation's own policyserv implementation, because managing a bot account for this one information
source can be a lot of overhead.

The second option relies on the policy server receiving an event from a server it trusts before it
can "learn" the state of the room. If the room has a lot of traffic from other servers, its view of
"current state" may drift significantly and produce inaccurate spam determinations. This is the approach
policyserv currently uses.

This MSC introduces a new endpoint that (primarily) policy servers can use to retrieve the *current*
extremities a given server has so it may then retrieve the current state for the room. Policy servers
which require historical context of room state (or the DAG in general) should behave like a normal
homeserver and resolve the DAG to that point in time - this MSC will not be overly useful to them.

By allowing a server to retrieve the current extremities, that server can request (and cache) current
state whenever it feels it needs to rather than waiting for a remote server to become active. This
could be on a timer, after a certain number of events have been scanned in the room, after specific
event types are seen, or a combination of all 3 - when to call the new endpoint is left as an implementation
detail.

This MSC expects that the current extremities for a room are highly cached or easily discovered by
a given server implementation - it's the exact same information it would populate in `prev_events`
if it were to send an event at that time.

Though not primary drivers for this proposal, this MSC's new endpoint also enables two bonus features:

1. A server which has lost its copy of the DAG, but has a room ID and server name, can call the new
   endpoint to get current extremities and work backwards from there to rebuild the DAG. This doesn't
   fix a scenario where the server has a total loss of room information, but a step towards recovery
   is always better than none. A server may use this feature after data loss if a user happens to have
   a cache of their room list still, for example.

   Other MSCs in this space include:
   * [MSC2316: Federation queries to aid with database recovery](https://github.com/matrix-org/matrix-spec-proposals/pull/2316)
   * [MSC2314: A method to backfill room state](https://github.com/matrix-org/matrix-spec-proposals/pull/2314)
     (**MSC2314 is a strong alternative to this MSC.**)

2. If a lightweight server were to want to send an event, such as a redaction or a ban, it can use
   this MSC's new endpoint to get accurate-enough `prev_events` for its event, then inspect current
   state to populate `auth_events` and send the event to all other servers in the room.

   Currently policy servers manage a bot account to accomplish this task - see above regarding how
   fiddly that can be. Eliminating the need to manage a bot account is a desirable feature for the
   Foundation's policyserv implementation.

## Proposal

A new endpoint is added to the [Server-Server API](https://spec.matrix.org/v1.16/server-server-api/)
to retrieve the current extremities (as event IDs) the server has in the given room. The endpoint
requires normal authentication for federation endpoints and MAY be rate limited. "Current" is at the
time of the request and has no guarantee of being accurate after the request is completed.

Servers should note that this endpoint returns the same information which would be supplied in the
`prev_events` for an event, if they were to send one.

Request shape:

```
GET /_matrix/federation/v1/extremities/{roomId}
Authorization: X-Matrix ...
```

(there are no query parameters or request body)

Response shape:

```
Content-Type: application/json
{
  "prev_events": ["$event1", "$event2"]
}
```

The response is contained in an object for future expansion. `prev_events` is required, and MUST have
at least one event ID entry in its array.

The following errors may be returned:

* 403 / `M_FORBIDDEN` - The requesting server is not in the room, or is excluded from the room via
  `m.room.server_acl`.
* 404 / `M_NOT_FOUND` - The server is not aware of the room.

Servers SHOULD NOT attempt to fully resolve the DAG before returning a response - the calling server
is expected to handle the extremities as needed. For minimal/lightweight policy server implementations,
this may mean requesting state at each event and merging the results for a good enough representation
of current state - specific handling is left as an implementation detail.

## Potential issues

Lightweight server implementations may find it difficult to handle responses where `prev_events` has
more than a single entry. They could attempt to run state resolution over the information they learn,
or they could do a "simple" merge to get to somewhere close enough depending on their use case. They
may also decide to just wait a little bit and hope that the remote server self-resolves the DAG or
try another server.

## Alternatives

The major alternatives are discussed in the introduction for this proposal.

## Security considerations

**Author's note**: Specifics on how to exploit Matrix or this MSC are intentionally omitted from this
proposal. Refer to the [Security Disclosure Policy](https://matrix.org/security-disclosure-policy/)
to discuss such concerns and details.

Spammers can already use a few different tools to flood a room and this MSC makes it easier to do so.
This MSC does not have mitigation for such spam and instead expects that other aspects of Matrix will
take care of it. Features such as rate limits, policy servers, moderation tooling generally, and
server-side (implementation-specific) DAG/room simplification may be of interest to server developers
and communities on Matrix.

## Unstable prefix

While this proposal is not considered stable, implementations should use
`/_matrix/federation/unstable/org.matrix.msc4370/extremities/{roomId}` in place of the stable endpoint.

## Dependencies

This MSC has no direct dependencies, but is primarily intended to be useful to [MSC4284: Policy Servers](https://github.com/matrix-org/matrix-spec-proposals/pull/4284).
