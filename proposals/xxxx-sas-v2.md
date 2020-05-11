# SAS verification, v2

## Proposal

A new `key_agreement_protocol`, `curve25519-hkdf-sha256` is introduced. It is
the same as `curve25519` except that the info parameter for the HKDF is the
concatenation of:

  * The string `MATRIX_KEY_VERIFICATION_SAS|`.
  * The Matrix ID of the user who sent the `m.key.verification.start` message,
    followed by `|`.
  * The Device ID of the device which sent the `m.key.verification.start`
    message, followed by `|`.
  * The public key from the `m.key.verification.key` message sent by the device
    which sent the `m.key.verification.start` message, followed by `|`.
  * The Matrix ID of the user who sent the `m.key.verification.accept` message,
    followed by `|`.
  * The Device ID of the device which sent the `m.key.verification.accept`
    message, followed by `|`.
  * The public key from the `m.key.verification.key` message sent by the device
    which sent the `m.key.verification.accept` message, followed by `|`.
  * The `transaction_id` being used.

The differences from `curve25519` are the addition of the public keys, and the
addition of `|` as delimiter between the fields.

The `key_agreement_protocol` `curve25519` is deprecated and may be removed in
the future.

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix
