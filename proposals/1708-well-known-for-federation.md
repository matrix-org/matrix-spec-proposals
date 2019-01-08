# MSC1708: .well-known support for server name resolution

Currently, mapping from a server name to a hostname for federation is done via
`SRV` records. However,
[MSC1711](https://github.com/matrix-org/matrix-doc/pull/1711) proposes
requiring valid X.509 certificates on the federation endpoint. It will then be
necessary for the homeserver to present a certificate which is valid for the
server name. This presents difficulties for hosted server offerings: BigCorp
may want to delegate responsibility for running its Matrix homeserver to an
outside supplier, but it may be difficult for that supplier to obtain a TLS
certificate for `bigcorp.com` (and BigCorp may be reluctant to let them have
one).

This MSC proposes to solve this problem by augmenting the current `SRV` record
with a `.well-known` lookup.

## Proposal

For reference, the current [specification for resolving server
names](https://matrix.org/docs/spec/server_server/unstable.html#resolving-server-names)
is as follows:

1. If the hostname is an IP literal, then that IP address should be used,
   together with the given port number, or 8448 if no port is given.

2. Otherwise, if the port is present, then an IP address is discovered by
   looking up an AAAA or A record for the hostname, and the specified port is
   used.

3. If the hostname is not an IP literal and no port is given, the server is
   discovered by first looking up a `_matrix._tcp` SRV record for the
   hostname, which may give a hostname (to be looked up using AAAA or A queries)
   and port.

4. Finally, the server is discovered by looking up an AAAA or A record on the
   hostname, and taking the default fallback port number of 8448.

We insert the following between Steps 3 and 4:

If the SRV record does not exist, the requesting server should make a `GET`
request to `https://<server_name>/.well-known/matrix/server`, with normal
X.509 certificate validation. If the request does not return a 200, continue
to step 4, otherwise:

XXX: should we follow redirects?

The response must have a `Content-Type` of `application/json`, and must be
valid JSON which follows the structure documented below. Otherwise, the
request is aborted.

If the response is valid, the `m.server` property is parsed as
`<delegated_server_name>[:<delegated_port>]`, and processed as follows:

a. If `<delegated_server_name>` is an IP literal, then that IP address should
   be used, together with `<delegated_port>`, or 8448 if no port is
   given. The server should present a valid TLS certificate for
   `<delegated_server_name>`.

b. Otherwise, if the port is present, then an IP address is discovered by
   looking up an AAAA or A record for `<delegated_server_name>`, and the
   specified port is used. The server should present a valid TLS certificate
   for `<delegated_server_name>`.

   (In other words, the federation connection is made to
   `https://<delegated_server_name>:<delegated_port>`).

c. If the hostname is not an IP literal and no port is given, a second SRV
   record is looked up; this time for `_matrix._tcp.<delegated_server_name>`,
   which may give yet another hostname (to be looked up using A/AAAA queries)
   and port. The server must present a TLS cert for the
   `<delegated_server_name>` from the .well-known.

d. If no SRV record is found, the server is discovered by looking up an AAAA
   or A record on `<delegated_server_name>`, and taking the default fallback
   port number of 8448.

   (In other words, the federation connection is made to
   `https://<delegated_server_name>:8448`).

### Structure of the `.well-known` response

The contents of the `.well-known` response should be structured as shown:

```json
{
   "m.server": "<server>[:<port>]"
}
```

The `m.server` property should be a hostname or IP address, followed by an
optional port.

If the response cannot be parsed as JSON, or lacks a valid `server` property,
the request is considered to have failed, and no fallback to port 8448 takes
place.

(The formal grammar for the `server` property is identical to that of a [server
name](https://matrix.org/docs/spec/appendices.html#server-name).)

### Caching

Servers should not look up the `.well-known` file for every request, as this
would impose an unacceptable overhead on both sides. Instead, the results of
the `.well-known` request should be cached according to the HTTP response
headers, as per [RFC7234](https://tools.ietf.org/html/rfc7234). If the response
does not include an explicit expiry time, the requesting server should use a
sensible default: 24 hours is suggested.

Because there is no way to request a revalidation, it is also recommended that
requesting servers cap the expiry time. 48 hours is suggested.

A failure to retrieve the `.well-known` file should also be cached, though care
must be taken that a single 500 error or connection failure should not break
federation for an extended period. A short cache time of about an hour might be
appropriate; alternatively, servers might use an exponential backoff.

### Outstanding questions

Should we follow 30x redirects for the .well-known file? On the one hand, there
is no obvious usecase and they add complexity (for example: how do they
interact with caches?). On the other hand, we'll presumably be using an HTTP
client library to handle some of the caching stuff, and they might be useful
for something?

## Problems

It will take a while for `.well-known` to be supported across the ecosystem;
until it is, it will be difficult to deploy homeservers which rely on it for
their routing: if Alice is using a current homeserver implementation, and Bob
deploys a new implementation which relies on `.well-known` for routing, then
Alice will be unable to send messages to Bob. (This is the same problem we have with
[SNI](https://github.com/matrix-org/synapse/issues/1491#issuecomment-415153428).)

The main defence against this seems to be to release support for `.well-known`
as soon as possible, to maximise uptake in the ecosystem. It is likely that, as
we approach Matrix 1.0, there will be sufficient other new features (such as
new Room versions) that upgrading will be necessary anyway.

## Security considerations

The `.well-known` file potentially broadens the attack surface for an attacker
wishing to intercept federation traffic to a particular server.

## Conclusion

This proposal adds a new mechanism, alongside the existing `SRV` record lookup
for finding the server responsible for a particular matrix server_name, which
will allow greater flexibility in deploying homeservers.
