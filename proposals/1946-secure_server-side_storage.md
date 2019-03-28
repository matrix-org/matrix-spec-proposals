# Secure Server-side Storage

Some features may require clients to store encrypted data on the server so that
it can be shared securely between clients.  For example, key backups (MSC-1219)
can store the decryption key for the backups on the server, or cross-signing
(MSC-1756) can store the signing keys.  This proposal presents a standardized
way of storing such data.

## Proposal

A user can have multiple keys used for encrypting data.  This allows the user
to selectively decrypt data.  For example, the user could have one key that can
decrypt everything, and another key that can only decrypt their user-signing
key for cross-signing.  Each key has an ID, and a discription of the key is
stored in the user's `account_data` using the `type` `m.secure_storage.key.[key
ID]`.  The contents of the account data for the key will include an `algorithm`
property, which indicates the encryption algorithm used, as well as a `name`
property, which is a human-readable name.  Other properties depend on the
encryption algorithm, and are described below.

Encrypted data can be stored using the `account_data` API.  The `type` for the
`account_data` is defined by the feature that uses the data.  For example,
decryption keys for key backups could be stored under the type
`m.megolm_backup.v1.recovery_key`, or the self-signing key for cross-signing
could be stored under the type `m.signing_key.self_signing`.

Data will be stored using using the following format:

```json
{
    "encrypted": {
      [key ID]: {
        "ciphertext": "base64+encoded+encrypted+data",
        "mac": "base64+encoded+mac"
      }
    }
}
```

The `encrypted` property is map from key ID to an object.  The algorithm for
the given key defines how the other properties are interpreted, though it's
expected that most encryption schemes would have `ciphertext` and `mac`
properties, where the `ciphertext` property is the unpadded base64-encoded
ciphertext, and the `mac` is used to ensure the integrity of the data.

FIXME: the key format was chosen so that existing backups could be easily
migrated by just copying the configuration from the backup config to the key
description.  However, we need a way of signalling that the key for the backup
is the same as the key for decrypting the other bits.  Maybe a special flag in
the account data?  Or special case backups somehow, say, have clients inspect
the backup's `auth_data` to see of the key config is the same?

### Encryption algorithms

#### `m.secure_storage.v1.curve25519-aes-sha2`

The data is encrypted and MACed as follows:

1. Generate an ephemeral curve25519 key, and perform an ECDH with the ephemeral
   key and the backup's public key to generate a shared secret.  The public
   half of the ephemeral key, encoded using base64, becomes the `ephemeral`
   property.
2. Using the shared secret, generate 80 bytes by performing an HKDF using
   SHA-256 as the hash, with a salt of 32 bytes of 0, and with the empty string
   as the info.  The first 32 bytes are used as the AES key, the next 32 bytes
   are used as the MAC key, and the last 16 bytes are used as the AES
   initialization vector.
4. Encrypt the data using AES-CBC-256 with PKCS#7 padding.  This encrypted
   data, encoded using base64, becomes the `ciphertext` property.
5. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256
   using the MAC key generated above.  The first 8 bytes of the resulting MAC
   are base64-encoded, and become the `mac` property.

(The key HKDF, AES, and HMAC steps are the same as what are used for encryption
in olm and megolm.)

FIXME: add an example of `m.secure_storage.key.*`, and of encrypted data.

##### Keys

When a user is given a raw key for `m.secure_storage.v1.curve25519-aes-sha2`,
it will be encoded as follows (this is the same as what is proposed in MSC1703):

* prepend the two bytes 0x8b and 0x01 to the key
* compute a parity byte by XORing all bytes of the resulting string, and append
  the parity byte to the string
* base58-encode the resulting byte string with the alphabet
  '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'.
* format the resulting ASCII string into groups of 4 characters separated by
  spaces.

When decoding a raw key, the process should be reversed, with the exception
that whitespace is insignificant in the user's ASCII input.

##### Passphrase

A user may wish to use a chosen passphrase rather than a randomly generated
key.  In this case, information on how to generate the key from a passphrase
will be stored in the `passphrase` property of the `m.secure_storage.key.[key
ID]` account-data:

```json
{
    "passphrase": {
        "algorithm": "m.pbkdf2",
        "salt": "MmMsAlty",
        "rounds": 100000
    },
    ...
}
```

###### `m.pbkdf2`

The key is generated using PBKDF2 using the salt given in the `salt`
parameter, and the number of rounds given in the `rounds` parameter.

## Tradeoffs

Rather than encrypting data on the server using a static key, clients can
exchange data by sending to_device messages encrypted using Olm.  This allows
clients to share data securely without requiring the user to enter keys or
passphrases.  However, users who have only one device and lose it will still
need a way to, for example, recover their key backup, so we must provide a way
for the data to be stored on the server.

Currently, only a public/private key mechanism is defined.  It may be useful to
also define a secret key mechanism.

## Potential issues

Keeping all the data and keys in account data means that it may clutter up the
`/sync`.  However, clients can filter out the data that they are not interested
in.  One possibility for addressing this would be to add a flag to the account
data to indicate whether it should come down the `/sync` or not.

## Security considerations

Yes.

## Conclusion

This proposal presents a common way for bits of encrypted data to be stored on
a user's homeserver for use by various features.
