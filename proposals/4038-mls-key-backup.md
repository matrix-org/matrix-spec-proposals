# MSC4038: Key backup for MLS

[MSC2883](https://github.com/matrix-org/matrix-spec-proposals/pull/2883)
defines how to use [Messaging Layer Security
(MLS)](https://messaginglayersecurity.rocks/) with [decentralisation
extensions](https://gitlab.matrix.org/matrix-org/mls-ts/-/blob/decentralised2/decentralised.org)
for end-to-end encryption in Matrix.

This MSC describes how to use MLS with Matrix's [server-side key
backups](https://spec.matrix.org/unstable/client-server-api/#server-side-key-backups)
so that users can read old messages after logging in to a new device.

We only need to decrypt application messages and not handshake messages.  That
is, we only need to decrypt MLS messages that encrypt Matrix events, and not
MLS messages that manage the MLS group.

## Proposal

A new backup algorithm is added, `m.dmls_backup.v1.aes-hmac-sha2`, to store MLS
group information.   The existing key backup API stores data indexed by room ID
and by session ID.  However MLS does not have a session ID.  Instead, MLS, with
the decentralisation extensions, has epochs (which can be represented by a
number) and epoch creators.  We thus encode the epoch and epoch creator
together to use as the session ID.

TODO: The current implementation use `<epoch num>|<epoch creator>`, where
`<epoch num>` is a decimal number, and `<epoch creator>` is unpadded base64 of
`<user ID>|<device ID>` as the encoding.  We should do something better.

The `first_message_index` parameter in the key backup data has no meaning in
MLS, but the key backup API requires it; this parameter is set to 0.

The session data, prior to encryption, is a JSON object with the following
properties:

- `algorithm`: the string `m.dmls.v1.<ciphersuite>` where `<ciphersuite>` is
  the string identifying the ciphersuite used for MLS
- `room_id`: the Matrix room ID
- `epoch`: an array of the form ... TODO
- `group_export`: an unpadded base64 encoding of the MLS group export as
  defined below

The session data is encrypted as described in
[MSC3270](https://github.com/matrix-org/matrix-spec-proposals/pull/3270), and
the `auth_data` is the same as described in the same MSC.

### Group export

The MLS group data is exported using [TLS presentation
language](https://www.rfc-editor.org/rfc/rfc8446#section-3), using the
definitions from MLS:

```c
struct {
    ProtocolVersion version = mls10;
    CipherSuite ciphersuite;
    GroupContext context;
    opaque sender_data_secret<V>;
    opaque membership_key<V>;
    opaque confirmation_key<V>;
    opaque encryption_secret<V>;
    opaque interim_transcript_hash<V>;
    opaque epoch_authenticator<V>;
    KeyPackage key_packages<V>; // or KeyPackageRef?
    opaque authenticated_data<V>;
} group_export;
```

TODO: determine how to handle key_packages, and RatchetTree extension if the
group supports that.  Both can produce a lot of data in big groups, but there
can be a lot of duplication between backups, so we may be able to reduce total
storage.

## Potential issues

The current key backup API only allows writing to one backup version, so a user
cannot back up both Megolm and MLS keys.  Possible solutions are:

- change the backup API to allow one backup version per algorithm
- put MLS keys in the `m.megolm_backup.*` backup.  Clients that do not support
  MLS should ignore the MLS data since the keys do not fit the expected format,
  and do not have the expected `algorithm` in the session data.
- store the MLS backup somewhere else.  Part of the reason for having a
  special API was so that the server could compare backed-up keys based on
  cleartext data (e.g. first message index), and keep the "best" version.  This
  is not as necessary with MLS, and the group exports could be stored in a
  simple key-value storage, such as per-room account data.  However, the
  account data system would not be suitable as it currently is, since storing
  the keys in there would bloat `/sync` responses (in particular, the initial
  sync).  So this would require a change to account data to allow marking some
  data so that it is not included in the `/sync`.

## Security considerations

For forward secrecy reasons, MLS disallows storing some of the information that
is included in the group export.  This proposal conflicts with that
requirement, with the justification that users expect to be able to read old
messages, even on newly logged-in clients.  The only way to be able to read old
encrypted messages is to store the decryption keys or to store the plaintext.
Key backup is an optional feature, so users can choose how they wish to balance
privacy or convenience.

## Unstable prefix

Until this MSC is accepted, clients should use
`org.matrix.msc4038.v0.aes-hmac-sha2` as the backup version.  Note that the
session data contains an `algorithm` property giving the encryption algorithm
for the key.  Until MSC2883 is accepted, the unstable identifier from that MSC
should be used as the algorithm name, rather than the stable identifier.

## Dependencies

This MSC builds on
[MSC2833](https://github.com/matrix-org/matrix-spec-proposals/pull/2883) (which
at the time of writing has not yet been accepted into the spec).
