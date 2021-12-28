# Symmetric SSSS

[MSC1946 (Secure Secret Storage and
Sharing)](https://github.com/matrix-org/matrix-doc/pull/1946) proposed a way of
storing encrypted secrets on the server.  In the proposal, secrets were
encrypted using a Curve25519 key, which was chosen to allow easier migration
from key backups that we created before the backup key was stored using it.

However this does not provide any guarantees that data stored using the
proposal came from a trusted source.  To remedy this, we propose to change the
encryption to use AES with a MAC to ensure that only someone who knows the key
is able to store data.

## Proposal

* The `m.secret_storage.v1.curve25519-aes-sha2` method proposed in MSC1946 is
  removed.

* A new method, `m.secret_storage.v1.aes-hmac-sha2`, is added.  With this
  method, the Secret Storage key may be any size (though 256 bits is
  recommended), and data is encrypted as follows:

  1. Given the secret storage key, generate 64 bytes by performing an HKDF with
     SHA-256 as the hash, a salt of 32 bytes of 0, and with the secret name as
     the info.  The first 32 bytes are used as the AES key, and the next 32 bytes
     are used as the MAC key
  2. Generate 16 random bytes, set bit 63 to 0 (in order to work around
     differences in AES-CTR implementations), and use this as the AES
     initialization vector.  This becomes the `iv` property, encoded using base64.
  3. Encrypt the data using AES-CTR-256 using the AES key generated above.  This
     encrypted data, encoded using base64, becomes the `ciphertext` property.
  4. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256
     using the MAC key generated above.  The resulting MAC is base64-encoded and
     becomes the `mac` property.

  (We use AES-CTR to match file encryption and key exports.)

  If the key Secret Storage key is generated from a passphrase, information
  about how to generate the key is stored in the `passphrase` property of the
  key's account-data in a similar manner to what was done with the original
  `m.secret_storage.v1.curve25519-aes-sha2` method, except that there is an
  optional `bits` parameter that defaults to 256, and indicates the number of
  bits that should be generated from PBKDF2 (in other words, the size of the
  key).

* For the purposes of allowing clients to check whether a user has correctly
  entered the key, clients should:

  1. encrypt and MAC a message consisting of 32 bytes of 0 as described above,
     using the empty string as the info parameter to the HKDF in step 1.
  2. store the `iv` and `mac` in the `m.secret_storage.key.[key ID]`
     account-data.

* The `passthrough` property specified in the "Encoding the recovery key for
  server-side storage via MSC1946" section of MSC1219 is removed.  The primary
  purpose of that property was to allow easy migration of pre-MSC1946 backups,
  so that users could reuse the backup recovery key as the Secret Storage key
  without needing to re-enter the recovery key.  However, since we are now
  using a symmetric encryption algorithm, the client needs to know the key that
  is used to encrypt, so the purpose of the field cannot be fulfilled.

* Signing the Secret Storage key with the user's master cross-signing key is no
  longer required.  The key is trusted on the basis of the user entering the
  key/passphrase.


## Potential issues

Users who have data stored using the old encryption algorithm will need their
data migrated.  Clients that support the old algorithm but not the new
algorithm will not be able to use the migrated secrets until they are updated
with the new algorithms.  This should not be a major problem because the only
clients that are known to have implemented the old algorithm are Riot
Web/Android/iOS, and they have been upgraded to implement the new algorithm.


## Alternatives

Rather than switching to a symmetric encryption algorithm, we could stay with
an asymmetric encryption algorithm, and add on a method to authenticate the
data.  However, it is much safer to use well-known cryptographic methods rather
than trying to invent something new.  Since the main reason for using an
asymmetric scheme was to ease migration from older key backups without
requiring the user to re-enter the key, but this is no longer possible due to
the need to authenticate the data using the Secret Storage key, there is no
reason to stay with an asymmetric algorithm.  It is also better to use
cryptographic methods already used in Matrix where possible, rather than
introducing something new.
