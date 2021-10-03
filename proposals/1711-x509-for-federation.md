# MSC1711: X.509 certificate verification for federation connections

TLS connections for server-to-server communication currently rely on an
approach borrowed from the [Perspectives
project](https://web.archive.org/web/20170702024706/https://perspectives-project.org/)
to provide certificate verification, rather than the more normal model using
certificates signed by trusted Certificate Authorities. This document sets out
the reasons that this has not been a success, and suggests that we should
instead revert to the CA model.

## Background: the failure of the Perspectives approach

The Perspectives approach replaces the conventional hierarchy of trust provided
by the Certificate Authority model with a large number of "notary" servers
distributed around the world. The intention is that the notary servers
regularly monitor remote servers and observe the certificates they present;
when making a connection to a new site, a client can correlate the certificate
it presents with that seen by the notary servers. In theory this makes it very
hard to mount a Man-in-the-Middle (MitM) attack, because it would require
intercepting traffic between the target server and a large number of the notary
servers.

It is notable that the Perspectives project itself appears to have largely been
abandoned: its website has largely been repurposed, the [Firefox
extension](https://addons.mozilla.org/en-GB/firefox/addon/perspectives/) does
not work with modern versions of Firefox, the [mailing
list](https://groups.google.com/forum/#!forum/perspectives-dev) is inactive,
and several of the (ten) published notary servers are no longer functional. The
reasons for this are not entirely clear, though clearly it never gained
widespread adoption.

When Matrix was originally designed in 2014, the Perspectives project was
heavily active, and avoiding dependencies on the relatively centralised
Certificate Authorities was attractive, in accordance with Matrix's design as a
decentralised protocol. However, this has not been a success in practice.

Matrix was unable to make use of the existing notary servers (largely because
we wanted to extend the protocol to include signing keys): the intention was
that, as the Matrix ecosystem grew, public Matrix servers would act as notary
servers. However, in practice we have ended up in a situation where almost <sup
id="a1">[1](#f1)</sup> every Matrix homeserver either uses `matrix.org` as the
sole notary, or does no certificate verification at all. Far from avoiding the
centralisation of the Certificate Authorities, the entire protocol is therefore
dependent on a single point of control at `matrix.org` - and because
`matrix.org` only monitors from a single location, the protection against MitM
attacks is weak.

It is also clear that the Perspectives approach is poorly-understood. It is a
common error for homeservers to be deployed behind reverse-proxies which make
the Perspectives-based approach unreliable. The CA model, for all its flaws, is
at least commonly used, which makes it easier for administrators to deploy
(secure) homeservers, and allows server implementations to leverage existing
libraries.

## Proposal

We propose that Matrix homeservers should be required to present valid TLS
certificates, signed by a known Certificate Authority, on their federation
port.

In order to ease transition and give administrators time to switch to a signed
certificate, we will continue to follow the current, perspectives-based
approach for servers whose TLS certificates fail validation.

However, this fallback will be strictly time-limited, and Matrix S2S spec r0
will not accept self-signed certificates, nor will it include the
`tls_fingerprints` property of the
[`/_matrix/key/v2`](https://github.com/matrix-org/matrix-doc/blob/6dab4b28f80f5beeb1d4f475ddc624cf9e7ad085/specification/server_server_api.rst#23retrieving-server-keys)
endpoints. Synapse 1.0 will not accept self-signed certificates by default.

The `matrix.org` team will proactively attempt to reach out to homeserver
administrators who do not update their certificates in the coming weeks.

The process of determining which CAs are trusted to sign certificates would be
implementation-specific, though it should almost certainly make use of existing
operating-system support for maintaining such lists. It might also be useful if
administrators could override this list, for the purpose of setting up a
private federation using their own CA.

It would also be useful for administrators to be able to disable the
certificate checks for a whitelist of domains/netmasks. This would be useful
for testing, or for networks that provide server verification themselves,
such as like `.onion` domains on Tor or `fc00::/8` IPs on cjdns.

### Interaction with SRV records

With the use of `SRV` records, it is possible for the hostname of a homeserver
to be quite different from the matrix domain it is hosting. For example, if
there were an SRV record at `_matrix._tcp.matrix.org` which pointed to
`server.example.com`, then any federation requests for `matrix.org` would be
routed to `server.example.com`. The question arises as to which certificate
`server.example.com` should present.

In short: the server should present a certificate for the matrix domain
(`matrix.org` in the above example). This ensures that traffic cannot be
intercepted by a MitM who can control the DNS response for the `SRV` record
(perhaps via cache-poisoning or falsifying DNS responses).

This will be in line with the current
[requirements](https://github.com/matrix-org/matrix-doc/blob/6dab4b28f80f5beeb1d4f475ddc624cf9e7ad085/specification/server_server_api.rst#21resolving-server-names)
in the Federation API specification for the `Host`, and by implication, the TLS
Server Name Indication <sup id="a2">[2](#f2)</sup>. It is also consistent with
the recommendations of
[RFC6125](https://tools.ietf.org/html/rfc6125#section-6.2.1) and the
conventions established by the XMPP protocol (per [RFC6120](https://tools.ietf.org/html/rfc6120#section-13.7.2.1).

### Extensions

HTTP-Based Public Key Pinning (HPKP) and
[Certificate transparency](https://www.certificate-transparency.org) are
both HTTP extensions which attempt to work around some of the deficiencies in
the CA model, by making it more obvious if a CA has issued a certificate
incorrectly.

HPKP has not been particularly successful, and is
[deprecated](https://developers.google.com/web/updates/2018/04/chrome-67-deps-rems#deprecate_http-based_public_key_pinning)
in Google Chrome as of April 2018. Certificate transparency, however, is seeing
widespread adoption from Certificate Authories and HTTP clients.

This proposal sees both technologies as optional techniques which could be
provided by homeserver implementations. We encourage but do not mandate the use
of Certificate Transparency.

### Related work

The Perspectives approach is also currently used for exchanging the keys that
are used by homeservers to sign Matrix events and federation requests (the
"signing keys"). Problems similar to those covered here also apply to that
mechanism. This is discussed at [#1685](thttps://github.com/matrix-org/matrix-doc/issues/1685).

## Alternatives

There are well-known problems with the CA model, including a number of
widely-published incidents in which CAs have issued certificates
incorrectly. It is therefore important to consider alternatives to the CA
model.

### Improving support for the Perspectives model

In principle, we could double-down on the Perspectives approach, and make an effort
to get servers other than `matrix.org` used as notary servers. However, there
remain significant problems with such an approach:

* Perspectives remain complex to configure correctly. Ideally, administrators
  need to make conscious choices about which notaries to trust, which is hard
  to do, especially for newcomers to the ecosystem. (In practice, people use
  the out-of-the-box configuration, which is why everyone just uses
  `matrix.org` today).

* A *correct* implementation of Perspectives really needs to take into account
  more than the latest state seen by the notary servers: some level of history
  should be taken into account too.

Essentially, whilst we still believe the Perspectives approach has some merit,
we believe it needs further research before it can be relied upon. We believe
that the resources of the Matrix ecosystem are better spent elsewhere.

### DANE

DNS-Based Authentication of Named Entities (DANE) can be used as an alternative
to the CA model. (It is arguably more appropriately used *together* with the CA
model.)

It is not obvious to the author of this proposal that DANE provides any
material advantages over the CA model. In particular it replaces the
centralised trust of the CAs with the centralised trust of the DNS registries.

## Potential issues

Beyond the problems already discussed with the CA model, requiring signed
certificates comes with a number of downsides.

### More difficult setup

Configuring a working, federating homeserver is a process fraught with
pitfalls. This proposal adds the requirement to obtain a signed certificate to
that process. Even with modern intiatives such as Let's Encrypt, this is
another procedure requiring manual intervention across several moving parts.

On the other hand: obtaining an SSL certificate should be a familiar process to
anybody capable of hosting a production homeserver (indeed, they should
probably already have one for the client port). This change also opens the
possibility of putting the federation port behind a reverse-proxy without the
need for additional configuration. Hopefully making the certificate usage more
conventional will offset the overhead of setting up a certificate.

Furthermore, homeserver implementations could provide an implementation of the
ACME protocol and integration with Let's Encrypt, to make it easier for
administrators to get started. (This would of course be
implementation-specific, and administrators who wanted to keep control of the
certificate creation process would be free to do so).

### Inferior support for IP literals

Whilst it is possible to obtain an SSL cert which is valid for a literal IP
address, this typically requires purchase of a premium certificate; in
particular, Let's Encrypt will not issue certificates for IP literals. This may
make it impractical to run a homeserver which uses an IP literal, rather than a
DNS name, as its `server_name`.

It has long been the view of the `matrix.org` administrators that IP literals
are only really suitable for internal testing. Those who wish to use them for
that purpose could either disable certificate checks inside their network, or
use their own CA to issue certificates.

### Inferior support for hidden services (`.onion` addresses)

It is currently possible to correctly route traffic to a homeserver on a
`.onion` domain, provided any remote servers which may need to reach that
server are configured to route to such addresses via the Tor network. However,
it can be difficult to get a certificate for a `.onion` domain (again, Let's
Encrypt do not support them).

The reasons for requiring a signed certificate (or indeed, for using TLS at
all) are weakened when traffic is routed via the Tor network. Administrators
using the Tor network could disable certificate checks for `.onion` addresses.

## Conclusion

We believe that requiring homeservers to present an X.509 certificate signed by
a recognised Certificate Authority will improve security, reduce
centralisation, and eliminate some common deployment pitfalls.

<a id="f1"/>[1] It's *possible* to set up homeservers to use servers other than
`matrix.org` as notaries, but only a minority are actually set up this
way. [↩](#a1)

<a id="f2"/>[2] I've not been able to find an authoritative source on this, but
most reverse-proxies will reject requests where the SNI and Host headers do not
match. [↩](#a2)
