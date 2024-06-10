# MSCxxxx: Invisible Cryptography

End-to-end encryption was first introduced to Matrix in 2016. Over the years,
more encryption-related features have been added, such as key verification,
cross-signing, key backup, and secure storage/sharing.

The current spec allows clients freedom to choose what features to implement.
And while clients should be able to make decisions based on their threat model,
there are behaviours that the spec can recommend that will improve the user
experience and security of encrypted conversations.

In general, this MSC proposes to standardize on using cross-signing as a basis
for trusting devices.  While a user may be unable to verify every other user
that they communicate with, or may be unaware of the need to verify other
users, cross-signing gives some measure of protection and so should be used
where possible.  One of the goals of this MSC is to reduce the number of
warnings that users will encounter by taking advantage of cross-signing.

## Proposal

The changes below only apply to clients that support encryption.

### Users should have cross-signing keys

Clients should create new cross-signing keys for users who do not yet have
cross-signing keys.

Users should have Secret Storage with a default key that encrypts the private
cross-signing keys and key backup key (if available)

The spec currently does not give recommendations for what information is stored
in Secret Storage, or even whether Secret Storage is available to users.  A
user’s Secret Storage should contain the user’s cross-signing secret keys and
the key backup decryption key (if the user is using key backup).  This ensures
that users have a more consistent experience.

### Verifying individual devices of other users is deprecated

When one user verifies a different user, the verification should verify the
users’ cross-signing keys.  Any flow that verifies only the device keys of
different users is deprecated.  Verifying a user’s own device keys is still
supported.

### Devices should be cross-signed

Clients should encourage users to cross-sign their devices.  This includes both
when logging in a new device, and for existing devices.  Clients may even go so
far as to require cross-signing of devices by preventing the user from using
the client until the device is cross-signed.  If the user cannot cross-sign
their device (for example, if they have forgotten their Secret Storage key),
the client can allow users to reset their Secret Storage, cross-signing, and
key backup.

### Clients should flag when cross-signing keys change

If Alice’s cross-signing keys change, Alice’s own devices must alert her to
this fact, and prompt her to re-cross-sign those devices.  If Bob is in an
encrypted room with Alice, Bob’s devices should inform him of Alice’s key
change and should prevent him from sending an encrypted message to Alice
without acknowledging the change.

Bob’s clients may behave differently depending on whether Bob had previously
verified Alice or not.  For example, if Bob had previously verified Alice, and
Alice’s keys change, Bob’s client may require Bob to re-verify, or may display
a more aggressive warning.

Note that this MSC does not propose a mechanism for remembering previous
cross-signing keys between devices. In other words if Alice changes her
cross-signing keys and then Bob logs in a new device, Bob’s new device will not
know that Alice’s cross-signing keys had changed, even if Bob has other devices
that were previously logged in. Such a mechanism could be proposed by another
MSC.

### Room keys should by default not be sent to non-cross-signed devices

Since non-cross-signed devices don’t provide any assurance that the device
belongs to the user, and server admins can trivially create new devices for
users, clients should not send room keys to non-cross-signed devices by
default. Clients may provide users the ability to encrypt to specific
non-cross-signed devices, for example, for development or testing purposes.

### Messages from non-cross-signed devices should be untrusted

Similarly, clients have no assurance that encrypted messages sent from
non-cross-signed devices were sent by the user, rather than an
impersonator. Therefore messages sent from non-cross-signed devices cannot be
trusted and should be displayed differently to the user. For example, the
message could be displayed with a warning, or may be hidden completely from the
user. Again, clients may be allow the user to override this behaviour for
specific devices for development or testing purposes.

## Potential Issues

If a user has devices that are not cross-signed, they will not be able to
communicate with other users whose clients implement this proposal completely,
due to the last two points.  Thus we encourage clients to implement
cross-signing as soon as possible, and to encourage users to cross-sign their
devices, and clients should delay the implementation of the last two points (or
make it optional) until most clients have implemented cross-signing.

TODO: status of cross-signing in clients

## Alternatives

## Security considerations

## Unstable prefix

No new names are introduced, so no unstable prefix is needed.

## Dependencies

Though not strictly dependencies, other MSCs improve the behaviour of this MSC:
- [authenticated backups
  (MSC4048)](https://github.com/matrix-org/matrix-spec-proposals/pull/4048)
  will improve the user experience by ensuring that trust information is
  preserved when loading room keys from backup.  TODO: I think we also need to
  add information to the backup about the cross-signing status of the device
- [Including device keys with Olm-encrypted events
  (MSC4147)](https://github.com/matrix-org/matrix-spec-proposals/pull/4147)
  allows recipients to check the cross-signing status of devices that have been
  deleted
