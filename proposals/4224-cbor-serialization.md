# MSC4224: Initial support for CBOR serialization

This proposal introduces support for CBOR (Concise Binary Object Representation)
as an optional serialization format for the Client-Server API. CBOR, a binary
format standardized by [RFC
8949](https://datatracker.ietf.org/doc/html/rfc8949), is designed for efficient
data encoding and processing, offering a more compact alternative to JSON. By
providing optional CBOR support, this proposal aims to improve the performance
for devices with constrained resources and enhance overall efficiency.

This proposal is inspired by
[MSC3079](https://github.com/matrix-org/matrix-spec-proposals/pull/3079), which
at the time of writing is too complex to implement and have not yet been
accepted into the spec, this proposal focuses on CBOR serialization part of it.

## Proposal

This MSC proposes supporting CBOR encoding as an optional format for Matrix API
requests and responses. CBOR encoding should be an additional format that
implementations can negotiate to use, with JSON remaining as the default. To
ensure backward compatibility, clients and servers must be able to indicate
whether they support CBOR and negotiate which encoding to use.

### Content Negotiation

Clients MUST set the `Content-Type` header to `application/cbor` when sending
CBOR objects. Similarly, servers MUST set the `Content-Type` header to
`application/cbor` when responding with CBOR to requests. Servers MUST NOT
respond to requests with `Content-Type: application/json` with CBOR, unless the
`Accept` header in the client's request includes `application/cbor`.

### Encoding

CBOR objects are encoded and represented identically from JSON, with exception
of binary data, such as public keys or signatures. Given that unlike JSON, CBOR
can safely represent raw binary data, all binary data MUST be encoded and
represented as binary strings with tag 22, as described in RFC 8949 [Section
3.4.5.2](https://www.rfc-editor.org/rfc/rfc8949.html#section-3.4.5.2). Tagging
is required for compatibility with generic CBOR-to-JSON converters.

Example object would be encoded like this:
```
D6                                     # tag(22)
   50                                  # bytes(16)
      03082C12C0053C1EC80BD712ACED1E0A # "AwgsEsAFPB7IC9cSrO0eCg" in base64
```

## Potential issues

At the time of writing, this proposal doesn't provide a integer mapping for
string keys and static string values, which leaves out encoding efficiency.
Identifiers also can be encoded more efficiently by using the assumptions
provided by specification, such as that they utilize way less than 128
characters.

## Alternatives

[MessagePack](https://github.com/msgpack/msgpack/blob/master/spec.md) was
considered first, but in discussion CBOR was favored due to standardised
specification while having on-par performance.

## Security considerations

This proposal does not provide any new endpoints. Security of CBOR, just like
with JSON, depends on implementation.

## Unstable prefix

Clients should check for server support before using the features proposed by
this MSC. Before this MSC gets merged, to detect server support, clients MUST
check for the presence of the `org.matrix.msc4224` flag in `unstable_features`
on `/versions`.
