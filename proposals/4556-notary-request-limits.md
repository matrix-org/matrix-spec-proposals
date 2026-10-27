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

A new endpoint is introduced: `POST /_matrix/key/v3/query`. Unlike its predecessor, it is
rate-limited AND authenticated.

Servers MAY wish to rate-limit based on the complexity of received requests, potentially taking into
account how many requests required contacting origin servers - rather than the rate of requests - as
smaller requests may have a 100% cache hit rate, and consequently are cheap to serve.

And to set baseline expectations for what a notary server can receive, the following limitations
are defined on the request:

* Servers MUST NOT ask for more than 4096 unique server names (object keys of `server_keys`).
* Servers MUST NOT ask for more than 16384 total key IDs per request.

Notary servers MAY reject requests with `413 / M_TOO_LARGE` if they exceed these limits.
When receiving this error from a notary server, servers MUST NOT retry the request unmodified.
They MAY try another request with a smaller payload size (e.g. asking for half as many keys,
splitting into two chunks).

Upon receiving a `404 M_UNRECOGNIZED` response from a notary server, a homeserver SHOULD retry the
same request to the previous version of this endpoint, [`POST /_matrix/key/v2/query`][spec-qry].

Should this proposal be merged, the previous version of this endpoint becomes deprecated. Notary
servers SHOULD continue to support it as long as it is in the specification, however MAY apply
mitigation techniques on it to prevent service overload. Some approaches are listed in the
alternatives section.

## Potential issues

Notary servers are required to continue supporting the v2 query endpoint, which is not allowed to
refuse large queries, which may impact service availability if appropriate mitigation technologies
are not implemented.

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

Refer to the issue outlined in potential issues - inappropriate rate-limits may cause
disproportionate strain on the notary server.

## Unstable prefix

| Stable                  | Unstable                                               |
| ----------------------- | ------------------------------------------------------ |
| `/_matrix/key/v3/query` | `/_matrix/key/unstable/org.continuwuity.msc4556/query` |

## Dependencies

This proposal has no dependencies.
