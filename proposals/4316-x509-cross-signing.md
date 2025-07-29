# MSC4316: External cross-signing signatures with X.509 certificates and (semi-)automated verification

Matrix allows users to establish explicit trust and prevent MITM attacks through [cross-signing] and
[device verification]. The current verification options require an out-of-band channel such as a
video call or meeting in person and comparing authentication strings or scanning QR codes. This
process is somewhat cumbersome and less helpful for people that haven't yet met in the physical
world.

As an example, say you've found the MXID of Dr. Bob, General Physician, online and invite him to
chat about your latest health issues. You may now verify him in a video call but you haven't
actually met Dr. Bob before and the person on the other end might as well be anybody. You do know
that Dr. Bob works in a hospital and the hospital has an X.509 certificate from a national health
CA. The hospital accrediting that Dr. Bob is in fact Dr. Bob would, therefore, help you trust him.
However, Matrix doesn't currently support binding Dr. Bob's cryptographic identity to his
organization's certificate.

To address this shortcoming, the present proposal introduces a mechanism to attach and share X.509
based signatures on cross-signing keys.

## Proposal

The `signatures` properties in the response of [`/_matrix/client/v3/keys/query`] are extended to
allow a special key `external`. As this is not a valid [MXID], it cannot clash with other keys
inside `signatures`. `external` is meant to store signatures that are tied to X.509 certificates in
the same [format] already used for other signatures. Since in this case the certificate encapsulates
both the signing algorithm and the public key, the generic string `x509` is used as the algorithm
identifier while the certificate's SHA-256 fingerprint encoded in [unpadded base64] is used as the
key identifier.

As a result, an externally signed device key looks like this:

``` json5
{
  "device_keys": {
    "@bob:hospital.org": {
      "ABCDEFGHIJ": {
        // Device identity & signing keys
        "keys": {
          "curve25519:ABCDEFGHIJ": "...",
          "ed25519:ABCDEFGHIJ": "..."
        },
        ...,
        "user_id": "@bob:hospital.org",
        "signatures": {
          "@bob:hospital.org": {
            // Device self-signature
            "ed25519:ABCDEFGHIJ": "...",
            // Self-signing key signature
            "ed25519:$SSK_BASE64": "..."
          },
          "external": {
            // External X.509 signature
            "x509:$FINGERPRINT_BASE64": "$SIGNATURE"
          }
        }
      }
    }
  },
  ...
}
```

Home servers MAY additionally include the certificate itself via a new top-level property `external`
that stores the DER encoding of the certificate encoded in [unpadded base64] under the same signing
key identifier.

``` json5
{
  "device_keys": { ... },
  ...
  "external": {
    "x509:$FINGERPRINT_BASE64": "$CERT.DER_BASE64"
  }
}
```

In closed federations, it is expected that clients are aware of a central PKI which obviates the
need to expose the certificate in [`/_matrix/client/v3/keys/query`].

Clients MAY check external signatures using the certificate and its chain. If they do, they SHOULD
also verify certificate validity, for instance, using OCSP. Clients MAY additionally present the
signing certificate to the user and prompt them for review and confirmation. Once a signature has
been checked successfully, clients SHOULD mark the signed key as verified.

Servers currently limit the visibility of signatures to [avoid leaking social graphs]. Since
external signatures are not tied to a signing account, servers MUST make any external signatures and
certificates in [`/_matrix/client/v3/keys/query`] visible to all users.

This proposal doesn't prescribe how an external signature is added to a user's account as this is
assumed to be an administrator task. It is expected that home servers will offer suitable admin APIs
to facilitate this task.

## Potential issues

Including certificates in [`/_matrix/client/v3/keys/query`] will increase the size of the response.

## Alternatives

External signatures and certificates could be combined by using PKCS \#7 detached signatures.

``` json5
"signatures": {
  "external": {
    "pkcs7": "$FILE.P7S_BASE64"
  }
}
```

This would remove the need to identify and look-up certificates. It would, however, fit less well
with the current signature format in Matrix.

## Security considerations

A client that was tricked into trusting a malign certificate may be tricked into considering
arbitrary users as verified.

## Unstable prefix

While this MSC is not considered stable, `external` should be referred to as
`de.gematik.msc4316.external`.

## Dependencies

This proposal doesn't depend on but plays together with [MSC4317].

  [cross-signing]: https://spec.matrix.org/v1.15/client-server-api/#cross-signing
  [device verification]: https://spec.matrix.org/v1.15/client-server-api/#device-verification
  [`/_matrix/client/v3/keys/query`]: https://spec.matrix.org/v1.15/client-server-api/#post_matrixclientv3keysquery
  [MXID]: https://spec.matrix.org/v1.15/appendices/#user-identifiers
  [format]: https://spec.matrix.org/v1.15/appendices/#signing-details
  [unpadded base64]: https://spec.matrix.org/v1.15/appendices/#unpadded-base64
  [avoid leaking social graphs]: https://spec.matrix.org/v1.15/client-server-api/#key-and-signature-security
  [MSC4317]: https://github.com/matrix-org/matrix-spec-proposals/pull/4317
