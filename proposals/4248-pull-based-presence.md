# MSC4248: Pull-based presence

Currently, presence in Matrix imposes a considerable burden on all participating servers when
users are engaging in large rooms, such as Matrix HQ, the Raspberry Pi room,
and the Python room.

Matrix presence currently works by having the client notify its homeserver when a user changes
their presence (online, unavailable, or offline, and optionally a custom status message).
The homeserver then delivers this information to every server that might be interested,
as described in the
[specification's presence section](https://spec.matrix.org/v1.13/server-server-api/#presence).

However, this approach is highly inefficient and wasteful, requiring significant resources
for all involved parties. Many servers have therefore disabled federated presence, some have
even gone as far as to disable local presence, and many clients have consequently chosen
not to implement presence at all, because many maintainers simply don't see the value in
presence.

This MSC proposes a new optional pull-based model for presence that works alongside the current
"push-based" EDU presence mechanism.
The aim of "push-based presence" is to save bandwidth and CPU usage for all servers, and to
reduce superfluous data exchanged between uninterested servers and clients.

## Proposal

Today, when a user's presence is updated, their homeserver receives the update and decides
which remote servers might need it. It then sends an EDU to those servers. Each remote
server processes and relays the data to its interested clients. This creates substantial
bandwidth usage and duplication of effort.

In contrast, this MSC suggests a pull-based approach:

1. When the user updates their presence, their homeserver stores the new status without
   pushing it to other servers.
2. Other servers periodically query that homeserver for presence updates, in bulk, for the
   users they track.
3. The homeserver returns only presence information that has changed since the last query.

Clients continue to request presence as before (e.g. `/sync` and
`/presence/{userId}/status`). No client-side changes are strictly required.

Servers instead calculate which users they are interested in and query the homeservers of
those users at intervals. The new proposed federation endpoint is
`/federation/v1/query/presence`. This allows servers to request presence data in bulk for
the relevant users on that homeserver.

Servers should offer the option to enable push-based presence, pull-based presence, or both.

### New flow

1. User 1 updates their presence on server A.
2. Server A stores the new presence and timestamp.
3. Server B queries server A about users 1, 2, and 3, including the time it last observed
   their presence changes.
4. Server A checks its data for these users and responds only with updated presence info.
5. Server B updates its local records and informs any interested clients.
6. Server B repeats the query at the next interval, plus a random scatter period.

By pulling presence only when needed, each server can maintain accurate user status without
excessive data broadcasts. This is significantly more efficient than pushing updates to
every server that might be interested.

Servers **should** implement a "scatter period" in their intervals to avoid synchronised
bursts of traffic, ideally in the magnitutde of up to a few minutes. By adding or subtracting
a random value from the query interval, servers can automatically space out their requests,
to avoid overloading the remote server if it is popular.
For example, if server A fetches presence every 10 minutes, it could run the next fetch cycle
a few minutes early or a few minutes late, to avoid sporadic traffic spikes.

#### New federation endpoint: `/federation/v1/query/presence`

**Servers must implement:**

`POST /federation/v1/query/presence`

**Request body example:**

```json
{
    "@user1:server.a": 1735324578000,
    "@user2:server.a": 0
}
```

Here, `@user1:server.a` was last updated at `1735324578000` (Unix milliseconds) as seen by
the querying server. For `@user2:server.a`, the querying server has no stored timestamp.

Homeservers **must not** proxy requests for presence: only users on the homeserver being
queried should appear in the request. Likewise, the responding server must only provide
presence data for its own users.

#### 200 OK response

If successful, the response is a JSON object mapping user IDs to
[`m.presence` data](https://spec.matrix.org/v1.13/client-server-api/#mpresence). For example:

```json
{
    "@user1:server.a": {
        "presence": "online",
        "last_active_ago": 300
    },
    "@user2:server.a": {
        "presence": "unavailable",
        "status_msg": "Busy, try again in 5 minutes",
        "last_active_ago": 0
    }
}
```

Users whose presence has not changed since the last time the querying server checked should
not appear in the response. An empty response body is valid if no updates exist.

#### 403 Forbidden response

If the remote server does not federate presence or explicitly blocks the querying server, it
should respond with
[HTTP 403 Forbidden](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403):

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "Federation disabled for presence",
    "reason": "This server does not federate presence information"
}
```

Servers that receive this response should not retry this query for a long period of time, as this
is likely a permanent restriction.

#### 413 Content too large response

To avoid large payloads and timeouts, servers should cap the number of presence queries in a  
single request. A recommended default limit is 500 users. If a request exceeds this limit,  
respond with [HTTP 413 Payload Too Large](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/413):

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "Too many users requested",
    "max_users": 500
}
```

## Potential issues

1. **Stale data**: If a server's polling interval is long, clients may see outdated status.  
   However, this trade-off is often preferable to constant pushing of updates, which wastes
   bandwidth and CPU.
2. **Performance bursts**: Polling in bulk might cause periodic spikes in traffic. In
   practice, scheduling queries reduces overhead compared to perpetual push notifications.
3. **Server downtime**: If a homeserver is unavailable, remote servers cannot retrieve
   updates. This is still simpler to handle than a push-based system that continually retries.
4. **Partial coverage**: Each server must poll multiple homeservers if users span many
   domains. This is still more controlled than blindly receiving all presence EDUs from
   across the federation.
5. **Implementation complexity**: Homeservers must track timestamps for each user's presence
   changes. Despite this, the overall load and bandwidth consumption should be lower than the
   push-based approach.

## Alternatives

1. **Optimising push-based EDUs**: Servers could throttle or batch outgoing presence. While
   it reduces the raw volume of messages, uninterested servers might still receive unwanted
   data.
2. **Hybrid push-pull**: Pushing for high-profile users while polling for others can reduce
   traffic but complicates implementation. It also risks partially reverting to old,
   inefficient patterns.
3. **Deprecating presence**: Servers could disable presence entirely. This has already
   happened in some deployments but removes a key real-time user activity feature.
4. **Posting presence in rooms**: Embedding presence as timeline events could leverage
   existing distribution. However, this would complicate large, high-traffic rooms and let
   presence be tracked indefinitely. The added data overhead and privacy impact are worse
   than poll-based federation for many use cases.

## Security considerations

1. **Data visibility**: Because presence can reveal user activity times, queries and responses
   must be restricted to legitimate servers. Proper ACLs and rate-limiting are advised.
2. **Query abuse**: A malicious server could repeatedly query for large user lists to track
   patterns or overload a homeserver. Bulk requests limit overhead more effectively than
   repeated push, but the server should still implement protections.
3. **Privacy**: Even pull-based presence shares user status and activity times. Operators
   should minimise leakages and evaluate if presence is necessary for all users.
4. **Server authentication**: Proper federation checks remain critical to prevent
   impersonation or man-in-the-middle attacks.

## Unstable prefix

If this proposal is adopted prior to finalisation, implementers must ensure they can migrate  
to the final version. This typically involves using `/unstable` endpoints and vendor prefixes,  
as per [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324).

The vendor prefix for this MSC should be `uk.co.nexy7574.pull_based_presence`.

## Dependencies

This MSC does not depend on any other MSCs.
