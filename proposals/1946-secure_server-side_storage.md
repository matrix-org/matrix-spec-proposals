# Secure Secret Storage and Sharing

Some features may require clients to store encrypted data on the server so that
it can be shared securely between clients.  Clients may also wish to securely
send such data directly to each other.  For example, key backups
([MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219)) can store the
decryption key for the backups on the server, or cross-signing
([MSC1756](https://github.com/matrix-org/matrix-doc/pull/1756)) can store the
signing keys.  This proposal presents a standardized way of storing such data.

## Changes

- [MSC2472](https://github.com/matrix-org/matrix-doc/pull/2472) changed the
  encryption algorithm used from an asymmetric algorithm (Curve25519) to a
  symmetric algorithm (AES).

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
a human-readable name.  Other properties depend on the encryption algorithm,
and are described below.

Example:

A key with ID `abcdefg` is stored in `m.secret_storage.key.abcdefg`

```json
{
  "name": "Some key",
  "algorithm": "m.secret_storage.v1.aes-hmac-sha2",
  // ... other properties according to algorithm
}
```

A key can be marked as the "default" key by setting the user's account_data
with event type `m.secret_storage.default_key` to an object that has the ID of
the key as its `key` property.  The default key will be used to encrypt all
secrets that the user would expect to be available on all their clients.
Unless the user specifies otherwise, clients will try to use the default key to
decrypt secrets.

#### Secret storage

Encrypted data is stored in the user's account_data using the event type
defined by the feature that uses the data.  For example, decryption keys for
key backups could be stored under the type `m.megolm_backup.v1`,
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

`org.example.some.secret`:

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

and the key descriptions for the keys would be:

`m.secret_storage.key.key_id_1`:

```json
{
  "name": "Some key",
  "algorithm": "m.secret_storage.v1.aes-hmac-sha2",
  // ... other properties according to algorithm
}
```

`m.secret_storage.key.key_id_2`:

```json
{
  "name": "Some other key",
  "algorithm": "m.secret_storage.v1.aes-hmac-sha2",
  // ... other properties according to algorithm
}
```

#### Encryption algorithms

##### `m.secret_storage.v1.aes-hmac-sha2`

Secrets are encrypted using AES-CTR-256 and MACed using HMAC-SHA-256.  The data
is encrypted and MACed as follows:

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

For the purposes of allowing clients to check whether a user has correctly
entered the key, clients should:

  1. encrypt and MAC a message consisting of 32 bytes of 0 as described above,
     using the empty string as the info parameter to the HKDF in step 1.
  2. store the `iv` and `mac` in the `m.secret_storage.key.[key ID]`
     account-data.

For example, the `m.secret_storage.key.key_id` for a key using this algorithm
could look like:

```json
{
  "name": "m.default",
  "algorithm": "m.secret_storage.v1.aes-hmac-sha2",
  "iv": "random+data",
  "mac": "mac+of+encrypted+zeros"
}
```

and data encrypted using this algorithm could look like this:

```json
{
  "encrypted": {
      "key_id": {
        "iv": "16+bytes+base64",
        "ciphertext": "base64+encoded+encrypted+data",
        "mac": "base64+encoded+mac"
      }
  }
}
```

###### Keys

When a user is given a raw key for `m.secret_storage.v1.aes-hmac-sha2`,
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
        "iterations": 100000,
        "bits": 256
    },
    ...
}
```

**`m.pbkdf2`**

The key is generated using PBKDF2 using the salt given in the `salt` parameter,
and the number of iterations given in the `iterations` parameter.  The key size
that is generated is given by the `bits` parameter, or 256 bits if no `bits`
parameter is given.

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
the user’s own devices that are verified and MAY prompt the user to confirm sharing the
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
