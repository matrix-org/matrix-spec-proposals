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

A new `message_authentication_code` method, `hkdf-hmac-sha256.v2` is introduced.  It
is the same as `hkdf-hmac-sha256`, except that the info parameter for the HKDF
is the concatenation of:

  * The string `MATRIX_KEY_VERIFICATION_MAC|`.
  * The Matrix ID of the user whose key is being MAC-ed, followed by `|`.
  * The Device ID of the device sending the MAC, followed by `|`.
  * The Matrix ID of the other user, followed by `|`.
  * The Device ID of the device receiving the MAC, followed by `|`.
  * The transaction_id being used, followed by `|`.
  * The Key ID of the key being MAC-ed, or the string `KEY_IDS` if the item
    being MAC-ed is the list of key IDs.

A new `short_authentication_string` method, `emoji.v2` is introduced.  It is
the same as `emoji`, but emoji number 34 is changed from 🔧 (`U+1F527` Spanner)
to ⭐ (`U+2B50` Star).

The `key_agreement_protocol` `curve25519`, `message_authentication_code`
`hkdf-hmac-sha256`, and `short_authentication_string` `emoji` are deprecated.

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix
