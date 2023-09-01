# MSC4048: Signed key backup

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
but to ensure authenticity by signing the backup data.

## Proposal

A user has a new signing key, referred to as the "backup signing key", used to
sign key backups using the ed25519 signature algorithm.  The private key can be
shared/stored using [the Secrets
module](https://spec.matrix.org/unstable/client-server-api/#secrets) using the
name `m.key_backup.signing`.

The `AuthData` object for the [`m.megolm_backup.v1.curve25519-aes-sha2` key
backup
algorithm](https://spec.matrix.org/unstable/client-server-api/#backup-algorithm-mmegolm_backupv1curve25519-aes-sha2)
has a new optional property called `signing_public_key`, contains the public
key of the backup signing key, encoded in unpadded base64.  If the `AuthData`
is not signed by the user's master signing key or by a verified device
belonging to the same user, the backup signing key must be ignored, and all
keys in the backup must be treated as being unsigned.

The `SessionData` object for the `m.megolm_backup.v1.curve25519-aes-sha2` key
backup algorithm has two new optional properties:

- a `signatures` property: the `SessionData` is a [signed JSON
  object](https://spec.matrix.org/unstable/appendices/#signing-json), signed
  using the backup signing key, using the public key (encoded in unpadded
  base64) as the key ID
- a boolean `authenticated` property, defaulting to `false`: indicates whether
  the device that uploaded the key to the backup believes that the key belongs
  to the given `sender_key`.  This is true if: a) the key was received via an
  Olm-encrypted `m.room_key` event from the `sender_key`, b) the key was
  received via a trusted key forward
  ([MSC3879](https://github.com/matrix-org/matrix-spec-proposals/pull/3879)),
  or c) the key was downloaded from the key backup, with the `authenticated`
  property set to `true` and signed by a trusted key.  If the `SessionData` is
  not signed by the backup signing key, then this flag must be treated as being
  `false`.

The `mac` property in the cleartext `session_data` property of the
`KeyBackupData` is deprecated.  Clients should continue to produce it for
compatibility with older clients, but should no longer use it to verify the
contents of the backup if the `SessionData` object is signed.

## Potential issues

As the `AuthData` is changed, a new backup version will need to be created.  A
client will need to download all existing keys and re-upload them.

In order to store a new secret in the Secret Storage, clients may need to
prompt the user for the Secret Storage key.  Clients may need to do so already
to download all the current keys from the backup.

## Alternatives

As mentioned above, we could switch to using a symmetric encryption algorithm
for the key backup.  However, this is not backwards-compatible, and does not
allow for clients that can write to the backup without reading.

Rather than using a new signing key, we could use an existing signing key, such
as one of the cross-signing keys.  This would remove the need for users to
enter their Secret Storage key to add the new signing key.  However, this means
that a user cannot create a key backup without also using cross-signing.  Using
a separate key also allows the user to give someone else (such as a bot)
permission to write to their backups without allowing them to perform any
cross-signing operations.

## Security considerations

Being able to prove authenticity of keys may affect the deniability of
messages: if a user has a Megolm session in their key backup that is signed by their
backup signing key, and the session data indicates that it originated from one
of their devices, this could be used as evidence that the Megolm session did in
fact come from them.

This is somewhat mitigated by the fact that obtaining the Megolm session
requires the decryption key for the backup.  In addition, the deniability
property mainly refers to the fact that a recipient cannot prove the
authenticity of the message to a third party, and usually is not concerned with
preventing self-incrimination.  And in fact, a confiscated device may already
have enough information to sufficiently prove that the device's owner sent a
message.

## Unstable prefix

Until this MSC is accepted, the property name
`org.matrix.msc4048.signing_public_key` should be used in place of
`signing_public_key`, and `org.matrix.msc4048.authenticated` should be used in
place of `authenticated`.  No unstable prefix is used for the `signatures`
property since it uses the existing definition of JSON signing.

## Dependencies

None
