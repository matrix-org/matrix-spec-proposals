# Secure Secret Storage and Sharing

Some features may require clients to store encrypted data on the server so that
it can be shared securely between clients.  Clients may also wish to securely
send such data directly to each other.  For example, key backups
([MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219)) can store the
decryption key for the backups on the server, or cross-signing
([MSC1756](https://github.com/matrix-org/matrix-doc/pull/1756)) can store the
signing keys.  This proposal presents a standardized way of storing such data.

## Proposal

Secrets are data that clients need to use and that are sent through or stored
on the server, but should not be visible to server operators.  Secrets are
plain strings -- if clients need to use more complicated data, they must be
encoded as a string, such as by encoding as JSON.

### Storage

If secret data is stored on the server, it must be encrypted in order to
prevent homeserver administrators from being able to read it.  A user can have
multiple keys used for encrypting data.  This allows the user to selectively
decrypt data on clients.  For example, the user could have one key that can
decrypt everything, and another key that can only decrypt their user-signing
key for cross-signing.

Key descriptions and secret data are both stored in the user's account_data.

#### Key storage

Each key has an ID, and the description of the key is stored in the user's
account_data using the event type `m.secret_storage.key.[key ID]`.  The contents
of the account data for the key will include an `algorithm` property, which
indicates the encryption algorithm used, as well as a `name` property, which is
a human-readable name.  The contents will be signed as signed JSON using the
user's master cross-signing key.  Other properties depend on the encryption
algorithm, and are described below.

Example:

A key with ID `abcdefg` is stored in `m.secret_storage.key.abcdefg`

```json
{
  "name": "Some key",
  "algorithm": "m.secret_storage.v1.curve25519-aes-sha2",
  // ... other properties according to algorithm
}
```

A key can be marked as the "default" key by setting the user's account_data
with event type `m.secret_storage.default_key` to the ID of the key.  The
default key will be used to encrypt all secrets that the user would expect to
be available on all their clients.  Unless the user specifies otherwise,
clients will try to use the default key to decrypt secrets.

Clients MUST ensure that the key is trusted before using it to encrypt secrets.
One way to do that is to have the client that creates the key sign the key
description (as signed JSON) using the user's master cross-signing key.
Another way to do that is to prompt the user to enter the passphrase and ensure
that the generated private key correponds to the public key.

#### Secret storage

Encrypted data is stored in the user's account_data using the event type
defined by the feature that uses the data.  For example, decryption keys for
key backups could be stored under the type `m.megolm_backup.v1.recovery_key`,
or the self-signing key for cross-signing could be stored under the type
`m.cross_signing.self_signing`.

The account_data will have an `encrypted` property that is a map from key ID
to an object.  The algorithm from the `m.secret_storage.key.[key ID]` data for
the given key defines how the other properties are interpreted, though it's
expected that most encryption schemes would have `ciphertext` and `mac`
properties, where the `ciphertext` property is the unpadded base64-encoded
ciphertext, and the `mac` is used to ensure the integrity of the data.

Example:

Some secret is encrypted using keys with ID `key_id_1` and `key_id_2`:

```json
{
  "encrypted": {
    "key_id_1": {
      "ciphertext": "base64+encoded+encrypted+data",
      "mac": "base64+encoded+mac",
      // ... other properties according to algorithm property in
      // m.secret_storage.key.key_id_1
    },
    "key_id_2": {
      // ...
    }
  }
}
```

#### Encryption algorithms

##### `m.secret_storage.v1.curve25519-aes-sha2`

The public key is stored in the `pubkey` property of the `m.secret_storage.key.[key
ID]` account_data as a base64-encoded string.

The data is encrypted and MACed as follows:

1. Generate an ephemeral curve25519 key, and perform an ECDH with the ephemeral
   key and the public key to generate a shared secret.  The public half of the
   ephemeral key, encoded using base64, becomes the `ephemeral` property.
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

For example, the `m.secret_storage.key.[key ID]` for a key using this algorithm
could look like:

```json
{
  "name": "m.default",
  "algorithm": "m.secret_storage.v1.curve25519-aes-sha2",
  "pubkey": "base64+public+key"
}
```

and data encrypted using this algorithm could look like this:

```json
{
  "encrypted": {
      "key_id": {
        "ciphertext": "base64+encoded+encrypted+data",
        "ephemeral": "base64+ephemeral+key",
        "mac": "base64+encoded+mac"
      }
  }
}
```

###### Keys

When a user is given a raw key for `m.secret_storage.v1.curve25519-aes-sha2`,
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

###### Passphrase

A user may wish to use a chosen passphrase rather than a randomly generated
key.  In this case, information on how to generate the key from a passphrase
will be stored in the `passphrase` property of the `m.secret_storage.key.[key
ID]` account-data:

```json
{
    "passphrase": {
        "algorithm": "m.pbkdf2",
        "salt": "MmMsAlty",
        "iterations": 100000
    },
    ...
}
```

**`m.pbkdf2`**

The key is generated using PBKDF2 using the salt given in the `salt` parameter,
and the number of iterations given in the `iterations` parameter.

### Sharing

Rather than (or in addition to) storing secrets on the server encrypted by a
shared key, devices can send secrets to each other, encrypted using olm.

To request a secret, a client sends a `m.secret.request` device event with `action`
set to `request` to other devices, and `name` set to the name of the secret
that it wishes to retrieve.  A device that wishes to share the secret will
reply with a `m.secret.send` event, encrypted using olm.  When the original
client obtains the secret, it sends a `m.secret.request` event with `action`
set to `request_cancellation` to all devices other than the one that it received the
secret from.  Clients should ignore `m.secret.send` events received from
devices that it did not send an `m.secret.request` event to.

Clients MUST ensure that they only share secrets with other devices that are
allowed to see them.  For example, clients SHOULD only share secrets with
devices that are verified and MAY prompt the user to confirm sharing the
secret.

If a feature allows secrets to be stored or shared, then for consistency it
SHOULD use the same name for both the account_data event type and the `name` in
the `m.secret.request`.

#### Event definitions

##### `m.secret.request`

Sent by a client to request a secret from another device.  It is sent as an
unencrypted to-device event.

- `name`: (string) Required if `action` is `request`. The name of the secret
  that is being requested.
- `action`: (enum) Required. One of ["request", "request_cancellation"].
- `requesting_device_id`: (string) Required. ID of the device requesting the
  secret.
- `request_id`: (string) Required. A random string uniquely identifying the
  request for a secret. If the secret is requested multiple times, it should be
  reused. It should also reused in order to cancel a request.

##### `m.secret.send`

Sent by a client to share a secret with another device, in response to an
`m.secret.request` event.  It MUST be encrypted as an `m.room.encrypted` event,
then sent as a to-device event.

- `request_id`: (string) Required. The ID of the request that this a response to.
- `secret`: (string) Required. The contents of the secret.

## Tradeoffs

Currently, only a public/private key mechanism is defined.  It may be useful to
also define a secret key mechanism.

## Potential issues

Keeping all the data and keys in account data means that it may clutter up
`/sync` requests.  However, clients can filter out the data that they are not interested
in.  One possibility for addressing this would be to add a flag to the account
data to indicate whether it should come down the `/sync` or not.

## Security considerations

By storing information encrypted on the server, this allows the server operator
to read the information if they manage to get hold of the decryption keys.
In particular, if the key is based on a passphrase and the passphrase can be
guessed, then the secrets could be compromised.  In order to help protect the
secrets, clients should provide feedback to the user when their chosen
passphrase is considered weak, and may also wish to prevent the user from
reusing their login password.

## Conclusion

This proposal presents a common way for bits of encrypted data to be stored on
a user's homeserver for use by various features.
