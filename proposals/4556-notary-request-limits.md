# MSC4556: Notary request limits

Currently, the server-to-server spec for "Querying keys through another server" defines two
endpoints: [`POST /_matrix/key/v2/query`][spec-qry] and
[`GET /_matrix/key/v2/query/{serverName}`][spec-qry1]. These two endpoints both serve the same
purpose (fetching signing keys for a remote server *through* another server), however the former
allows for a bulk fetch via query criteria. This is mainly useful for fetching signing keys required
to verify events upon joining a room, as fetching each key from the origin individually is slow and
fallible, and using the second listed endpoint to fetch keys may require thousands of requests.

[spec-qry]: https://spec.matrix.org/v1.19/server-server-api/#post_matrixkeyv2query
[spec-qry1]: https://spec.matrix.org/v1.19/server-server-api/#get_matrixkeyv2queryservername

Unfortunately, this places the notary server of choice in a predicament: it is illegal to completely
refuse a large query, which means a notary server *has* to fetch all of the keys it can. This also
makes notary servers an amplification attack vector, as they are required to contact origins to
fetch their latest signing keys before the notary is allowed to pull from its local cache. Notary
servers also have no way to signal to requesters that their request may be too large, or that
they're querying too frequently, which means it can be very easy to overload weaker notary servers.

This proposal introduces new standard limits to the bulk lookup endpoint specifically, as well as
defining behaviour for errors and rate-limits.

## Proposal

For [`POST /_matrix/key/v2/query`][spec-qry] specifically, the endpoint becomes rate-limited, and
to accompany this, optionally authenticated. Servers querying the endpoint SHOULD
[authenticate the request][s2s-auth], so that notaries can rate-limit based on the server name,
instead of source IP address.

[s2s-auth]: https://spec.matrix.org/v1.19/server-server-api/#request-authentication

Servers MAY wish to rate-limit based on the complexity of received requests, potentially taking into
account how many requests required contacting origin servers - rather than the rate of requests - as
smaller requests may have a 100% cache hit rate, and consequently are cheap to serve.

And to set baseline expectations for what a notary server can receive, the following limitations
are defined on the request:

* Servers MUST NOT ask for more than 4096 unique server names (object keys of `server_keys`).
* Servers SHOULD NOT ask for more than 4 key IDs per server name.
* Servers MUST NOT ask for more than 16384 total key IDs per request.

Notary servers MAY reject requests with `413 / M_TOO_LARGE` if they exceed these limits.
When receiving this error from a notary server, servers MUST NOT retry the request unmodified.
They MAY try another request with a smaller payload size (e.g. asking for half as many keys,
splitting into two chunks).

## Potential issues

Servers that contact notary servers may not be aware of these limitations if they are outdated, and
consequently will not have appropriate handling for the error response, or the rate-limit.
This is acceptable, as existing implementations simply degrade by backing off from the notary, which
ultimately achieves the end goal anyway.

## Alternatives

Transparent rate-limiting approaches do exist, such as locally throttling how many iterations the
notary server is willing to do over a period of time. Another approach is to simply only perform the
first N lookups.

Both of these have issues: the first introduces artificial latency that scales with the size of the
request, which makes slow operations like joining rooms even slower. The latter may cause
functional problems as requesting servers may not understand that the query was truncated, and
consequently may assume they just can't verify signatures they need (this is particularly
problematic for servers that use a "fastest response" approach and discard other notary responses
that may return the keys they want).

## Security considerations

This pull request does not introduce any new security considerations, however it aims to resolve
some potential problems with the existing system, as outlined in the opening paragraphs.

## Unstable prefix

This MSC does not necessitate an unstable prefix, however notary server implementations should
consider the adoption rate of this proposal before rejecting requests per the limits defined,
opting to use one of the [alternative approaches](#alternatives) instead when a request exceeds the
limits.

## Dependencies

This proposal has no dependencies.
