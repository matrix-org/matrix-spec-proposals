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

We insert the following between Steps 3 and 4.

If the SRV record does not exist, the requesting server should make a `GET`
request to `https://<server_name>/.well-known/matrix/server`, with normal X.509
certificate validation, and following 30x redirects (being careful to avoid
redirect loops). If the request does not return a 200, continue to step 4,
otherwise:

The response must be valid JSON which follows the structure documented
below. Otherwise, continue to the next step in the discovery process. It is
NOT necessary for the response to have a `Content-Type` of `application/json`.

If the response is valid, the `m.server` property is parsed as
`<delegated_server_name>[:<delegated_port>]`, and processed as follows:

* If `<delegated_server_name>` is an IP literal, then that IP address should be
  used, together with `<delegated_port>`, or 8448 if no port is given. The
  server should present a valid TLS certificate for `<delegated_server_name>`.

* If `<delegated_server_name>` is not an IP literal, and `<delegated_port>` is
  present, then an IP address is discovered by looking up an AAAA or A record
  for `<delegated_server_name>`, and the specified port is used. The server
  should present a valid TLS certificate for `<delegated_server_name>`.

  (In other words, the federation connection is made to
  `https://<delegated_server_name>:<delegated_port>`).

* If the hostname is not an IP literal and no port is given, a second SRV
  record is looked up; this time for `_matrix._tcp.<delegated_server_name>`,
  which may give yet another hostname (to be looked up using A/AAAA queries)
  and port. The server must present a TLS cert for the
  `<delegated_server_name>` from the .well-known.

* If no SRV record is found, the server is discovered by looking up an AAAA
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

If the response cannot be parsed as JSON, or lacks a valid `m.server` property,
the request is considered to have failed, and no fallback to port 8448 takes
place.

The formal grammar for the `m.server` property is the same as that of a [server
name](https://matrix.org/docs/spec/appendices.html#server-name): it is a
hostname or IP address, followed by an optional port.

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

## Dismissed alternatives

For future reference, here are the alternative solutions which have been
considered and dismissed.

### Look up the `.well-known` file before the SRV record

We could make the request for `.well-known` before looking up the `SRV`
record. On the one hand this is maybe marginally simpler (and avoids the
overhead of having to make *two* `SRV` lookups in the case that a `.well-known`
is found. It might also open a future path for using `.well-known` for
information other than delegation.

Ultimately we decided to include the initial `SRV` lookup so that deployments
have a mechanism to avoid the `.well-known` overhead in the common case that it
is not required.

### Subdomain hack

As well as accepting TLS certs for `example.com`, we could also accept them for
`delegated--matrix.example.com`. This would allow `example.com` to delegate its
matrix hosting by (a) setting up the SRV record at `_matrix._tcp.example.com`
and (b) setting up a CNAME at `delegated--matrix.example.com`. The latter would
enable the delegatee to obtain an acceptable TLS certificate.

This was certainly an interesting idea, but we dismissed it for the following
reasons:

* There's a security trap for anybody who lets people sign up for subdomains
  (which is certainly not an uncommon business model): if you can register for
  delegated--matrix.example.com, you get to intercept all the matrix traffic
  for example.com.

* Generally it feels quite unintuitive and violates the principle of least
  surprise.

* The fact that we can't find any prior art for this sets off alarm bells too.

### Rely on DNS/DNSSEC

If we could trust SRV records, we would be able to accept TLS certs for the
*target* of the SRV record, which avoids this whole problem.

Such trust could come from assuming that plain DNS is "good enough". However,
DNS cache poisoning attacks are a real thing, and the fact that the designers
of TLS chose to implement a server-name check specifically to deal with this
case suggests we would be foolish to make this assumption.

The alternative is to rely on DNSSEC to provide security for SRV records. The
problem here is simply that DNSSEC is not that widely deployed currently. A
number of large organisations are actively avoiding enabling it on their
domains, so requiring DNSSEC would be a direct impediment to the uptake of
Matrix. Furthermore, if we required DNSSEC-authenticated SRV records for
domains doing delegation, we would end up with a significant number of
homeservers unable to talk to such domains, because their local DNS
infrastructure may not implement DNSSEC.

Finally, if we're expecting servers to present the cert for the *target* of the
SRV record, then we'll have to change the Host and SNI fields, and that will
break backwards compat everywhere (and it's hard to see how to mitigate that).

### Stick with perspectives

The final option is to double-down on the Perspectives approach, ie to skip
[MSC1711](https://github.com/matrix-org/matrix-doc/pull/1711). MSC1711
discusses the reasons we do not believe this to be a viable option.

## Conclusion

This proposal adds a new mechanism, alongside the existing `SRV` record lookup
for finding the server responsible for a particular matrix server_name, which
will allow greater flexibility in deploying homeservers.
