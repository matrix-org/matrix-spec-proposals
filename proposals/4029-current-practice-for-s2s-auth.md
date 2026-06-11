# MSC4029: Fixing `X-Matrix` request authentication

The spec inadequately describes how the [`X-Matrix` authentication scheme](https://spec.matrix.org/v1.9/server-server-api/#authentication)
works in the real world. Details like how the query string for a request is handled, encoding
considerations, error/failure conditions, how to handle multiple headers, when to *expect* multiple
headers, etc are all lacking in the specification.

This proposal refers to existing server implementations to introduce standardized behaviour for the
above concerns. Some of these details may be acceptable as regular spec PRs to clarify the spec itself,
though an MSC allows an opportunity to ensure common behaviour should be standard behaviour.

Backwards compatibility with the current common behaviour is a key requirement for this MSC, for areas
it does stray from the common behaviour for.

Issues relating to this problem space are:

* https://github.com/matrix-org/matrix-spec/issues/849
* https://github.com/matrix-org/matrix-spec/issues/561
* https://github.com/matrix-org/matrix-spec/issues/512
* https://github.com/matrix-org/matrix-spec/issues/1570
* https://github.com/matrix-org/matrix-spec/issues/1471
* https://github.com/matrix-org/matrix-spec/issues/479

Related issues, while we're in the area:
* https://github.com/matrix-org/matrix-spec/issues/1569

## Proposal

### Key retrieval

*Issues: [#479](https://github.com/matrix-org/matrix-spec/issues/479)*

The keys a server uses to sign its request are the same it uses to sign events. This also means that
a server *verifying* a signature can use the normal [`GET /_matrix/key/v2/server`](https://spec.matrix.org/v1.9/server-server-api/#get_matrixkeyv2server)
endpoint to fetch that server's keys.

Servers SHOULD NOT [query keys through another server](https://spec.matrix.org/v1.9/server-server-api/#querying-keys-through-another-server)
when validating a request signature. Instead, the server's local cache and direct requests to the
origin server SHOULD be used instead.

Note that it's possible for a remote server to be able to send outbound requests, but not respond to
`GET /_matrix/key/v2/server`. This will result in a signature error if the destination server doesn't
have the key cached already.

**Implementation notes**:

* Synapse already does this.
  * Start of verification: https://github.com/matrix-org/synapse/blame/be65a8ec0195955c15fdb179c9158b187638e39a/synapse/federation/transport/server/_base.py#L125
  * Direct request (post cache): https://github.com/matrix-org/synapse/blame/be65a8ec0195955c15fdb179c9158b187638e39a/synapse/crypto/keyring.py#L280-L296
* Dendrite?
* Conduit?

### Key validity

*Issues: [#479](https://github.com/matrix-org/matrix-spec/issues/479)*

All keys used to sign the request must be valid at the time the receiver processes the request,
otherwise the signature is assumed to be invalid. Specifically, the server's `valid_until_ts` MUST
be in the future relative to "now".

**Implementation notes**:

* Synapse already does this. ***TODO: Evidence.***
* Dendrite?
* Conduit?


### Required keys

*Issues: [#1471](https://github.com/matrix-org/matrix-spec/issues/1471)*

For endpoints which require authentication, a minimum of one key MUST sign the request. Multiple keys
MAY be provided, and MUST individually be valid.

**Implementation notes**:

* Synapse already does this. ***TODO: Evidence.***
* Dendrite?
* Conduit?

### Error codes

When no `Authorization` headers are provided, the server MUST respond with a 401 HTTP status code
and `M_UNAUTHORIZED` Matrix error code. When at least one header is provided, but any of those
headers is invalid, the HTTP status code is 403 instead.

An invalid header is one where the format is not adhered to or the contained signature cannot be
verified. This includes when the sender is not revealing their public keys, per "Key retrieval" above.

***TODO: Signed by random/multiple servers?***

**Implementation notes**:

* Synapse [returns 401 for both cases](https://github.com/matrix-org/synapse/blame/d75d6d65d1681889db05b077e97fc2ddf123b757/synapse/crypto/keyring.py#L340-L350),
  but should be able to support a 403 too.
* Dendrite?
* Conduit?

It is assumed that any server will handle a 401 or 403 equally, likely similar to a 500 as the sending
server should have confidence that its request is properly authenticated (in the general case). Any
error response is therefore likely to be unexpected by the sender.

### Canonicalization

*Issues: [#849](https://github.com/matrix-org/matrix-spec/issues/849),
[#561](https://github.com/matrix-org/matrix-spec/issues/561),
[#512](https://github.com/matrix-org/matrix-spec/issues/512)*

***TODO: This.***

### TODO:

Issues:
* Are path params percent encoded?
* Are query string params percent encoded?
* Can we reliably maintain query string order? (do libraries expose that order?)
  * If we define an order, what happens when multiple query string parameters are specified?
* Can the sending server add random fields to the signed JSON object? (issue #510)
  * ... or can we presume that they're redacted?
* What is the JSON request body for a GET request? (or non-PUT, non-POST request)
* Other edge case questions not yet asked.

## Potential issues

TODO: Write this bit.

## Alternatives

TODO: Write this bit.

## Security considerations

TODO: Write this bit.

## Unstable prefix

TODO: Write this bit.
