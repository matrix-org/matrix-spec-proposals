# MSC4048: Authenticated key backup

The [server-side key
backups](https://spec.matrix.org/unstable/client-server-api/#server-side-key-backups)
allows clients to store event decryption keys so that when the user logs in to
a new device, they can decrypt old messages.  The current algorithm encrypts
the event keys using an asymmetric algorithm, allowing clients to upload keys to
the backup without necessarily giving them the ability to read from the
backup.  For example, this allows for a partially-trusted client to be able to
read (and save the keys for) current messages, but not read old messages.

However, since the event decryption keys are encrypted using an asymmetric
algorithm, this allows anyone who knows the public key to write to the backup.
As a result, keys loaded from the backup must be marked as unauthenticated,
leading to [usability
issues](https://github.com/vector-im/element-web/issues/14323).

[MSC3270](https://github.com/matrix-org/matrix-spec-proposals/pull/3270) tries
to fix this issue by using a symmetric, authenticated encryption algorithm,
which ensures that only someone who knows the secret key can write to the
backup.  However this removes the ability for a client to be able to write to
the backup without being able to read from it.

We propose to continue using an asymmetric encryption algorithm in the backup,
but to ensure authenticity by producing a MAC using a key derived from the
backup's decryption key.

## Proposal

A user who has a key backup derives a new backup MAC key by performing HKDF on
the backup decryption key (as raw unencoded bytes) with no salt and an info
parameter of `"MATRIX_BACKUP_MAC_KEY"` and generating 32 bytes (256 bits):

    backup_mac_key = HKDF("", decryption_key, "MATRIX_BACKUP_MAC_KEY", 32)

The backup MAC key can be shared/stored using [the Secrets
module](https://spec.matrix.org/unstable/client-server-api/#secrets) using the
name `m.megolm_backup.v1.mac`.  Note that if the backup decryption key (the
secret using the name `m.megolm_backup.v1`) is stored/shared, then the backup
MAC key does not need to be stored/shared as it can be derived from the backup
decryption key.

The `SessionData` object for the [`m.megolm_backup.v1.curve25519-aes-sha2` key
backup
algorithm](https://spec.matrix.org/unstable/client-server-api/#backup-algorithm-mmegolm_backupv1curve25519-aes-sha2)
key backup algorithm has a new optional `authenticated` property, defaulting to
`false`.  This property indicates whether the device that uploaded the key to
the backup believes that the key belongs to the given `sender_key`.  This is
true if: a) the key was received via an Olm-encrypted `m.room_key` event from
the `sender_key`, b) the key was received via a trusted key forward
([MSC3879](https://github.com/matrix-org/matrix-spec-proposals/pull/3879)), or
c) the key was downloaded from the key backup, with the `authenticated`
property set to `true` and was authenticated (for example using the method from
this proposal).  If the `session_data` does not have a `mac2` property (see
below), then this flag must be treated as being `false`.

No changes are made to the `AuthData` for the
`m.megolm_backup.v1.curve25519-aes-sha2` key backup algorithm.

The following changes are made to the cleartext `session_data` property of the
`KeyBackupData` object:

- a new `mac2` [FIXME: get a better name.  suggestions?] property is added,
  which is a MAC of the `SessionData` ciphertext (prior to base64-encoding),
  using HMAC-SHA-256 with the backup MAC key derived above.
- the current `mac` property is deprecated.  Clients should continue to produce
  it for compatibility with older clients, but should no longer use it to
  verify the contents of the backup if the `mac2` property is present.  Clients
  should also accept `session_data` that does not have the `mac` property if
  the `mac2` property is present, as the `mac` property may become optional in
  the future.

The [construction of the `session_data`
property](https://spec.matrix.org/unstable/client-server-api/#backup-algorithm-mmegolm_backupv1curve25519-aes-sha2)
thus becomes:

1. Encode the session key to be backed up as a JSON object using the
   `SessionData`.
2. Generate an ephemeral Curve25519 key, and perform an ECDH with the ephemeral
   key and the backup’s public key to generate a shared secret. The public half
   of the ephemeral key, encoded using unpadded base64, becomes the `ephemeral`
   property of the `session_data`.
3. Using the shared secret, generate 80 bytes by performing an HKDF using
   SHA-256 as the hash, with a salt of 32 bytes of 0, and with the empty string
   as the info. The first 32 bytes are used as the AES key, the next 32 bytes
   are used as the MAC key, and the last 16 bytes are used as the AES
   initialization vector.
4. Stringify the JSON object, and encrypt it using AES-CBC-256 with PKCS#7
   padding. This encrypted data, encoded using unpadded base64, becomes the
   `ciphertext` property of the `session_data`.
5. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256
   using the MAC key generated above. The first 8 bytes of the resulting MAC
   are base64-encoded, and become the `mac` property of the `session_data`.
6. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256
   using the backup MAC key.  The MAC is base64-encoded (unpadded), and becomes
   the `mac2` property of the `session_data`.

FIXME: should the server compare the `mac2` when a client uploads a key to the
backup, when deciding whether to keep the existing key or replace it with a new
key?

## Potential issues

For users with existing backups, in order to start storing backup keys using
this format, the user may need to enter their Secret Storage key so that the
client can obtain the backup decryption key, if it does not already have it
cached, in order to derive the backup MAC key.  If a user has multiple clients,
one client may try to obtain the backup MAC key from other clients using Secret
Sharing, but it does not have a way of knowing which clients, if any, have the
backup MAC key.

## Alternatives

As mentioned above, we could switch to using a symmetric encryption algorithm
for the key backup.  However, this is not backwards-compatible, and does not
allow for clients that can write to the backup without reading.

Rather than using a new MAC key, we could use an existing signing key, such as
one of the cross-signing keys.  This would remove the need for users to enter
their Secret Storage key to add the new signing key.  However, this means that
a user cannot create a key backup without also using cross-signing.  Using a
separate key also allows the user to give someone else (such as a bot)
permission to write to their backups without allowing them to perform any
cross-signing operations.

A previous version of this MSC used a signing key that was generated randomly.
The method presented in the current version has the following advantages:

- No changes to `AuthData` are necessary, so a new backup version is not
  required.
- A MAC is faster to calculate.  The main advantage of a signature is that it
  allows one to verify the signature without knowing the private key, but in
  this case, reading is a more privileged action than writing, and writers
  already need to know the private/secret key.
- Since the MAC key is derived from the decryption key, two clients can be
  upgraded at the same time without interfering with each other, as they will
  derive the same MAC key.
- The MAC is calculated after encryption, and hence is verified before
  decryption, so we know that it is authenticated before we do any processing
  on it.

A disadvantage of the currently-proposed method versus the previous proposal is
that migration requires that the user gives the client access to the backup
decryption key in order to derive the MAC key.  However, in both proposals,
most clients would require that the user enter their default SSSS key, which
would give them access to the decryption key anyways.

## Security considerations

Being able to prove authenticity of keys may affect the deniability of
messages: if a user has a Megolm session in their key backup that is MAC'ed by
their backup MAC key, and the session data indicates that it originated from
one of their devices, this could be used as evidence that the Megolm session
did in fact come from them.

This is somewhat mitigated by the fact that obtaining the Megolm session
requires the decryption key for the backup.  In addition, the deniability
property mainly refers to the fact that a recipient cannot prove the
authenticity of the message to a third party, and usually is not concerned with
preventing self-incrimination.  And in fact, a confiscated device may already
have enough information to sufficiently prove that the device's owner sent a
message.

## Unstable prefix

Until this MSC is accepted, the following unstable names should be used:

- the property name `org.matrix.msc4048.authenticated` should be used in place
  of `authenticated` in the `SessionData` object,
- the property name `org.matrix.msc4048.mac2` should be used in place of `mac2`
  in the `session_data` property,
- the SSSS identifier `org.matrix.msc4048.mac` should be used in place of
  `m.megolm_backup.v1.mac`.

## Dependencies

None
