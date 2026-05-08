# MSC4464: Verifiable Links in Profile

A lot of other chat platforms (like Discord) and social media platforms (like
Mastodon, Sharkey, ...) allow you to put a list of links in your profile which
then get verified.

In the fediverse (e.g. Mastodon) it is simply done by crawling the linked site
and searching for links with the `rel="me"` attribute.

This proposal introduces a way for Matrix homeservers to do a relationship based
(`rel="me"`), as known from the fediverse, but beyond that also a dns and matrix
backlink (useful for example for alt accounts) verification. This would go a
long way in establishing more feature parity to other popular platforms.

It would also go a long way in reducing the risk of impersonation and phishing
for a set of MSC4462 connections in profile.

## Proposal

### The role of the homeserver

A homeserver SHOULD provide a client-server API endpoint to verify link
relationship against under `/_matrix/client/v1/verify_profile_connection`. The
result of the link verification SHOULD be cached for some amount of time
(*implementation detail*). The homeserver SHOULD add a `expires` field to the
response, to indicate after what point in time a verification should be
considered outdated, after that time a client SHOULD reverify.

A homeserver MAY choose to disable the
`/_matrix/client/v1/verify_profile_connection` endpoint by its respective
configuration. Since there can be a lot of verification requests on a big
homeserver, a ratelimit may be applied (in which case a HTTP 429 should be
returned).

To prevent potentially infinite redirect loops, a restriction on the amount of
redirects SHOULD be applied. A homeserver MAY use a blocklist/allowlist if it
wants to filter what links they try to verify. However a homeserver MUST prevent
verification requests pointing to restricted addresses
([RFC1918](https://www.rfc-editor.org/info/rfc1918), localhost, ...).

To verify a relationship it MUST match the full MXID (after normalization).

As a client may wish to display additional information regarding a link
(especially if the link is a web address) a homeserver MAY include url preview
information with the response.

A homeserver SHOULD allow verification request towards subpages (e.g.
`https://example.org/about`), but MUST NOT mark the whole domain as verified for
the mxid, it SHOULD as well allow multiple matrix-account-links per page.

#### Verification Methods

##### Relationship

A homeserver

- MAY derive the cache time from the `cache-control` http response header.
- SHOULD upon request, with a payload defined below, fetch that link, parse, and
  check if the relationship is given
- MAY restrict from which hosts websites can be fetched from for verification,
  similar to link previews
- SHOULD enforce content-type (e.g. HTML only)
- MUST parse static HTML (no JS execution)
- MAY discard the verification and mark it as failed if the http response
  exceeds 1MB in size
- SHOULD NOT regard links in `<iframe>`, even if they would pass the
  verification
- MUST treat `rel` as ASCII case-insensitive

A homeserver checks the verification by checking for elements of type `a` or
`link` with the relationship me
([`rel="ME"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/rel/me)).
A simple link (without the relationship) MUST NOT result in verifying a link
relationship. As a reference developers could see Mastodon's approach (see
[mastodon docs](https://docs.joinmastodon.org/user/profile/#verification)).

The homeserver SHOULD consider both the
[`matrix.to` address](https://spec.matrix.org/v1.18/appendices/#matrixto-navigation)
(e.g. `https://matrix.to/#/@alice:example.org`) and the
[`matrix` URI](https://spec.matrix.org/v1.18/appendices/#matrix-uri-scheme)
(e.g. `matrix:u/alice:example.org`) scheme for the backlink.

A homeserver SHOULD consider when evaluating a `matrix.to` address, that it
could also be encoded (e.g. `https://matrix.to/#/%40example%3Aexample.org`).

##### DNS

A homeserver SHOULD also offer DNS based link verification, by checking the
domain for a `_matrix-verification.DOMAIN` txt record containing a comma
separated list of mxids. If a domain has been verified by DNS record all
subpages of the domain MUST also be marked as verified. However, if a subdomain
has been DNS verified, the root domain MUST NOT be marked as verified. A
homeserver SHOULD respect the DNS records TTL for it's caching.

Example txt record for `_matrix-verification.example.org`:

```
"@alice:example.org,@bob:example.org"
```

This example should result in the homeserver verifying the whole domain for both
`@alice:example.org` and `@bob:example.org`.

For the format of a MXID, the
[grammar of a user identifier in the spec](https://spec.matrix.org/v1.18/appendices/#user-identifiers)
finds application.

##### Matrix

A relationship between matrix users SHOULD be marked as verified if they have a
bidirectional link towards each other. In other words if `@alice:example.org`
links to `@alice:example.com` the link MUST only be verified if
`@alice:example.com` also links back to `@alice:example.org`.

A homeserver would check this by requesting the profiles of both
`@alice:example.org` and `@alice:example.com`, and checks if they link to each
other. If they don't link to each other it SHOULD be treated as a failed
verification. If an error during lookup occurs it SHOULD be treated as an
erroring verification (see verification with `error` as result below).

#### Request to the endpoint

A client SHOULD, when wanting to check a link-user-relationship, send a `GET`
Request to the `/_matrix/client/v1/verify_profile_connection` endpoint.

The request should set the following query parameters:

- `uri` the uri a client wants to verify (example: `https://example.org`)
- `mxid` the mxid to check against, not the mxid of the user initiating the
  request (example: `@alice:example.org`)
- `method` the verification method to use (accepted values: `m.method.dns`,
  `m.method.relation`, or `m.method.matrix`)

#### Response format

For **successful verifications**, homeservers SHOULD respond to the client with
the following:

```json
{
    "verification": {
        "result": "success",
        "method": "m.method.dns" | "m.method.relation" | "m.method.matrix",
        // expiry should be defined as the unix epoch after which to try again
        "expires": "1778107123",
        "scope": "m.scope.site" | "m.scope.domain" | "m.scope.account"
    },
    // optional additional url preview stuff
    "preview_url": {
        // same format as defined for url preview responses
        // see https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv1mediapreview_url
    }
}
```

The scope field describes the extent of the verified relationship:

- `m.scope.site` indicates verification of a specific URL (related to
  `m.method.relation`)
- `m.scope.domain` indicates verification of an entire domain and its subpages
  (related to `m.method.dns`)
- `m.scope.account` indicates verification of an account-level identifier (e.g.
  a Matrix user ID, related to `m.method.matrix`)

While the `scope` and `method` fields may appear redundant, the `scope` field
makes the extent, not the strength, of a verification result explicit. This
allows clients to interpret verification results without relying on
method-specific behavior (e.g. determining whether a verification applies to a
single URL or an entire domain).

Additionally, including `scope` allows for future extensibility, where new
verification methods may be introduced without requiring clients to infer the
scope from the method.

For **failed/erroring verifications**, homeservers SHOULD respond to the client
with the following:

```json
{
    "verification": {
        "result": "not_found" | "error" | "verification_failed",
        "method": "m.method.dns" | "m.method.relation" | "m.method.matrix",
        "expires": "1778107123"
    }
}
```

The `result` should use the following logic:

- `not_found` if a http request returns `404`, or a DNS lookup returns
  `NXDOMAIN`
- `error` for other errors
- `verification_failed` if the request was successful the verification however
  wasn't (i.e. the website loaded as expected but no matching `rel="me"` found)

For **rate-limited** request, homeservers SHOULD respond with a 429 response
like the following

```json
{
  "errcode": "M_LIMIT_EXCEEDED",
  "error": "Too many requests",
  "retry_after_ms": 2000
}
```

Note that this is the same response a client would get for a rate-limited url
preview request.

### The role of the client

#### Storage in the user profile

This proposal builds on
[MSC4462: Links in Profile](https://github.com/matrix-org/matrix-spec-proposals/pull/4462)
and extends its `m.connections` field in the user profile, with
`verification_method` as an attribute describing how the link can be verified.

Example of the extended `m.connections` field:

```json
{
   "m.connections": [
     {
        "description": "homepage",
        "uri": "https://example.org",
        "verification_method": "m.method.dns"
     },
     {
        "description": "mastodon",
        "uri": "https://mastodon.social/@example",
        "verification_method": "m.method.relation"
     },
     {
        "description": "alt-account",
        "uri": "matrix:u/alice:example.org",
        "verification_method": "m.method.matrix"
     }
   ]
}
```

The value of `verification_method` may either be `m.method.dns`,
`m.method.relation`, or `m.method.matrix`. If it is unset clients MAY use the
same behaviour as for `m.method.relation` or mark the link as unverified.

#### Verifying a link

Clients

- MUST NOT mark a link as verified unless the homeserver marks the link as
  verified
- SHOULD use the format specified in "Payload for the endpoint" to request
  verification from homeserver
- MAY cache the result until the `expires` date if the verification has been
  successful
- SHOULD consider the verification as outdated after `expires` has passed and
  reverify
- SHOULD treat outdated verification as a link being unverified
- MAY cache failures to not overwhelm the homeserver with requests
- MAY hide unverified links from the user

### Summary

A link MUST only be marked as verified if a verifiable relationship exists
between the MXID and the `uri`, established via one of the supported methods.

Depending on the method:

- Relationship- and Matrix-based verification REQUIRE bidirectional linking
- DNS-based verification establishes domain-level authority and does not require
  a backlink from the target resource

Small but notable difference between the verification methods: DNS-based
verification verifies domain-level authority, whereas matrix- and relationship
based verification verify link-level reciprocity.

## Potential issues

### Single Page Sites using JavaScript

Nowadays a lot of sites are heavily reliant on the execution of JavaScript for
their content. There is a case in allowing parsing after JavaScript execution to
allow more sites.

However, that would open an attack vector and require a JavaScript runtime on
the homeserver, therefore the link must be present in static HTML, or using the
DNS method.

## Alternatives

### Verifying a link client side

A verification of links in the way this proposal proposes it for homeservers to
act, could also be done by clients.

However, this would have considerable security implications:

- fetching a arbitrary website (in that exposing the client ip to potentially
  malicious actors)
- rendering a arbitrary website (could end up as an attack vector for cross side
  scripting)
- a lot of requests to a website, if a lot of users look at one's profile (a
  homeserver could cache the verification result)

### Third Party Verification

Another possible alternative would be to rely on a set of supported third-party
verification services. However, this would require a shared trust model and
service discovery mechanism across the federation, which would complicate
deployment and interoperability.

If a clear use case emerges, this could be added later through a new
`verification_method` value. For example, a Discord integration could use
`"verification_method": "m.method.discord"`. This proposal therefore leaves
`verification_method` open for future methods. However this proposal doesn't in
itself propose third party verification methods.

### Cryptographic Proofs

This is a plausible alternative. However, it would introduce additional protocol
complexity and key-management requirements, while providing little benefit over
the existing relationship-based approach already used by established platforms
such as Mastodon.

## Security considerations

- A website could trigger cyclic redirects, therefore a server MUST enforce a
  limit on redirects, see above
- DNS-based verification proves that the operator of a domain asserts an
  association with a given MXID. It does not prove that the MXID owner controls
  the domain.
- When a homeserver performs a verification (especially for relationship based
  verification) it initiates a connection to an arbitrary website, which could
  lead to leak some meta data to the website operator (similar to homeserver
  based url previews)

## Unstable prefix

implementations should use

- `fyi.cisnt.connections` instead of `m.connections`
- `fyi.cisnt.method.*` instead of `m.method.*`
- `fyi.cisnt.scope.*` instead of `m.scope.*`
- `_msc4464-verification` instead of `_matrix-verification` for the DNS TXT
  record
- `/_matrix/client/unstable/fyi.cisnt.connections/verify_profile_connection`
  instead of `/_matrix/client/v1/verify_profile_connection`

## Dependencies

[MSC4462 (Links in Profile)](https://github.com/matrix-org/matrix-spec-proposals/pull/4462)
