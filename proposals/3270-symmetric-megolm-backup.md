# MSC3270: Symmetric megolm backup
The current megolm backup uses asymmetric encryption. This was chosen so that
clients without the private key can still add their own megolm sessions to the
backup. This, however, allows a homeserver admin to inject their own malicious
megolm session into someone’s backup and then send an encrypted message as a user
that they wish to impersonate.  Due to this, some clients such as Element [warn the
user](https://github.com/vector-im/element-web/issues/14323#issuecomment-740855963)
that a message cannot be authenticated when the megolm session for that
message was obtained from backup.

Using symmetric encryption for megolm backup would fix this attack vector,
since keys added by untrusted devices would be undecryptable, thus allowing keys
obtained from backup to be trusted.  Additionally, many clients cache the
megolm private key anyway, making the original reason for choosing asymmetric
encryption obsolete.

**Credits:** This proposal was originally written by @sorunome.

## Proposal
This proposal introduces a new megolm backup algorithm, `m.megolm_backup.v1.aes-hmac-sha2`.
The backup method `m.megolm_backup.v1.curve25519-aes-sha2`
is deprecated.

### `session_data`
The session data of the megolm backup is an object containing the `iv` property
and the `ciphertext` property. Below is described how to generate these from
the megolm backup key.  The data to be encoded is the same JSON-encoded data as
in `m.megolm_backup.v1.curve25519-aes-sha2`.

As such, a complete `KeyBackupData` object could look as follows:

```json
{
  "first_message_index": 0,
  "forwarded_count": 0,
  "is_verified": true,
  "session_data": {
    "iv": "cL/0MJZaiEd3fNU+I9oJrw",
    "ciphertext": "WL73Pzdk5wZdaaSpaeRH0uZYKcxkuV8IS6Qa2FEfA1+vMeRLuHcWlXbMX0w"
  }
}
```

### Encryption
Room keys are encrypted using AES-GCM using the following process:

1. Encode the session key to be backed up as a JSON object with the same
   properties as with `m.megolm_backup.v1.curve25519-aes-sha2`, with the
   addition of an optional property `untrusted`, which is a boolean indicating
   whether the Megolm session should be considered as untrusted, for example
   because it came from an untrusted source.  If the `untrusted` property is
   absent, the key should be considered as trusted.
2. Given the megolm backup key, generate 32 bytes by performing an HKDF with
   SHA-256 as the hash, a salt of 32 bytes of 0, and with `<session ID>|<backup
   version>` as the info. This is the AES encryption key.
3. Generate 16 random bytes, and use this as the AES initialization
   vector. This becomes the `iv` property, encoded using unpadded base64.
4. Stringify the JSON object and encrypt it using AES-GCM-256 using the AES key
   and initialization vector generated above. This encrypted data, encoded
   using unpadded base64, becomes the `ciphertext` property.

### `auth_data`
Similar to symmetric SSSS, the `auth_data` object in the `versions` reply
contains information to verify that you indeed have the correct private
key. For that, you generate a random initialization vector and encrypt the
empty string using the method above, and put the `iv` and the `ciphertext` into
the `auth_data` object. For session ID and backup version, an empty string is
used. As such, a reply to the `versions` endpoint could look as follows:

```json
{
  "algorithm": "m.megolm_backup.v1.aes-hmac-sha2",
  "auth_data": {
    "iv": "cL/0MJZaiEd3fNU+I9oJrw",
    "ciphertext": "+xozp909S6oDX8KRV8D8ZFVRyh7eEYQpPP76f+DOsnw"
  },
  "count": 42,
  "etag": "meow",
  "version": "foxies"
}
```

### Secret key storage
The secret key for symmetric megolm is stored in SSSS base64-encoded with the
name `m.megolm_backup.v1.<backup version>`.

### Transitioning to symmetric backup

Clients that implement this backup method should consider older clients,
which will not be able to use backups created using this method.  For example,
clients can initially be updated so that they will be able to use backups
created using this method, but not yet create new backups using this method.
Some time later, once the client author deems that a sufficient number of
clients have been updated to use the new backup method, the client can be
modified such that new backups are created using this method.

## Potential issues
Many users already have an asymmetric megolm backup and rely on it. In order to
not lose any megolm keys, clients would have to implement a migration to
symmetric megolm backup.  When doing so, the existing keys should be marked as
untrusted.

## Alternatives
An earlier version of this MSC used the same encryption as is currently used in
[symmetric
SSSS](https://github.com/matrix-org/matrix-spec-proposals/pull/2472).  However,
it was
[later](https://matrix.org/blog/2022/09/28/upgrade-now-to-address-encryption-vulns-in-matrix-sdks-and-clients)
noted that this method is not "IND-CCA2 secure". As a result, it now uses
AES-GCM-256 instead.

The authenticity of keys could be established in backups using the
`m.megolm_backup.v1.curve25519-aes-sha2` algorithm by adding a signature or a
MAC.  However, this would require managing another key for the key backup.  It
would be easier for clients to only need to manage one key.

## Security considerations
The proposed method requires clients to cache the encryption key for the key
backup.  This means that an attacker who compromises a client that uses the key
backup will have access to all the key stored in the backup.  Since most
clients already cache the decryption key for current backups, this is not a
change from current practice.

To migrate an existing backup to the new method, clients will need the SSSS key
to read the existing backup and to store the key for the new backup.  When the
user enters the SSSS key, the client will have access to all of the other
secrets stored in SSSS.  In general, most users already trust their clients
with their secrets, or could select a trusted client to perform the migration.

## Unstable prefix
While this feature is in development, implementations should use
`org.matrix.msc3270.v2.aes-hmac-sha2` as the backup algorithm.

`org.matrix.msc3270.v1.aes-hmac-sha2` was used in a previous version that used
AES-CTR-256 for encryption.
