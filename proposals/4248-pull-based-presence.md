# MSC4248: Pull-based presence

_TODO: MSC number may change_

Currently, presence in Matrix imposes a considerable burden on all participating servers.  
Matrix presence works by having the client notify its homeserver when a user changes their presence  
(online, unavailable, or offline). The homeserver then delivers this information to every server that  
might be interested, as described in the [specification’s presence section](https://spec.matrix.org/v1.13/server-server-api/#presence).

However, this approach is highly inefficient and wasteful, requiring significant resources for all  
involved parties. Many servers have therefore disabled federated presence, and many clients have  
consequently chosen not to implement presence at all.

This MSC proposes a new pull-based model for presence that replaces the current “push-based” EDU  
presence mechanism. The aim is to save bandwidth and CPU usage for all servers, and to reduce the  
amount of superfluous data exchanged between uninterested servers and clients.

## Proposal

Today, when a user’s presence is updated, their homeserver receives the update and determines  
which remote servers may need this information. It then sends an EDU to those servers with the user’s  
updated presence. Each remote server processes the data and relays it to its interested clients,  
which may then display the new presence status.

This MSC suggests a different approach:

1. When the user updates their presence, their homeserver stores the new status but does  
   not send it to other servers immediately.  
2. Other servers periodically query this homeserver for presence updates, in bulk, for the  
   users they care about.  
3. The homeserver returns only new or changed presence information since the last query.  

Clients would continue to request presence in the usual manner (for instance, through `/sync`  
and the `/presence/{userId}/status` endpoint), meaning no client-side change is strictly necessary.

Servers would calculate which users they are interested in and query presence data on a  
timed interval from the relevant homeservers. The new proposed federation endpoint is:  
`/federation/v1/query/presence`. Through this endpoint, servers can request presence  
information for specific users on that homeserver, in a bulk query.

### New flow

1. User 1 updates their presence on server A.  
2. Server A stores the new presence and timestamps it.  
3. Server B queries server A for the presence of users 1, 2, and 3, along with the time  
   it last observed their presence updates.  
4. Server A checks its local presence records and replies with the updated presence  
   statuses for those users (only if there have been changes).  
5. Server B updates its local presence records and relays the information to any  
   interested clients.  
6. Server B repeats the query at the next scheduled interval.  

By only requesting fresh data when needed, each server can independently maintain presence  
information without excessive data broadcast. This cuts down on network usage and CPU load.

#### New federation endpoint: `/federation/v1/query/presence`

**Servers must implement:**

```
POST /federation/v1/query/presence
```

**Request body example:**

```json
{
    "@user1:server.a": 1735324578000,
    "@user2:server.a": 0
}
```

Here, the request indicates that `@user1:server.a` had its presence last updated at Unix  
timestamp `1735324578000` (milliseconds), as seen by the querying server. For `@user2:server.a`,  
the querying server has no stored timestamp (0).

Homeservers **must not** request presence information by proxy; presence queries **must only**  
concern users of the homeserver being queried. Similarly, the responding server must only  
provide presence data for its own users.

#### 200 OK response

If successful, the response provides an object mapping user IDs to  
[`m.presence` content](https://spec.matrix.org/v1.13/client-server-api/#mpresence). For example:

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

The server **must not** include users whose presence has not changed since the querying  
server last updated. It is valid for the response object to be empty if no new data exists.

#### 403 Forbidden response

If the remote server does not federate presence, or explicitly disallows the requesting  
server, it should respond with an [HTTP 403 Forbidden](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/403),  
such as:

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "Federation disabled for presence",
    "reason": "This server does not federate presence information"
}
```

#### 413 Content too large response

To prevent timeouts and large payloads, servers should cap the number of presence queries  
allowed in a single request. This limit is configurable per server, but a recommended  
default is 500 users. If a request exceeds this limit, the server should respond with an  
[HTTP 413 Payload Too Large](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/413),  
for example:

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "Too many users requested",
    "max_users": 500
}
```

## Potential issues

(Describe any potential pitfalls in implementing this model.)

## Alternatives

(Discuss alternative approaches and why they might or might not be suitable.)

## Security considerations

(Outline any security or privacy concerns relevant to this approach.)

## Unstable prefix

If a proposal is implemented before it is finalised in the spec, implementers must ensure  
compatibility with the final design. Typically, this means using `/unstable` endpoints and  
appropriate vendor prefixes. This section should detail the temporary endpoints, feature  
flags, or other requirements for experimental implementations, per  
[MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324).

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy, and MSCzzzz (which have not yet been accepted at  
the time of writing).
