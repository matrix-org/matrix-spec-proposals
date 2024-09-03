# MSC3783: Fixed base64 for SAS verification

libolm's original implementation for calculating the
[MAC](https://spec.matrix.org/v1.5/client-server-api/#mkeyverificationmac) for
SAS-based device verification [encoded the base64 output
incorrectly](https://gitlab.matrix.org/matrix-org/olm/-/merge_requests/16).
Thus other implementations that use a correct base64 encoding are not
compatible, and must instead [re-implement libolm's incorrect
encoding](https://matrix-org.github.io/vodozemac/vodozemac/sas/struct.EstablishedSas.html#method.calculate_mac_invalid_base64).
libolm now has a function that returns the correct base64 encoding, but it is
currently not used to ensure compatibility with older clients.

This proposal introduces a new message authentication code identifier for use
with SAS verification that uses the correct base64 encoding.  The current
method will be deprecated.

## Proposal

A new message authentication code identifier `hkdf-hmac-sha256.v2` is
introduced.  This identifier is used in the `message_authentication_codes`
property of the
[`m.key.verification.start`](https://spec.matrix.org/v1.5/client-server-api/#mkeyverificationstartmsasv1)
event, and the `message_authentication_code` property of the
[`m.key.verification.accept`](https://spec.matrix.org/v1.5/client-server-api/#mkeyverificationaccept)
event.  Clients that implement SAS verification are required to implement this
method.  The `message_authentication_codes` parameter for the
[`m.key.verification.start`](https://spec.matrix.org/v1.5/client-server-api/#mkeyverificationstartmsasv1)
event will require clients to include `hkdf-hmac-sha256.v2`.  Clients are no
longer required to include `hkdf-hmac-sha256`, but should still do so for
compatibility with older clients.

When the two clients that are verifying each other agree to use
this method, the MAC is calculated in the same way as `hkdf-hmac-sha256`, but
is encoded to base64 correctly.

The old `hkdf-hmac-sha256` method is redefined to use the base64 encoding
implemented in the original libolm implementation, and is deprecated: if both
clients involved in the verification support `hkdf-hmac-sha256.v2` as the
message authentication code, then `hkdf-hmac-sha256` must not be used, even if
both clients support it.

`hkdf-hmac-sha256` will be removed by a future MSC.

## Potential issues

None

## Alternatives

None

## Security considerations

This change does not introduce any security issues.

## Unstable prefix

Until this MSC is accepted, the key agreement protocol identifier
`org.matrix.msc3783.hkdf-hmac-sha256` should be used instead of
`hkdf-hmac-sha256.v2`.

## Dependencies

None
