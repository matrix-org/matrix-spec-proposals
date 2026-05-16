# MSCXXXX: Proxied room alias resolution

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

Note: *authoritative* and *origin* server are used interchangeably in this proposal to refer to the
server which an alias belongs to, i.e. the server name in the alias.

The approach taken in this proposal is inspired by the existing signing key discovery system:
<https://spec.matrix.org/v1.18/server-server-api/#querying-keys-through-another-server>.
As such, it is assumed that servers implementing this proposal either have a concept of trusted
servers, or at least key notary servers. These servers already have an implicitly high amount of
trust.

When this proposal is implemented, [`GET /_matrix/federation/v1/query/directory`][fed-1] should be
queried as normal. If the server being queried (receiving server) is the server which owns the
room alias, it SHOULD [sign the response](https://spec.matrix.org/v1.18/appendices/#signing-json).
If the server performing the query (sending server) caches room alias resolutions, it SHOULD store
this signature alongside the response. If a signature is returned, the sending server MUST verify
it - if it fails, the response is discarded and the server is treated as unavailable.

[fed-1]: https://spec.matrix.org/v1.18/server-server-api/#get_matrixfederationv1querydirectory

If the sending server is unable to reach the room alias server, it MAY attempt to contact other
trusted servers, such as configured key perspectives/notaries.

Currently, if a homeserver receives a request for an alias which does not belong to it, the request
is refused, returning an error code. If this proposal is implemented, the behaviour should instead
be changed to follow the following steps:

1. If the alias belongs to the receiving server, return as normal (see above).
2. If the alias belongs to a different server, attempt to query the alias' origin directly.
   1. If the alias origin responds, the response is checked for a signature.
   2. If the response has a valid, in-date signature, the origin's response is returned directly.
   3. If the response does not have a signature, or the signature is invalid, discard the response
      and continue.
3. If the receiving server has a cached entry for the queried alias, AND the signing key used to
   sign the cached response is still in-date at the time of the incoming request, the server MAY
   return the cached response.
4. Otherwise, resolution is impossible, and `404 M_NOT_FOUND` is returned.

Additionally, servers which cache room alias resolution responses SHOULD respect the
`Cache-Control` header in the response, if it is present. Servers MUST limit the maximum lifetime
of a cache entry to that of the signing key which signed the response, even if the `cache-control`
header indicates it should be stored for longer. For example, if the key expires in 12 hours,
but the room alias query response indicated it should be stored for 12 hours, the cache should only
live for 12 hours. If the response indicated it should be stored for 5 minutes, it should be stored
for 5 minutes, not 12 hours.

Step 3 specifically qualifies that servers *MAY* return the cached response, because implementations
may prefer to check that the alias is a canonical alias of a room it is a resident of. Servers may
choose not to return aliases which they cannot find in canonical alias events,
however this is up to the receiving server's discretion.

Servers MUST NOT cache responses from servers other than the room alias' origin. This prevents an
effect where a stale response may be incorrectly "freshened" by a second-degree server, and then
passed on to a third-degree server, so on. Or visually, in a chain of
`ORIGIN <- A <- B <- C`, `A` can cache the response from `ORIGIN`, and `A` can return that cached
response to `B` (see step 3), but `B` *MUST NOT* cache that response. If `C` attempts to query `B`,
`B` will perform the same steps `A` did, meaning it will always return a fresh response, or a
not-found error.

Furthermore, servers MUST NOT serve cached responses that lack a signature from the origin. Such
responses cannot be verified as authentic by any server other than the one that made the query to
the origin. This also means that servers who do not wish to allow their aliases to be proxied may
simply avoid signing the response in the first place, even if they support this proposal.

Servers MUST NOT allow clients to define vias. Allowing clients to specify which non-authoritative
servers are queried for a room alias may allow an attacker to inject a malicious response into the
sending server's cache, which has greater implications for multi-user deployments.

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
(who may be malicious).

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

As this change is transparent, no unstable prefix is required. Servers which do not understand this
proposal will not include `signatures`, which disables proxying, and will return an error response
if queried for an alias which does not belong to them.

## Dependencies

None
