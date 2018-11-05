# MSC1708: .well-known support for server name resolution

Currently, mapping from a server name to a hostname for federation is done via
`SRV` records. This presents two principal difficulties:

 * SRV records are not widely used, and administrators may be unfamiliar with
   them, and there may be other practical difficulties in their deployment such
   as poor support from hosting providers. [^1]

 * It is likely that we will soon require valid X.509 certificates on the
   federation endpoint. It will then be necessary for the homeserver to present
   a certificate which is valid for the server name. This presents difficulties
   for hosted server offerings: BigCorp may be reluctant to hand over the
   keys for `bigcorp.com` to the administrators of the `bigcorp.com` matrix
   homeserver.

Here we propose to solve these problems by augmenting the current `SRV` record
with a `.well-known` lookup.

## Proposal

For reference, the current [specification for resolving server
names](https://matrix.org/docs/spec/server_server/unstable.html#resolving-server-names)
is as follows:

* If the hostname is an IP literal, then that IP address should be used,
  together with the given port number, or 8448 if no port is given.

* Otherwise, if the port is present, then an IP address is discovered by
  looking up an AAAA or A record for the hostname, and the specified port is
  used.

* If the hostname is not an IP literal and no port is given, the server is
  discovered by first looking up a `_matrix._tcp` SRV record for the
  hostname, which may give a hostname (to be looked up using AAAA or A queries)
  and port.  If the SRV record does not exist, then the server is discovered by
  looking up an AAAA or A record on the hostname and taking the default
  fallback port number of 8448.

  Homeservers may use SRV records to load balance requests between multiple TLS
  endpoints or to failover to another endpoint if an endpoint fails.

The first two points remain unchanged: if the server name is an IP literal, or
contains a port, then requests will be made directly as before.

If the hostname is neither an IP literal, nor does it have an explicit port,
then the requesting server should continue to make an SRV lookup as before, and
use the result if one is found.

If *no* result is found, the requesting server should make a `GET` request to
`https://\<server_name>/.well-known/matrix/server`, with normal X.509
certificate validation. If the request fails in any way, then we fall back as
before to using using port 8448 on the hostname.

Rationale: Falling back to port 8448 (rather than aborting the request) is
necessary to maintain compatibility with existing deployments, which may not
present valid certificates on port 443, or may return 4xx or 5xx errors.

If the GET request succeeds, it should result in a JSON response, with contents
structured as shown:

```json
{
   "server": "<server>[:<port>]"
}
```

The `server` property has the same format as a [server
name](https://matrix.org/docs/spec/appendices.html#server-name): a hostname
followed by an optional port.

If the response cannot be parsed as JSON, or lacks a valid `server` property,
the request is considered to have failed, and no fallback to port 8448 takes
place.

Otherwise, the requesting server performs an `AAAA/A` lookup on the hostname,
and connects to the resultant address and the specifed port. The port defaults
to 8448, if unspecified.

### Caching

Servers should not look up the `.well-known` file for every request, as this
would impose an unacceptable overhead on both sides. Instead, the results of
the `.well-known` request should be cached according to the HTTP response
headers, as per [RFC7234](https://tools.ietf.org/html/rfc7234). If the response
does not include an explicit expiry time, the requesting server should use a
sensible default: 24 hours is suggested.

Because there is no way to request a revalidation, it is also recommended that
requesting servers cap the expiry time. 48 hours is suggested.

Similarly, a failure to retrieve the `.well-known` file should be cached for
a reasonable period. 24 hours is suggested again.

### The future of SRV records

It's worth noting that this proposal is very clear in that we will maintain
support for SRV records for the immediate future; there are no current plans to
deprecate them.

However, clearly a `.well-known` file can provide much of the functionality of
an SRV record, and having to support both may be undesirable. Accordingly, we
may consider sunsetting SRV record support at some point in the future.

### Outstanding questions

Should we follow 30x redirects for the .well-known file? On the one hand, there
is no obvious usecase and they add complexity (for example: how do they
interact with caches?). On the other hand, we'll presumably be using an HTTP
client library to handle some of the caching stuff, and they might be useful
for something?

## Security considerations

The `.well-known` file potentially broadens the attack surface for an attacker
wishing to intercept federation traffic to a particular server.

## Conclusion

This proposal adds a new mechanism, alongside the existing `SRV` record lookup
for finding the server responsible for a particular matrix server_name, which
will allow greater flexibility in deploying homeservers.


[^1] For example, Cloudflare automatically "flattens" SRV record responses.

