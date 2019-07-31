Storing megolm keys serverside
==============================

Background
----------

A user who uses end-to-end encryption will usually have many inbound group session
keys.  Users who log into new devices and want to read old messages will need a
convenient way to transfer the session keys from one device to another.  While
users can currently export their keys from one device and import them to
another, this is involves several steps and may be cumbersome for many users.
Users can also share keys from one device to another, but this has several
limitations, such as the fact that key shares only share one key at a time, and
require another logged-in device to be active.

To help resolve this, we *optionally* let clients store an encrypted copy of
their megolm inbound session keys on the homeserver.  Clients can keep the
backup up to date, so that users will always have the keys needed to decrypt
their conversations.  The backup could be used not just for new logins, but
also to support clients with limited local storage for keys (clients can store
old keys to the backup, and remove their local copy, retrieving the key from
the backup when needed).

To recover keys from the backup, a user will need to enter a recovery key to
decrypt the backup.  The backup will be encrypted using public key
cryptography, so that any of a user's devices can back up keys without needing
the user to enter the recovery key until they need to read from the backup.

See also:

* https://github.com/matrix-org/matrix-doc/issues/1219
* https://github.com/vector-im/riot-web/issues/3661
* https://github.com/vector-im/riot-web/issues/5675
* https://docs.google.com/document/d/1MOoIA9qEKIhUQ3UmKZG-loqA8e0BzgWKKlKRUGMynVc/edit#
  (old version of proposal)

Proposal
--------

This proposal creates new APIs to allow clients to back up room decryption keys
on the server.  Decryption keys are encrypted (using public key crypto) before
being sent to the server along with some unencrypted metadata to allow the
server to manage the backups, overwriting backups with "better" versions of the
keys.  The user is given a private recovery key to save for recovering the keys
from the backup.

Clients can create new versions of backups.  Aside from the initial backup
creation, a client might start a new version of a backup when, for example, a
user loses a device, and wants to ensure that that device does not get any new
decryption keys.

Once one client has created a backup version, other clients can fetch the
public key for the backup from the server and add keys to the backup, if they
trust that the backup was not created by a malicious device.

### Possible UX for interactive clients

This section gives an example of how a client might handle key backups.  Clients
may behave differently.

On receipt of encryption keys (1st time):

1. client checks if there is an existing backup: `GET /room_keys/version`
   1. if not, ask if the user wants to back up keys
      1. if yes:
         1. generate new curve25519 key pair
         2. create new backup version: `POST /room_keys/version`
         3. display private key for user to save (see below for the format)
      2. if no, exit and remember decision (user can change their mind later)
      3. while prompting, continue to poll `GET /room_keys/versions`, as
         another device may have created a backup.  If so, go to 1.2.
   2. if yes, get public key, prompt user to verify a device that signed the
      key¹, or enter recovery key (which can derive the backup key).
      1. User can also decide to create a new backup, in which case, go to 1.1.
2. send key to backup: `PUT /room_keys/keys/${roomId}/${sessionId}?version=$v`
3. continue backing up keys as we receive them (may receive a
   `M_WRONG_ROOM_KEYS_VERSION` error if a new backup version has been created:
   see below)

On `M_WRONG_ROOM_KEYS_VERSION` error when trying to `PUT` keys:

1. get the current version
2. notify the user that there is a new backup version, and display relevant
   information
3. confirm with user that they want to use the backup (user may want use the
   backup, to stop backing up keys, or to create a new backup)
4. verify the device that signed the backup key¹, or enter recovery key

¹: cross-signing (when that is completed) can be used to verify the device
that signed the key.

On receipt of undecryptable message:

1. ask user if they want to restore backup (ask whether to get individual key,
   room keys, or all keys).  (This can be done in the same place as asking if
   the user wants to request keys from other devices.)
2. if yes, prompt for private key, and get keys: `GET /room_keys/keys`

Users can also set up, disable, or rotate backups, or restore from backup via user
settings.

### Recovery key

The recovery key can be saved by the user directly, stored encrypted on the
server (using the method proposed in
[MSC1946](https://github.com/matrix-org/matrix-doc/issues/1946)), or both.  If
the key is saved directly by the user, then the code is constructed as follows:

1. The 256-bit curve25519 private key is prepended by the bytes `0x8B` and
   `0x01`
2. All the bytes in the string are above are XORed together to form a parity
   byte. This parity byte is appended to the byte string.
3. The byte string is encoded using base58, using the same mapping as is used
   for Bitcoin addresses.

This 58-character string is presented to the user to save.  Implementations may
add whitespace to the recovery key; adding a space every 4th character is
recommended.

When reading in a recovery key, clients must disregard whitespace.  Clients
must base58-decode the code, ensure that the first two bytes of the decoded
string are `0x8B` and `0x01`, ensure that XOR-ing all the bytes together
results in 0, and ensure that the total length of the decoded string
is 35 bytes.  Clients must then remove the first two bytes and the last byte,
and use the resulting string as the private key to decrypt backups.

If MSC1946 is used to store the key on the server, it must be stored using the
`account_data` `type` `m.megolm_backup.v1`.

As a special case, if the recovery key is the same as the curve25519 key used
for storing the key, then the contents of the `m.megolm_backup.v1`
`account_data` for that key will be the an object with a `passthrough` property
whose value is `true`.  For example, if `m.megolm_backup.v1` is set to:

```json
{
  "encrypted": {
    "key_id": {
      "passthrough": true
    }
  }
}
```

means that the recovery key for the backup is the same as the private key for
the key with ID `key_id`. (This is mostly intended to provide a migration path
for for backups that were created using an earlier draft that stored the
recovery information in the `auth_data`.)

### API

#### Backup versions

##### `POST /room_keys/version`

Create a new backup version.

Body parameters:

- `algorithm` (string): Required. The algorithm used for storing backups.
  Currently, only `m.megolm_backup.v1.curve25519-aes-sha2` is defined.
- `auth_data` (object): Required. algorithm-dependent data.  For
  `m.megolm_backup.v1.curve25519-aes-sha2`, see below for the definition of
  this property.

Example:

```javascript
{
  "algorithm": "m.megolm_backup.v1.curve25519-aes-sha2",
  "auth_data": {
    "public_key": "abcdefg",
    "signatures": {
      "something": {
        "ed25519:something": "hijklmnop"
      }
    }
  }
}
```

On success, returns a JSON object with keys:

- `version` (string): the backup version

##### `GET /room_keys/version/{version}`

Get information about the given version, or the current version if `/{version}`
is omitted.

On success, returns a JSON object with keys:

- `algorithm` (string): Required. Same as in the body parameters for `POST
  /room_keys/version`.
- `auth_data` (object): Required. Same as in the body parameters for
  `POST /room_keys/version`.
- `version` (string): Required. The backup version.
- `hash` (string): Required. The hash value which is an opaque string 
 representing stored keys in the backup. Client can compare it with the `hash`
 value they received in the response of their last key storage request.
 If not equal, another matrix client pushed new keys to the backup.
- `count` (number): Required. The number of keys stored in the backup.

Error codes:

- `M_NOT_FOUND`: No backup version has been created.

##### `PUT /room_keys/version/{version}`

Update information about the given version. Only `auth_data` can be updated.

Body parameters:

- `algorithm` (string): Required. Must be the same as in the body parameters for `GET
 /room_keys/version`.
- `auth_data` (object): Required. algorithm-dependent data.  For
  `m.megolm_backup.v1.curve25519-aes-sha2`, see below for the definition of
  this property.
- `version` (string): Required. The backup version. Must be the same as the query parameter or must be the current version.

Example:

```javascript
{
  "algorithm": "m.megolm_backup.v1.curve25519-aes-sha2",
  "auth_data": {
    "public_key": "abcdefg",
    "signatures": {
      "something": {
        "ed25519:something": "hijklmnop"
        "ed25519:anotherthing": "abcdef"
      }
    }
  },
  "version": "42"
}
```

On success, returns the empty JSON object.

Error codes:

- `M_NOT_FOUND`: No backup version found.

#### Storing keys

##### `PUT /room_keys/keys/${roomId}/${sessionId}?version=$v`

Store the key for the given session in the given room, using the given backup
version.

If the server already has a backup in the backup version for the given session
and room, then it will keep the "better" one.  To determine which one is
"better", key backups are compared first by the `is_verified` flag (`true` is
better than `false`), then by the `first_message_index` (a lower number is better),
and finally by `forwarded_count` (a lower number is better).

Body parameters:

- `first_message_index` (integer): Required. The index of the first message
  in the session that the key can decrypt.
- `forwarded_count` (integer): Required. The number of times this key has been
  forwarded.
- `is_verified` (boolean): Required. Whether the device backing up the key has
  verified the device that the key is from.
- `session_data` (object): Required. Algorithm-dependent data.  For
  `m.megolm_backup.v1.curve25519-aes-sha2`, see below for the definition of
  this property.

On success, returns a JSON object with keys:

- `hash` (string): Required. The new hash value representing stored keys. See
`GET /room_keys/version/{version}` for more details.
- `count` (number): Required. The new count of keys stored in the backup.

Error codes:

- `M_WRONG_ROOM_KEYS_VERSION`: the version specified does not match the current
  backup version

Example:

`PUT /room_keys/keys/!room_id:example.com/sessionid?version=1`

```javascript
{
  "first_message_index": 1,
  "forwarded_count": 0,
  "is_verified": true,
  "session_data": {
    "ephemeral": "base64+ephemeral+key",
    "ciphertext": "base64+ciphertext+of+JSON+data",
    "mac": "base64+mac+of+ciphertext"
  }
}
```

Result:

```javascript
{
  "hash": "abcdefghi",
  "count": 10
}
```

##### `PUT /room_keys/keys/${roomId}?version=$v`

Store several keys for the given room, using the given backup version.

Behaves the same way as if the keys were added individually using `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`.

Body parameters:
- `sessions` (object): an object where the keys are the session IDs, and the
  values are objects of the same form as the body in `PUT
  /room_keys/keys/${roomId}/${sessionId}?version=$v`.

Returns the same as `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`.

Example:

`PUT /room_keys/keys/!room_id:example.com?version=1`

```javascript
{
  "sessions": {
    "sessionid": {
      "first_message_index": 1,
      "forwarded_count": 0,
      "is_verified": true,
      "session_data": {
        "ephemeral": "base64+ephemeral+key",
        "ciphertext": "base64+ciphertext+of+JSON+data",
        "mac": "base64+mac+of+ciphertext"
      }
    }
  }
}
```

Result:

```javascript
{
  "hash": "abcdefghi",
  "count": 10
}
```

##### `PUT /room_keys/keys?version=$v`

Store several keys, using the given backup version.

Behaves the same way as if the keys were added individually using `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`.

Body parameters:
- `rooms` (object): an object where the keys are the room IDs, and the values
  are objects of the same form as the body in `PUT
  /room_keys/keys/${roomId}/?version=$v`.

Returns the same as `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`

Example:

`PUT /room_keys/keys/!room_id:example.com?version=1`

```javascript
{
  "rooms": {
    "!room_id:example.com": {
      "sessions": {
        "sessionid": {
          "first_message_index": 1,
          "forwarded_count": 0,
          "is_verified": true,
          "session_data": {
            "ephemeral": "base64+ephemeral+key",
            "ciphertext": "base64+ciphertext+of+JSON+data",
            "mac": "base64+mac+of+ciphertext"
          }
        }
      }
    }
  }
}
```

Result:

```javascript
{
  "hash": "abcdefghi",
  "count": 10
}
```

#### Retrieving keys

When retrieving keys, the `version` parameter is optional, and defaults to
retrieving the latest backup version.

##### `GET /room_keys/keys/${roomId}/${sessionId}?version=$v`

Retrieve the key for the given session in the given room from the backup.

On success, returns a JSON object in the same form as the request body of `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`.

Error codes:

- M_NOT_FOUND: The session is not present in the backup, or the requested
  backup version does not exist.

##### `GET /room_keys/keys/${roomId}?version=$v`

Retrieve the all the keys for the given room from the backup.

On success, returns a JSON object in the same form as the request body of `PUT
/room_keys/keys/${roomId}?version=$v`.

If the backup version exists but no keys are found, then this endpoint returns
a successful response with body:

```
{
  "sessions": {}
}
```

Error codes:

- `M_NOT_FOUND`: The requested backup version does not exist.

##### `GET /room_keys/keys?version=$v`

Retrieve all the keys from the backup.

On success, returns a JSON object in the same form as the request body of `PUT
/room_keys/keys?version=$v`.

If the backup version exists but no keys are found, then this endpoint returns
a successful response with body:

```
{
  "rooms": {}
}
```

Error codes:

- `M_NOT_FOUND`: The requested backup version does not exist.

#### Deleting keys

##### `DELETE /room_keys/keys/${roomId}/${sessionId}?version=$v`
##### `DELETE /room_keys/keys/${roomId}?version=$v`
##### `DELETE /room_keys/keys/?version=$v`

Deletes keys from the backup.

On success, returns the empty JSON object.

#### `m.megolm_backup.v1.curve25519-aes-sha2` definitions

##### `auth_data` for backup versions

The `auth_data` property for the backup versions endpoints for
`m.megolm_backup.v1.curve25519-aes-sha2` is a signedjson object with the
following keys:

- `public_key` (string): the curve25519 public key used to encrypt the backups
- `signatures` (object): signatures of the public key

##### `session_data` for key backups

The `session_data` field in the backups is constructed as follows:

1. Encode the session key to be backed up as a JSON object with the properties:
   - `algorithm` (string): `m.megolm.v1.aes-sha2`
   - `sender_key` (string): base64-encoded device curve25519 key
   - `sender_claimed_keys` (object): object containing the identity keys for the
     sending device
   - `forwarding_curve25519_key_chain` (array): zero or more curve25519 keys
     for devices who forwarded the session key
   - `session_key` (string): base64-encoded (unpadded) session key
2. Generate an ephemeral curve25519 key, and perform an ECDH with the ephemeral
   key and the backup's public key to generate a shared secret.  The public
   half of the ephemeral key, encoded using base64, becomes the `ephemeral`
   property of the `session_data`.
3. Using the shared secret, generate 80 bytes by performing an HKDF using
   SHA-256 as the hash, with a salt of 32 bytes of 0, and with the empty string
   as the info.  The first 32 bytes are used as the AES key, the next 32 bytes
   are used as the MAC key, and the last 16 bytes are used as the AES
   initialization vector.
4. Stringify the JSON object, and encrypt it using AES-CBC-256 with PKCS#7
   padding.  This encrypted data, encoded using base64, becomes the
   `ciphertext` property of the `session_data`.
5. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256
   using the MAC key generated above.  The first 8 bytes of the resulting MAC
   are base64-encoded, and become the `mac` property of the `session_data`.

(The key HKDF, AES, and HMAC steps are the same as what are used for encryption
in olm and megolm.)

Security Considerations
-----------------------

An attacker who gains access to a user's account can delete or corrupt their
key backup.  This proposal does not attempt to protect against that.

An attacker who gains access to a user's account can create a new backup
version using a key that they control.  For this reason, clients SHOULD confirm
with users before sending keys to a new backup version or verify that it was
created by a trusted device by checking the signature.  One way to confirm the
new backup version if the signature cannot be checked is by asking the user to
enter the recovery key, and confirming that the backup's public key matches
what is expected.

Other Issues
------------

Since many clients will receive encryption keys at around the same time, they
will all want to back up their copies of the keys at around the same time,
which may increase load on the server if this happens in a big room.  (TODO:
how much of an issue is this?)  For this reason, clients should offset their
backup requests randomly.

Conclusion
----------

This proposal allows users to securely and conveniently back up and restore
their decryption keys so that users logging into a new device can decrypt old
messages.
