# MSC4248: Pull-based presence

_TODO: msc number may change_

Currently, presence in Matrix is a great tax on every server involved in the process.
Matrix presence currently works by having the client tell the homeserver what the user's presence is
(online, unavailable, or offline). The homeserver then takes this information, and
[sends it to every server that might be interested in it](https://spec.matrix.org/v1.13/server-server-api/#presence).

This, however, is massively inefficient, wasteful, and very expensive for all parties involved.
This is why many servers have disabled federated presence, and as such why many clients do not support
presence in the first place.

This MSC proposes a new model for presence in Matrix, one which completely replaces the current EDU presence
system with one that is pull-based. This new model will save on bandwidth and CPU usage for all servers,
and reduces the amount of wasted data being sent around the internet to uninterested servers and clients alike.

## Proposal

Currently, on Matrix, when a user updates their presence, their homeserver receives this,
and then calculates which servers may be interested in this information.
It then opens connections to all of these servers, and sends them the presence information
in an EDU.
Then, the receiving server processes the data, and sends it to any clients connected that
may be interested in this information. Then, the client can choose to display it.

This proposal instead suggests a different approach:

When the user updates their presence, their homeserver will instead store this information locally, and not
send it out to other servers. Then, other servers will instead request this information from the homeserver
when they need it.

Clients would still request presence information from the homeserver in the normal fashion
(i.e. via sync and the `/presence/{userId}/status` endpoint), so this would not require any change
from clients.

Servers should instead calculate which users they are interested in, and then request presence information
on a timed interval from the respective homeservers. This would be done via a new federation endpoint,
`/federation/v1/query/presence`. This endpoint would allow servers to look up, in bulk, the presence
information of users that the server is explicitly interested in.

### New flow

The new flow can be summarised as follows:

1. User 1 updates their presence on server A
2. Server A stores the new presence, and when it was set
3. Server B queries server A for the presence of users 1, 2, and 3,
   including when it last saw their presence change
4. Server A checks its local presence data for users 1, 2, and 3, and returns
   only fresh presence information to server B (i.e. only if the presence has changed)
5. Server B updates its local presence data for users 1, 2, and 3, and sends this
   to clients that are interested in this information
6. Server B waits for the next interval to query server A again.

This new flow is much more efficient as it allows each server to independently track the presence
of users and only request updates when they are needed. This reduces the amount of data
being sent around the network and reduces the amount of CPU time spent processing this data.

#### New federation endpoint: `/federation/v1/query/presence`

__Servers must implement the new endpoint: `POST /federation/v1/query/presence`__.

The request should be as such:

`POST /federation/v1/query/presence`

```json
{
    "@user1:server.a": 1735324578000,  // server b last saw user1's presence change at this point in time (unix millisecond timestamps)
    "@user2:server.a": 0,  // server b has never seen presence for user2
    // "@user3:server.c": 0  // presence should only be requested for users on the same server, i.e.
                             // server A cannot respond with presence information for server C
}
```

Note that as commented, homeservers should NEVER request presence information by proxy.
In addition, servers must never respond with presence information for users on other servers.
This prevents leaking information about users to servers that should not have it (e.g. blocked users),
and prevents serving stale presence information.

#### 200 OK response

The response from the server should follow a similar structure, but instead include a
[m.presence content](https://spec.matrix.org/v1.13/client-server-api/#mpresence) as the value. For example:

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

Servers should omit users that have not updated their presence since the last time the querying server.
The returned object may be empty if no users have updated their presence since the last query.

#### 403 Forbidden response

If the remote server is not federating presence, or if the requesting server is being explicitly
blocked by the remote server, it should respond with
[HTTP 403 Forbidden](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403).

For example:

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "Federation disabled for presence",
    "reason": "This server does not federate presence information"
}
```

#### 413 Content too large response

Furthermore, servers should limit the number of users they simultaneously query for presence information.
The limitation should be configurable and decided per-server, but ideally would not be too large as to
prevent timeouts and huge payloads.
A reasonable default would be 500 users per-query.
Additionally, servers should explicitly respond with [HTTP 413 Content too large](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/413)
in the event that the requested users exceeds the configured amount, and the server should indicate
the maximum amount of users that can be queried in the response body. For example:

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "Too many users requested",
    "max_users": 500
}
```

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).
