# MSC4330: Specify HTTP and TLS version used for Matrix

Currently there are no HTTP and TLS version mandated by the Matrix spec to be used with the HTTP transport. This
ambiguity is not good for a standard which should be interoperable with different implementations.

## Proposal

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in RFC 2119.

All implementations of the Matrix protocol MUST support HTTP/2 and MAY additionally support HTTP/3 for any HTTP based
transport. Furthermore, all implementations using a transport secured by TLS MUST support TLSv1.2 and SHOULD support any
newer TLS versions.

## Potential issues

\-

## Alternatives

The mininmum HTTP version could be set to HTTP/1.1 instead.

## Security considerations

See RFC9113 (HTTP/2) section 10 and RFC9114 (HTTP/3) section 10. Additionally, future TLS versions may contain security
issues which must be addressed.

