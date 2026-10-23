# MSC4473: Proxied room alias resolution

Room aliases provide a way to assign memorable addresses to otherwise random room identifiers. For
example, `#matrix:matrix.org` is a user-friendly pointer to
`!L58ME6ufiP49v97UIOBIpvWKEgj4912JmECPuDzlvCI` (at the time of writing).
Typically, users will provide aliases to their clients, which the client then needs to resolve to a
room ID for further use. In order to do this, clients will ask the server to resolve the alias for
them via the [`GET /_matrix/client/v3/directory/room/{roomAlias}`][c2s-resolve].
The user's homeserver will then check its local cache and/or database, but if it cannot find an appropriate result for the
alias, the server will then contact
[`GET matrix-federation://{authority}/_matrix/federation/v1/query/directory`][s2s-resolve] to fetch
the details over federation.

[c2s-resolve]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3directoryroomroomalias
[s2s-resolve]: https://spec.matrix.org/v1.18/server-server-api/#get_matrixfederationv1querydirectory

However, alias resolution over federation depends on querying only the authoritative owner over the
alias (the server whose name is in the alias itself). This presents a number of problems that can
often result in an alias being unresolvable, which tends to lead to confused users having to ask
around for links, or even worse, having to try to find the underlying room ID on their own, which
may allow a malicious actor to lie to them in order to get them to join a room of their choosing.

These problems are not uncommon or unexpected either. Servers can temporarily go down for a few
hours every now and again for updates or unexpected outages, and sometimes unexpected outages may
be prolonged to a number of days. A great example of this was when
[matrix.org was offline for 24 hours](https://matrix.org/blog/2025/10/post-mortem/). For those
24 hours, there were constant complaints from users on other servers who were now unable to join
rooms that at the time hosted their canonical alias(es) on `matrix.org`, which was now unreachable.
This also meant that `#foundation-office:matrix.org`, the Matrix.org Foundation Office, could not
be joined without knowing someone who was already in the room that could drop you a join link with
alternative vias for routing.

And that's just unexpected outages. There is a growing trend in online censorship globally that
threatens to disrupt day-to-day connectivity of swathes of the Matrix network.

This highlights a critical weak-point in the decentralised network: while rooms themselves are
network-partition resistant, and you can even join rooms through other servers if the desired one is
unreachable, *you have to already know the room ID* and *at least one other server in the room*.
Most people aren't going to remember that they can join
`!L58ME6ufiP49v97UIOBIpvWKEgj4912JmECPuDzlvCI` via `t2l.io`, or that
`!8cR4g-i9ucof69E4JHNg9LbPVkGprHb3SzcrGBDDJgk` can be joined through `continuwuity.rocks`. And even
if they *did* know this, most client UIs right now don't provide an easy way for users to specify
vias with room IDs, unless they manually type out a join link and click it (or sometimes run
`/join`).
This means that effectively, if the room alias can't be resolved, you can't join a room.
You might not even be able to figure out if you're even joined to a room an alias points to if your
server doesn't cache the last known response long enough, since your client can't check if you're
joined to `#matrix:matrix.org` without resolving the alias in the first place!

This proposal will outline a new way to resolve room aliases that makes them almost as
partition-resistant as the rooms they point towards, allowing aliases to survive their origins
going down or otherwise becoming unreachable, while still ensuring the origin maintains as much
control over the alias as possible.

## Proposal

Quick glossary:

- *Authoritative* or *origin*: used to refer to the server which owns the room alias (the server
  whose name appears in the alias itself)
- *Alias*: The actual room alias itself (shortened to alias for brevity).
- *Proxy server(s)*: Servers which are capable of forwarding the lookup request.
- *Receiving server*: the server which is receiving a query request. May or may not be the *origin*.
- *Sending server*: the server which is sending a query request.

Note: *authoritative* and *origin* server are used interchangeably in this proposal to refer to the
server which an alias belongs to, i.e. the server name in the alias.

The approach taken in this proposal is inspired by the existing signing key discovery system:
<https://spec.matrix.org/v1.18/server-server-api/#querying-keys-through-another-server>.
As such, it is assumed that servers implementing this proposal either have a concept of trusted
servers, or at least key notary servers. These servers already have an implicitly high amount of
trust.

### New server-server endpoint

In order to facilitate a reasonably different response body to the existing, the version of the
endpoint is bumped, although its shape remains familiar:

`GET /_matrix/federation/v2/query/directory`

Rate-limited: no

Authenticated: yes

Query params:

- `room_alias` (string, required): The full room alias to resolve (`#example:matrix.example`)

Responses:

`200 OK`: The resolved room ID, a list of servers in the room, when this response should be
considered stale, and signatures to attest the authenticity:

| key          | type                  | description                                                                     |
| ------------ | --------------------- | ------------------------------------------------------------------------------- |
| `room_id`    | string                | The resolved room ID                                                            |
| `servers`    | \[string\]            | A list of servers in the room                                                   |
| `expires_ts` | integer               | A timestamp in unix milliseconds when this response should be considered stale. |
| `signatures` | [Signatures][signing] | Any signatures required to attest to the authenticity of the response.          |

[signing]: https://spec.matrix.org/v1.18/appendices/#signing-details

```json
{
   "room_id": "!example",
   "servers": ["server1.example", "server2.example"],
   "expires_ts": 1778991778468,
   "signatures": {
      "origin.example": {
         "ed25519:foobar": "OmJsb2JjYXQgbW9ub2NsZTogOmNvb2tpZTogOmZpc2g6Cg=="
      }
   }
}
```

`404 M_NOT_FOUND`: A **signed** standard error response:

| key          | type                  | description                                                            |
| ------------ | --------------------- | ---------------------------------------------------------------------- |
| `errcode`    | string                | An error code.                                                         |
| `err`        | string (optional)     | A human-readable error message.                                        |
| `signatures` | [Signatures][signing] | Any signatures required to attest to the authenticity of the response. |

`502 M_NOT_FOUND`: A standard error response:

| key          | type                  | description                     |
| ------------ | --------------------- | ------------------------------- |
| `errcode`    | string                | An error code.                  |
| `err`        | string (optional)     | A human-readable error message. |

### Signing & Expiry

If the receiving server owns the alias being queried, and the alias is known, an appropriate
response is generated, ready for signing. The server MUST attach an expiry to the response -
the recommended (and maximum) time period is **7 days**, but it MUST be no less than 1 minute.
The server MUST then [sign the response][signing], before returning it.

If the receiving server owns the alias being queried, but the alias is *not* known, a `HTTP 404`
response is generated, with `errcode` set to `M_NOT_FOUND`. The server MUST sign the error response
before returning it. The signature is required so that the sending server can pass the response
along if it happens to be acting as a proxy - this allows the error response to be authoritative,
thus signalling to downstreams that resolution should halt.

If the sending server receives a signed response, it MUST [verify the signature][sig-verify] of the
authoritative server (signatures from other servers are ignored).
If the signature cannot be verified, or the key used to sign the response expired before the request
was made, the response is discarded, and the server should be treated as if it were unreachable.

[sig-verify]: https://spec.matrix.org/v1.18/appendices/#checking-for-a-signature

Furthermore, if the `expires_ts` is in the past, the response is again discarded. The server MAY
choose to abort further resolution attempts on account of the origin itself being reachable, but
returning bogus data (the chances of a third-party acquiring a fresh response are low).

Servers MUST NOT retain the cached entry past `expires_ts`. Likewise, servers MUST NOT re-use
a cached response if the key used to sign it itself expires before `expires_ts`, and it cannot
be refreshed. Servers MAY instead choose the lower of the two timestamps when deciding the cache
entry's TTL, rather than attempting to re-validate the signature.

If a sending server receives a signed response, it SHOULD store the signature and expiry timestamp,
as this will allow it to act as a proxy (much like how third party servers can be used to fetch
signing keys). If the signature and expiry timestamp are not stored, the server can only proxy by
forwarding the request, as it will be unable to serve from its cache.

### New room alias resolution steps

The sending server MUST first attempt to contact the origin server directly. If the origin server
responds (or returns a signed `404 M_NOT_FOUND` error), and the response passes any applicable
checks in [§ Signing & Expiry](#signing--expiry), the sending server MUST use that response and
cease any further resolution.

If the sending server is unable to reach the room alias server, it MAY attempt to contact other
servers it trusts (for example, configured notary servers). The sending server MUST NOT allow its
clients to define which servers are queried, unlike with room joins & summaries. If the server does
not trust any other servers, it should return `M_NOT_FOUND` to the requesting client. Proxy servers
MUST NOT attempt to query other proxy servers over federation, in order to prevent recursion loops.

Currently, if a homeserver receives a request for an alias which does not belong to it, the request
is refused, returning an error code. If this proposal is implemented, the behaviour of queries is
instead changed to the following:

1. If the queried room alias is owned by receiving server, return as normal (see above).
2. If the queried room alias belongs to a different server,
   the receiving server should attempt to query the room alias origin directly. The receiving server
   is now a *proxy server*.
   1. If the room alias origin responds with a [valid signed](#signing--expiry) `404 M_NOT_FOUND`,
      this is returned to the sending server. Resolution is halted here, the alias does not exist.
   2. If the room alias origin responds with a successful response, the response is
      [checked](#signing--expiry).
   3. If the response is valid, it is directly returned to the sending server, and the process ends
      here.
   4. If the response is invalid, or some other error is returned, discard the response and continue.
3. If the proxy server has a cached entry for the queried room alias, AND it passes
   [the same checks](#signing--expiry) at the time of the request, the proxy server MAY
   return the cached response (see next paragraph).
   1. The sending server MUST verify that the authoritative server signed the response it received
      from the proxy server, discarding it if the signature is missing or corrupt.
4. Otherwise, resolution is impossible, and unsigned `502 M_NOT_FOUND` is returned (see below).

Step 3 specifically qualifies that servers *MAY* return the cached response, because implementations
may prefer to check that the alias is a canonical alias of a room it is a resident of. Servers MAY
choose not to return aliases which they cannot find in canonical alias events, however this is up to
the receiving server's discretion.

If a sending server is itself later requested to act as a proxy server, it MAY use a cached response
it received from another proxy server, provided it still passes [the checks](#signing--expiry). Or,
in other words, this means a second degree server is allowed to serve the response a first-degree
proxy server gave it, provided it is still fresh.

It is important to remember that any server can be a proxy server and as such MUST run the full flow
defined above even if they already know they have a valid cached entry - the authoritative origin
MUST always be contacted before serving from a cache, in order to ensure the origin retains complete
control over the validity of the alias.

Servers who receive a `502 M_NOT_FOUND` response MAY continue discovery with another trusted server.
However, servers who receive a signed `404 M_NOT_FOUND` MUST terminate discovery, as this means the
origin server has reported the alias no longer exists.
`502` is used to distinguish the *proxy* server not being capable of resolving the alias from `404`,
meaning the origin reports that the alias no longer exists, further re-enforced with a signature.

### Servers that don't support v2

If the server being queried is the authoritative server, and it returns `404 M_UNRECOGNIZED`, the
sending server SHOULD re-try the request with the [v1 endpoint][s2s-resolve]. As the v1 endpoint is
not signed, the response from the v1 endpoint MAY be cached for **local use only**, and MUST NOT be
returned as a proxy response under any circumstances.

If the server being queried is NOT the authoritative server, and it returns `404 M_UNRECOGNIZED`,
the sending server SHOULD re-try the request with a different proxy server, and assume that the one
that returned the error does not support being a proxy server.

## Potential issues

See [§ Security Considerations](#security-considerations).

No other unsolved issues are considered at this time.

## Alternatives

None.

## Security considerations

<!-- TODO: Needs a gloss-over after v2 re-definition -->

**Room aliases are mutable**. By not exclusively querying the authoritative server, this proposal
does open up the possibility for stale responses to be considered valid, which carries several
concerns, including:

1. The room alias may have since been changed to point at a different room.
2. The server names reported to be in the room may no longer be in the room.
3. The alias may be temporarily pointed at a malicious room.
4. The receiving server might lie.
5. This effectively introduces a recursive lookup functionality.

The author believes appropriate mitigations for new security concerns introduced by this proposal
have been implemented. By retaining the behaviour that the authoritative server should always be
contacted first, the likelihood of a poisoned response is lowered.

If the authoritative server can't be reached, the sending server then queries third parties it
already implicitly trusts, and at no point is such control handed over to a user
(who may be malicious, see below).

Then, each third party must contact the authoritative server before checking its cache. This
resolves a problem where Alice may not be able to contact Charlie, but can contact Bob, and Bob can
contact Charlie. Since, in this case, the response would be fresh from the authoritative server,
assuming it has a (valid) signature, the receiving server can return the response it received
directly. This ensures that the sending server receives a fresh response, however, it does NOT cache
it, as it may not be aware of an appropriate TTL. Since servers cannot cache non-authoritative
responses, they cannot return them to other servers that may ask either.

If the authoritative server cannot be reached, non-stale cache entries may be returned. This allows
the alias to continue to function for a limited amount of time without the origin's involvement, but
ultimately ensures it does not live so long that the origin effectively loses control over the
alias.

## Unstable prefix

While this proposal is unstable, `uk.timedout.msc4473` should be used as an unstable prefix for the
directory route:

| Stable | Unstable |
| ------ | -------- |
| `GET /_matrix/federation/v2/query/directory` | `GET /_matrix/federation/unstable/uk.timedout.msc4473/query/directory` |

After the proposal is stabilised, servers SHOULD continue to accept requests to the unstable
endpoint for a period of time, which itself is at the discretion of the implementation.

## Dependencies

None
