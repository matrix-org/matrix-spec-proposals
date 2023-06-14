# MSC4029: Fixing `X-Matrix` request authentication

The spec inadequately describes how the [`X-Matrix` authentication scheme](https://spec.matrix.org/v1.7/server-server-api/#authentication)
works in the real world. Details like how the query string for a request is handled, encoding
considerations, error/failure conditions, how to handle multiple headers, when to *expect* multiple
headers, etc are all lacking in the specification.

This proposal covers those details, using what is currently implemented in servers as a starting
principle. Normally, these sorts of changes would be considered bug fixes against the spec itself,
however with an MSC it allows an opportunity to question the motivation for doing something. If
this MSC ultimately diverges from what is done in practice, backwards compatibility becomes a major
requirement.

Issues relating to this problem space are:

* https://github.com/matrix-org/matrix-spec/issues/849
* https://github.com/matrix-org/matrix-spec/issues/561
* https://github.com/matrix-org/matrix-spec/issues/512
* https://github.com/matrix-org/matrix-spec/issues/1570
* https://github.com/matrix-org/matrix-spec/issues/1471
* https://github.com/matrix-org/matrix-spec/issues/510 (kinda)
* https://github.com/matrix-org/matrix-spec/issues/479

Related issues, while we're in the area:
* https://github.com/matrix-org/matrix-spec/issues/1569

## Proposal

TODO: Write this bit.

Issues:
* Are path params percent encoded?
* Are query string params percent encoded?
* Can we reliably maintain query string order? (do libraries expose that order?)
  * If we define an order, what happens when multiple query string parameters are specified?
* How many of a server's signing keys need to sign the request?
  * Of those keys, what is their minimum lifetime/expiration?
* What's the error and status code when auth fails?
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
