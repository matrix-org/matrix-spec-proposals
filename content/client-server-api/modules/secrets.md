---
type: module
---

### Secrets

{{% added-in v="1.1" %}}

Clients may have secret information that they wish to be made available
to other authorised clients, but that the server should not be able to
see, so the information must be encrypted as it passes through the
server. This can be done either asynchronously, by storing encrypted
data on the server for later retrieval, or synchronously, by sending
messages to each other.

Each secret has an identifier that is used by clients to refer to the
secret when storing, fetching, requesting, or sharing the secret.
Secrets are plain strings; structured data can be stored by encoding it
as a string.

#### Storage

When secrets are stored on the server, they are stored in the user's
[account-data](#client-config), using an event type equal to the
secret's identifier. The keys that secrets are encrypted with are
described by data that is also stored in the user's account-data. Users
can have multiple keys, allowing them to control what sets of secrets
clients can access, depending on what keys are given to them.

##### Key storage

Each key has an ID, and the description of the key is stored in the
user's account\_data using the event type
`m.secret_storage.key.[key ID]`. The contents of the account data for
the key will include an `algorithm` property, which indicates the
encryption algorithm used, as well as a `name` property, which is a
human-readable name. Key descriptions may also have a `passphrase`
property for generating the key from a user-entered passphrase, as
described in [deriving keys from
passphrases](#deriving-keys-from-passphrases).

`KeyDescription`

| Parameter  | Type      | Description
|------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------|
| name       | string    | Optional. The name of the key. If not given, the client may use a generic name such as "Unnamed key", or "Default key" if the key is marked as the default key (see below). |
| algorithm  | string    | **Required.** The encryption algorithm to be used for this key. Currently, only `m.secret_storage.v1.aes-hmac-sha2` is supported.   |
| passphrase | string    | See [deriving keys from passphrases](#deriving-keys-from-passphrases) section for a description of this property.                   |

Other properties depend on the encryption algorithm, and are described
below.

A key can be marked as the "default" key by setting the user's
account\_data with event type `m.secret_storage.default_key` to an
object that has the ID of the key as its `key` property. The default key
will be used to encrypt all secrets that the user would expect to be
available on all their clients. Unless the user specifies otherwise,
clients will try to use the default key to decrypt secrets.

Clients that want to present a simplified interface to users by not supporting
multiple keys should use the default key if one is specified. If not default
key is specified, the client may behave as if there is no key is present at
all. When such a client creates a key, it should mark that key as being the
default key.

`DefaultKey`

| Parameter  | Type      | Description
|------------|-----------|------------------------------------------|
| key        | string    | **Required.** The ID of the default key. |

##### Secret storage

Encrypted data is stored in the user's account\_data using the event
type defined by the feature that uses the data. The account\_data will
have an `encrypted` property that is a map from key ID to an object. The
algorithm from the `m.secret_storage.key.[key ID]` data for the given
key defines how the other properties are interpreted, though it's
expected that most encryption schemes would have `ciphertext` and `mac`
properties, where the `ciphertext` property is the unpadded
base64-encoded ciphertext, and the `mac` is used to ensure the integrity
of the data.

`Secret`

| Parameter | Type             | Description |
|-----------|------------------|-------------|
| encrypted | {string: object} | **Required.** Map from key ID the encrypted data. The exact format for the encrypted data is dependent on the key algorithm. See the definition of `AesHmacSha2EncryptedData` in the [m.secret_storage.v1.aes-hmac-sha2](#msecret_storagev1aes-hmac-sha2) section. |

Example:

Some secret is encrypted using keys with ID `key_id_1` and `key_id_2`:

`org.example.some.secret`:

```
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

```
{
  "name": "Some key",
  "algorithm": "m.secret_storage.v1.aes-hmac-sha2",
  // ... other properties according to algorithm
}
```

`m.secret_storage.key.key_id_2`:

```
{
  "name": "Some other key",
  "algorithm": "m.secret_storage.v1.aes-hmac-sha2",
  // ... other properties according to algorithm
}
```

If `key_id_1` is the default key, then we also have:

`m.secret_storage.default_key`:

```
{
  "key": "key_id_1"
}
```

###### `m.secret_storage.v1.aes-hmac-sha2`

Secrets encrypted using the `m.secret_storage.v1.aes-hmac-sha2`
algorithm are encrypted using AES-CTR-256, and authenticated using
HMAC-SHA-256. The secret is encrypted as follows:

1.  Given the secret storage key, generate 64 bytes by performing an
    HKDF with SHA-256 as the hash, a salt of 32 bytes of 0, and with the
    secret name as the info. The first 32 bytes are used as the AES key,
    and the next 32 bytes are used as the MAC key
2.  Generate 16 random bytes, set bit 63 to 0 (in order to work around
    differences in AES-CTR implementations), and use this as the AES
    initialization vector. This becomes the `iv` property, encoded using
    base64.
3.  Encrypt the data using AES-CTR-256 using the AES key generated
    above. This encrypted data, encoded using base64, becomes the
    `ciphertext` property.
4.  Pass the raw encrypted data (prior to base64 encoding) through
    HMAC-SHA-256 using the MAC key generated above. The resulting MAC is
    base64-encoded and becomes the `mac` property.

`AesHmacSha2EncryptedData`

| Parameter  | Type    | Description
|------------|---------|------------------------------------------------------------------------|
| iv         | string  |   **Required.** The 16-byte initialization vector, encoded as base64.  |
| ciphertext | string  |   **Required.** The AES-CTR-encrypted data, encoded as base64.         |
| mac        | string  |   **Required.** The MAC, encoded as base64.                            |

For the purposes of allowing clients to check whether a user has
correctly entered the key, clients should:

1.  encrypt and MAC a message consisting of 32 bytes of 0 as described
    above, using the empty string as the info parameter to the HKDF in
    step 1.
2.  store the `iv` and `mac` in the `m.secret_storage.key.[key ID]`
    account-data.

`AesHmacSha2KeyDescription`

| Parameter   | Type   | Description                                                                                                                       |
|-------------|--------|-----------------------------------------------------------------------------------------------------------------------------------|
| name        | string | Optional. The name of the key.                                                                                                    |
| algorithm   | string | **Required.** The encryption algorithm to be used for this key. Currently, only `m.secret_storage.v1.aes-hmac-sha2` is supported. |
| passphrase  | object | See [deriving keys from passphrases](#deriving-keys-from-passphrases) section for a description of this property.                 |
| iv          | string | The 16-byte initialization vector, encoded as base64.                                                                             |
| mac         | string | The MAC of the result of encrypting 32 bytes of 0, encoded as base64.                                                             |

For example, the `m.secret_storage.key.key_id` for a key using this
algorithm could look like:

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

###### Key representation

When a user is given a raw key for `m.secret_storage.v1.aes-hmac-sha2`,
it will be presented as a string constructed as follows:

1.  The key is prepended by the two bytes `0x8b` and `0x01`
2.  All the bytes in the string above, including the two header bytes,
    are XORed together to form a parity byte. This parity byte is
    appended to the byte string.
3.  The byte string is encoded using base58, using the same [mapping as
    is used for Bitcoin
    addresses](https://en.bitcoin.it/wiki/Base58Check_encoding#Base58_symbol_chart),
    that is, using the alphabet
    `123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz`.
4.  The string is formatted into groups of four characters separated by
    spaces.

When decoding a raw key, the process should be reversed, with the
exception that whitespace is insignificant in the user's input.

###### Deriving keys from passphrases

A user may wish to use a chosen passphrase rather than a randomly
generated key. In this case, information on how to generate the key from
a passphrase will be stored in the `passphrase` property of the
`m.secret_storage.key.[key ID]` account-data. The `passphrase` property
has an `algorithm` property that indicates how to generate the key from
the passphrase. Other properties of the `passphrase` property are
defined by the `algorithm` specified.

Currently, the only algorithm defined is `m.pbkdf2`. For the `m.pbkdf2` algorithm, the `passphrase` property has the
following properties:

| Parameter  | Type    | Description                                                            |
|------------|---------|------------------------------------------------------------------------|
| algorithm  | string  | **Required.** Must be `m.pbkdf2`                                       |
| salt       | string  | **Required.** The salt used in PBKDF2.                                 |
| iterations | integer | **Required.** The number of iterations to use in PBKDF2.               |
| bits       | integer | Optional. The number of bits to generate for the key. Defaults to 256. |

The key is generated using PBKDF2 with SHA-512 as the hash, using the
salt given in the `salt` parameter, and the number of iterations given
in the `iterations` parameter.

Example:

```
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

#### Sharing

To request a secret from other devices, a client sends an
`m.secret.requests` device event with `action` set to `request` and
`name` set to the identifier of the secret. A device that wishes to
share the secret will reply with an `m.secret.send` event, encrypted
using olm. When the original client obtains the secret, it sends an
`m.secret.request` event with `action` set to `request_cancellation` to
all devices other than the one that it received the secret from. Clients
should ignore `m.secret.send` events received from devices that it did
not send an `m.secret.request` event to.

Clients must ensure that they only share secrets with other devices that
are allowed to see them. For example, clients should only share secrets
with the user’s own devices that are verified and may prompt the user to
confirm sharing the secret.

##### Event definitions

###### `m.secret.request`

Sent by a client to request a secret from another device or to cancel a
previous request. It is sent as an unencrypted to-device event.

| Parameter             | Type   | Description                                                                            |
|-----------------------|--------|----------------------------------------------------------------------------------------|
| name                  | string | Required if ``action`` is ``request``. The name of the secret that is being requested. |
| action                | enum   | **Required.** One of ["request", "request_cancellation"].                              |
| requesting_device_id  | string | **Required.** The ID of the device requesting the secret.                              |
| request_id            | string | **Required.** A random string uniquely identifying (with respect to the requester and the target) the target for a secret. If the secret is requested from multiple devices at the same time, the same ID may be used for every target. The same ID is also used in order to cancel a previous request.                                                  |

Example:

```json
{
  "name": "org.example.some.secret",
  "action": "request",
  "requesting_device_id": "ABCDEFG",
  "request_id": "randomly_generated_id_9573"
}
```

###### `m.secret.send`

Sent by a client to share a secret with another device, in response to
an `m.secret.request` event. It must be encrypted as an
`m.room.encrypted` event, then sent as a to-device event.

| Parameter   | Type   | Description                                                  |
|-------------|--------|--------------------------------------------------------------|
| request_id  | string | **Required.** The ID of the request that this a response to. |
|  secret     | string | **Required.** The contents of the secret.                    |

Example:

```json
{
  "request_id": "randomly_generated_id_9573",
  "secret": "ThisIsASecretDon'tTellAnyone"
}
```
