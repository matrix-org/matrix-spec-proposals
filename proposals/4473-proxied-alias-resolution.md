# MSC4473: Proxied room alias resolution

Room aliases provide a way to assign memorable addresses to otherwise random room identifiers. For
example, `#matrix:matrix.org`. Typically, users will provide aliases to their clients, which the
client (and/or server) then needs to resolve to a room ID, depending on the action to take. In order
to do this, clients will ask the server to resolve the alias for them, which returns the associated
room ID, and a list of servers who may be in the room.

However, alias resolution over federation depends on querying only the authoritative owner over the
alias (the server whose name is in the alias itself). This presents a number of problems that can
often result in an alias being unresolvable, and users have to go hunting for the room ID on their
own.

This proposal will detail a modification to the room alias resolution endpoints that allows them to
be *proxied*, enabling higher availability of room aliases, without having to resort to less ideal
means.

## Proposal

Quick glossary:

- *Authoritative* or *origin*: used to refer to the server which owns the room alias (the server
  whose name appears in the alias itself)
- *Receiving server*: the server which is receiving a query request. May or may not be the *origin*.
- *Sending server*: the server which is sending a query request.

Note: *authoritative* and *origin* server are used interchangeably in this proposal to refer to the
server which an alias belongs to, i.e. the server name in the alias.

The approach taken in this proposal is inspired by the existing signing key discovery system:
<https://spec.matrix.org/v1.18/server-server-api/#querying-keys-through-another-server>.
As such, it is assumed that servers implementing this proposal either have a concept of trusted
servers, or at least key notary servers. These servers already have an implicitly high amount of
trust.

When this proposal is implemented, [`GET /_matrix/federation/v1/query/directory`][fed-1] should be
queried as normal - there are no new query parameters.

[fed-1]: https://spec.matrix.org/v1.18/server-server-api/#get_matrixfederationv1querydirectory

### Signing & Expiry

If the server being queried (receiving server) is the server which owns the
room alias, it SHOULD [sign the response](https://spec.matrix.org/v1.18/appendices/#signing-json).

When a homeserver signs the query response, it MUST additionally include an `expires_ts` field with
a unix timestamp (milliseconds) for when servers should consider the response stale, and evict it
from their cache. So, the updated response body would look like:

```json5
{
   "room_id": "!c10y-t1HZB9jgYr9mmaKtMDsS19HXbWRFc6d0bWGVYU",
   "servers": [
      "nexy7574.co.uk",
      // ...
   ],
   "expires_ts": 1778969913414,
   "signatures": {
      // ...
   }
}
```

If the sending server receives a signed response, it MUST [verify the signature][sig-verify] of the
origin server (signatures from other servers are ignored). If the signature is forged/corrupt, or
the key used to sign the response expired before the request was made, the response is discarded,
and the server should be treated as unreachable.

[sig-verify]: https://spec.matrix.org/v1.18/appendices/#checking-for-a-signature

Furthermore, if the `expires_ts` is in the past, the response is again discarded. The server MAY
choose to abort further resolution attempts on account of the origin itself being reachable, but
returning bogus data (the chances of a third-party acquiring a fresh response are low).

Servers MUST NOT ever ret the cached entry past `expires_ts`. Likewise, servers MUST NOT re-use
a cached response if the key used to sign it itself expires before `expires_ts`, and it cannot
be refreshed. Servers MAY instead choose the lower of the two timestamps when deciding the cache
entry's TTL, rather than attempting to re-validate the signature.

If a sending server receives a signed response, it SHOULD store the signature and expiry timestamp,
as this will allow it to act as a proxy (much like how third party servers can be used to fetch
signing keys). If the signature and expiry timestamp are not stored, the server can only proxy by
forwarding the request, as it will be unable to serve from its cache.

### New room alias resolution steps

The sending server MUST first attempt to contact the origin server directly. If the origin server
responds, and the response passes any applicable checks in [§ Signing & Expiry](#signing--expiry),
the sending server MUST use that response and cease any further resolution. This additionally means
sending servers who receive an error response, such as `404 M_NOT_FOUND`, should use that response,
NOT attempt to query other servers.

If the sending server is unable to reach the room alias server, it MAY attempt to contact other
servers it trusts (for example, configured notary servers). The sending server MUST NOT allow its
clients to define which servers are queried, unlike with room joins & summaries.

Currently, if a homeserver receives a request for an alias which does not belong to it, the request
is refused, returning an error code. If this proposal is implemented, the behaviour of queries is
instead changed to the following:

1. If the queried room alias is owned by receiving server, return as normal (see above).
2. If the queried room alias belongs to a different server,
   the receiving server should attempt to query the room alias origin directly.
   1. If the room alias origin responds with `404 M_NOT_FOUND`, this is returned to the sending
      server.
   2. If the room alias origin responds with a successful response, the response is
      [checked](#signing--expiry).
   3. If the response is valid, it is directly returned to the sending server, and the process ends
      here.
   4. If the response is invalid, or some other error is returned, discard the response and continue.
3. If the receiving server has a cached entry for the queried room alias, AND it passes
   [the same checks](#signing--expiry) at the time of the request, the server MAY
   return the cached response (see next paragraph).
   1. The sending server MUST verify that the authoritative server signed the response it received,
      discarding it if the signature is missing or corrupt.
4. Otherwise, resolution is impossible, and `502 M_NOT_FOUND` is returned (see below).

Step 3 specifically qualifies that servers *MAY* return the cached response, because implementations
may prefer to check that the alias is a canonical alias of a room it is a resident of. Servers MAY
choose not to return aliases which they cannot find in canonical alias events, however this is up to
the receiving server's discretion.

Servers MUST NOT cache responses from servers other than the authoritative server. This prevents an
effect where a stale response may be incorrectly "freshened" by a second-degree server, and then
passed on to a third-degree server, so on. Or visually, in a chain of
`ORIGIN <- A <- B <- C`, `A` can cache the response from `ORIGIN`, and `A` can return that cached
response to `B` (see step 3), but `B` *MUST NOT* cache that response. If `C` attempts to query `B`,
`B` will perform the same steps `A` did, meaning it will always return a fresh response, or a
not-found error.
<!-- TODO: ^ Is this still necessary with expires_ts? I think it still seems like a good idea nonetheless -->

Since origin servers MAY NOT return signatures, unsigned responses MUST NOT be considered for
step 3. Both sides of the connection being required to validate the checks at the time of the
request should prevent this anyway, but this clause is defined specifically to allow servers to
continue the current behaviour of using these responses with a local cache to reduce the number of
lookups performed by local users.

Servers who receive a `502 M_NOT_FOUND` response MAY continue discovery with another trusted server.
However, servers who receive a `404 M_NOT_FOUND` MUST terminate discovery, as this means the origin
server has reported the alias no longer exists. `502` is used to distinguish the *proxy* server not
being capable of resolving the alias from `404`, meaning the origin reports that the alias no longer
exists.
<!-- TODO: Errors aren't typically signed, so this means a malicious proxy server could always
return 404 to cause a (rather pathetic) denial of service. Maybe the error should be signed? Doesn't
DNS have something like this with DNSSEC? -->

## Potential issues

See [§ Security Considerations](#security-considerations).

This proposal is designed in a manner that is intentionally 100% backwards compatible with existing
implementations, so no potential issues (other than security considerations) are known at this time.

## Alternatives

None.

## Security considerations

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
| `GET /_matrix/federation/v1/query/directory` | `GET /_matrix/federation/unstable/uk.timedout.msc4473/query/directory` |

Once stabilised, the endpoint can be switched back to the already existing endpoint transparently.

## Dependencies

None
