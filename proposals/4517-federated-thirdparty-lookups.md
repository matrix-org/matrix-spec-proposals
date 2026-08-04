# MSC4517: Federated third-party network lookups

## Problem

Matrix has always had [third-party lookup
APIs](https://spec.matrix.org/v1.19/client-server-api/#third-party-networks): a client asks its
homeserver to map an identifier on a bridged network (an XMPP JID, an IRC channel, a phone number)
to the corresponding Matrix ghost user or portal room, and the homeserver asks its application
services via the corresponding [AS API](https://spec.matrix.org/v1.19/application-service-api/#third-party-networks).

However, this only works for bridges attached to *your own* homeserver. In practice bridges are
run by somebody else: if montague.example runs an XMPP bridge, only montague.example's users can
resolve `juliet@capulet.example` to `@_xmpp_juliet=40capulet.example:montague.example`.
Everyone else has to guess the ghost's MXID syntax by hand, which is miserable and bridge-specific.

The room directory already solved the equivalent problem years ago with
[`GET /publicRooms?server=`](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3publicrooms),
which lets a client browse another server's directory over federation. This proposal does the same
for third-party lookups.

## Proposal

### Client-Server API

The four third-party lookup endpoints gain an optional `server` query parameter, with the same
semantics as `/publicRooms?server=`:

* `GET /_matrix/client/v3/thirdparty/protocols?server=montague.example`
* `GET /_matrix/client/v3/thirdparty/protocol/{protocol}?server=montague.example`
* `GET /_matrix/client/v3/thirdparty/user/{protocol}?server=montague.example&...`
* `GET /_matrix/client/v3/thirdparty/location/{protocol}?server=montague.example&...`

If `server` is absent or names the local server, behaviour is unchanged. Otherwise the homeserver
proxies the query to the named server over the federation endpoints below and returns the result
unchanged. The `server` (and `access_token`) parameters are stripped before the protocol-specific
query fields are forwarded.

Response shapes are exactly as today; the only observable difference is whose bridges answered.

### Federation API

Three new server-authenticated endpoints, mirroring their client-server counterparts:

* `GET /_matrix/federation/v1/thirdparty/protocols` - returns the same body as
  `GET /_matrix/client/v3/thirdparty/protocols` (the protocol metadata of the target server's
  bridges, including `user_fields`/`location_fields` and `instances`).
* `GET /_matrix/federation/v1/thirdparty/user/{protocol}?field1=...` - returns
  `{"results": [...]}` where the array is the same as the client-server response.
* `GET /_matrix/federation/v1/thirdparty/location/{protocol}?field1=...` - likewise.

(The user/location arrays are wrapped in an object because federation responses are JSON objects;
there is no federation equivalent of `/thirdparty/protocol/{protocol}` since the caller can filter
`/protocols` itself.)

For example, resolving a JID for a DM:

```
GET /_matrix/federation/v1/thirdparty/user/xmpp?username=juliet&domain=capulet.example
```
```json
{
  "results": [
    {
      "userid": "@_xmpp_juliet=40capulet.example:montague.example",
      "protocol": "xmpp",
      "fields": { "username": "juliet", "domain": "capulet.example" }
    }
  ]
}
```

The queried server consults only its own application services when answering: it MUST NOT
re-delegate the query to a third server, both to avoid loops and so that the answering server is
always authoritative for the ghosts/portals it returns. These endpoints should be rate limited.

Failures (timeouts, unknown endpoints on older servers) should be treated by the proxying server
as empty results rather than errors: third-party lookup is a UI nicety layered over search, and a
dead remote bridge shouldn't break the rest of the search experience.

### Client behaviour

Clients which offer a server picker for the room directory can now offer the same picker (and the
same bridged-network dropdown) when starting DMs or searching for rooms, resolving typed
third-party identifiers via whichever server the user selected. `instances` (and their
`instance_id`s) are only meaningful on the server that reported them, so clients must track which
server each instance came from and pass the same `server` when querying it.

## Potential issues

This doesn't solve the discoverability problem of which servers expose which bridges.
For instance, it might be nice for a given homeserver at example.com to tell its users that
if they want to talk XMPP, they should do so via a federated third party lookup against the
xmpp protocol on xmpp.bridge.example.com.  This is deferred for a later MSC, given it can always
be configured clientside.

## Security considerations

These endpoints expose to any federating server what a local user could already query, so they
widen *who* can enumerate a bridge's mappings, not *what* is exposed. Bridges which consider their
mappings sensitive already have to enforce that in their `user`/`location` handlers (results are
also visible to any local user), but server implementations should rate limit the federation
endpoints to make bulk scraping of bridged networks impractical, as with the user directory.

The `server` parameter must be validated as a server name before being used as a federation
destination.

## Unstable prefix

Until this proposal is stable:

* the federation endpoints are served under
  `/_matrix/federation/unstable/org.matrix.msc4517.thirdparty/{protocols,user/{protocol},location/{protocol}}`;
* servers advertise support via `org.matrix.msc4517.thirdparty` in `unstable_features` on
  `GET /_matrix/client/versions`. (Servers which don't support it simply ignore `?server=` and
  answer locally, so clients should check before offering remote pickers.)

## Dependencies

None. [MSC4258](https://github.com/matrix-org/matrix-spec-proposals/pull/4258) (federated user
directory search) is a natural sibling - together they let a user on one server discover both
Matrix users and bridged third-party users/rooms via another server - but neither depends on the
other.
