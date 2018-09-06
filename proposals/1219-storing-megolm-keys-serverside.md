Storing megolm keys serverside
==============================

Background
----------

We *optionally* let clients store a copy of their megolm inbound session keys
on the HS so that they can recover history if all devices are lost without an
explicit key export; fix UISIs; support clients with limited local storage for
keys.

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

On receipt of encryption keys (1st time):

1. client checks if there is an existing backup: `GET /room_keys/version`
   1. if not, ask if the user wants to back up keys
      1. if yes:
         1. generate new key pair
         2. create new backup version: `POST /room_keys/version`
         3. display private key to user to save TODO: specify how the key is
            displayed
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

### API

#### Backup versions

##### `POST /room_keys/version`

Create a new backup version.

Body parameters:

- `algorithm` (string): Required. The algorithm used for storing backups.
  Currently, only `m.megolm_backup.v1` is defined. (FIXME: change the algorithm
  name to include the encryption method)
- `auth_data` (string or object): Required. algorithm-dependent data.  For
  `m.megolm_backup.v1`, this is a signedjson object with the following keys:
  - `public_key` (string): the public key used to encrypt the backups
  - `signatures` (object): signatures of the public key

Example:

```javascript
{
  "algorithm": "m.megolm_backup.v1",
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

- `version` (integer): the backup version

##### `GET /room_keys/version`

Get information about the current version.

On success, returns a JSON object with keys:

- `algorithm` (string): Required. Same as in the body parameters for `POST
  /room_keys/version`.
- `auth_data` (string or object): Required. Same as in the body parameters for
  `POST /room_keys/version`.
- `version` (integer): the backup version

Error codes:

- `M_UNKNOWN`: No backup version has been created. FIXME: why not
  `M_NOT_FOUND`?

#### Storing keys

##### `PUT /room_keys/keys/${roomId}/${sessionId}?version=$v`

Store the key for the given session in the given room, using the given backup
version.

If the server already has a backup in the backup version for the given session
and room, then it will keep the "better" one ...

Body parameters:

- `first_message_index` (integer): Required. The index of the first message
  in the session that the key can decrypt.
- `forwarded_count` (integer): Required. The number of times this key has been
  forwarded.
- `is_verified` (boolean): Whether the device backing up the key has verified
  the device that the key is from.
- `session_data` (string or object): Algorithm-dependent data.  For
  `m.megolm_backup.v1`, this is an object with the following keys:
  - `ciphertext` (string): the encrypted version of the session key.  See below
    for how the session key is encoded.
  - `ephemeral` (string): the public ephemeral key that was used to encrypt the
    session key.
  - `mac` (string): the message authentication code for the ciphertext. FIXME:
    more details

On success, returns ... ?

Error codes:

- `M_WRONG_ROOM_KEYS_VERSION`: the version specified does not match the current
  backup version

##### `PUT /room_keys/keys/${roomId}?version=$v`

Store several keys for the given room, using the given backup version.

Behaves the same way as if the keys were added individually using `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`.

Body paremeters:
- `sessions` (object): an object where the keys are the session IDs, and the
  values are objects of the same form as the body in `PUT
  /room_keys/keys/${roomId}/${sessionId}?version=$v`.

Returns the same as `PUT
/room_keys/keys/${roomId}/${sessionId}?version=$v`

##### `PUT /room_keys/keys/?version=$v`

...

#### Retrieving keys

##### `GET /room_keys/keys/${roomId}/${sessionId}?version=$v`
##### `GET /room_keys/keys/${roomId}?version=$v`
##### `GET /room_keys/keys/?version=$v`

#### Deleting keys

##### `DELETE /room_keys/keys/${roomId}/${sessionId}?version=$v`
##### `DELETE /room_keys/keys/${roomId}?version=$v`
##### `DELETE /room_keys/keys/?version=$v`

#### Key format

Each session key is encoded as a JSON object with the properties:

- `algorithm` (string): `m.megolm.v1.aes-sha2`
- `sender_key` (string): base64-encoded device curve25519 key
- `sender_claimed_keys` (object): object containing the identity keys for the
  sending device
- `forwardingCurve25519KeyChain` (array): zero or more curve25519 keys for
  devices who forwarded the session key
- `session_key` (string): base64-encoded session key

...

Tradeoffs
---------

Security Considerations
-----------------------

An attacker who gains access to a user's account can delete or corrupt their
key backup.  This proposal does not attempt to protect against that.

An attacker who gains access to a user's account can create a new backup
version using a key that they control.  For this reason, clients SHOULD confirm
with users before sending keys to a new backup version.

Other Issues
------------

Since many clients will receive encryption keys at around the same time, they
will all want to back up their copies of the keys at around the same time,
which may increase load on the server if this happens in a big room.  (TODO:
how much of an issue is this?)  For this reason, clients should offset their
backup requests randomly.

Conclusion
----------
