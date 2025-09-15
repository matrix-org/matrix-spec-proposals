# MSC4153: Exclude non-cross-signed devices

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

Note: The changes below only apply to clients that support encryption.

### Users SHOULD have cross-signing keys

Clients SHOULD create new cross-signing keys for users who do not yet have
cross-signing keys.

### Users SHOULD have Secret Storage

The spec currently does not give recommendations for what information is stored
in Secret Storage, or even whether Secret Storage is available to users.  Secret
Storage allows users to keep secrets on the server so that they are accessible
when the user logs in to a new device and does not have an existing device that
can share the secrets with the new device.  Therefore users SHOULD have Secret
storage set up.

The user’s Secret Storage SHOULD contain the user’s cross-signing secret keys
and the key backup decryption key (if the user is using key backup).  This
ensures that users use cross-signing and key backup on new devices.

The user's Secret Storage SHOULD have a default key (a key referred to by
`m.secret_storage.default_key`) that encrypts the private cross-signing keys and
key backup key (if available).

### Verifying individual devices of other users is deprecated

When one user verifies a different user, the verification SHOULD verify the
users’ cross-signing keys.  Any flow between different users that does not
verify the users' cross-signing keys (it verifies only the device keys) is
deprecated.  Verifying a user’s own device keys is still supported.

### Devices SHOULD be cross-signed

Clients SHOULD encourage users to cross-sign their devices.  This includes both
when logging in a new device, and for existing devices.  Clients may even go so
far as to require cross-signing of devices by preventing the user from using
the client until the device is cross-signed.  If the user cannot cross-sign
their device (for example, if they have forgotten their Secret Storage key),
the client can allow users to reset their Secret Storage, cross-signing, and
key backup.

### Clients SHOULD flag when cross-signing keys change

If Alice’s cross-signing keys change, Alice’s own devices MUST alert her to
this fact, and prompt her to re-cross-sign those devices.  If Bob is in an
encrypted room with Alice, Bob’s devices SHOULD inform him of Alice’s key
change and SHOULD prevent him from sending an encrypted message to Alice
without acknowledging the change.

Bob’s clients may behave differently depending on whether Bob had previously
verified Alice or not.  For example, if Bob had previously verified Alice, and
Alice’s keys change, Bob’s client may require Bob to re-verify, or may display
a more aggressive warning.

Note that this MSC does not propose a mechanism for remembering previous
cross-signing keys between devices. In other words if Alice changes her
cross-signing keys and then Bob logs in a new device, Bob’s new device will not
know that Alice’s cross-signing keys had changed, even if Bob has other devices
that were previously logged in.  This may result in Bob never seeing a warning
about Alice's identity change, for example if Bob logs out of his last device,
then Alice changes her cross-signing keys, and then Bob logs into a new device.

In addition, this MSC does not propose a mechanism for synchronising between
devices information regarding what warnings the user has seen or acknowledged.
That is, if Alice changes her cross-signing keys and Bob has multiple devices
logged in, then Bob will see a warning on all his devices, and will have to
dismiss the warning on all of his devices.

A mechanism for synchronising information between devices could be proposed by
another MSC.

### Encrypted to-device messages MUST NOT be sent to non-cross-signed devices

Since non-cross-signed devices don’t provide any assurance that the device
belongs to the user, and server admins can trivially create new devices for
users, clients MUST not send encrypted to-device messages, such as room keys or
secrets (via Secret Sharing), to non-cross-signed devices by default.  When
sending room keys, clients can use a [`m.room_key.withheld`
message](https://spec.matrix.org/unstable/client-server-api/#reporting-that-decryption-keys-are-withheld)
with a code of `m.unverified` to indicate to the non-cross-signed device why it
is not receiving the room key.

An allowed exception to this rule is that clients may provide users the ability
to encrypt to specific non-cross-signed devices for development or testing
purposes.

A future MSC may specify exceptions to this rule.  For example, if a future MSC
defines a device verification method that uses encrypted to-device messages,
such messages would need to be sent to a user's own non-cross-signed devices, so
that the user can verify their device to cross-sign it.

### Encrypted messages from non-cross-signed devices SHOULD be ignored

Similarly, clients have no assurance that encrypted messages sent from
non-cross-signed devices were sent by the user, rather than an
impersonator. Therefore messages sent from non-cross-signed devices cannot be
trusted and SHOULD NOT be displayed to the user.

Again, an allowed exception to this is that clients may allow the user to
override this behaviour for specific devices for development or testing
purposes.

### Non-cryptographic devices SHOULD NOT impact E2EE behaviour

For the sake of clarity: non-cryptographic devices (devices which do not have
device identity keys uploaded to the homeserver) should not have any impact on
a client's E2EE behaviour. For all intents and purposes, non-cryptographic
devices are a completely separate concept and do not exist from the perspective
of the cryptography layer since they do not have identity keys, so it is
impossible to send them encrypted messages.

In particular, Matrix clients MUST NOT consider non-cryptographic devices to be
equivalent to non-cross-signed cryptographic devices for purposes of enforcing
E2EE policy. For example, clients SHOULD NOT warn nor refuse to send messages
due to the presence of non-cryptographic devices.

The intent of this is to smoothly support and minimise interference from
applications which choose to set up E2EE only on demand (e.g.
[WorkAdventure](https://workadventu.re/article-en/managing-e2e-encryption-with-matrix-in-a-simple-way/).
Such clients should initially create a non-cryptographic device until they are
ready to set up E2EE. Only when they are ready will they create the device
identity keys for the device and upload them to the homeserver, converting the
device into a cryptographic device and making it subject to the rules given in
this MSC.

### Clients MAY make provisions for encrypted bridges

Some bridges are structured in a way such that only one user controlled by the
bridge (often called the bridge bot) participates in encryption, and encrypted
messages from other bridge users are encrypted by the bridge bot.  Thus
encrypted messages sent by one user could be encrypted by a Megolm session sent
by a different user.  Clients MAY accept such messages, provided the bridge
bot's device is cross-signed. However, the client MUST annotate the message with
a warning, unless the client has a way to check that the bridge bot is permitted
to encrypt messages on behalf of the user.

[MSC4350](https://github.com/matrix-org/matrix-spec-proposals/pull/4350)
presents a way for bridge users to indicate that the bridge bot is allowed to
perform encryption on their behalf.

## Potential Issues

### Client support

If a user has devices that are not cross-signed, they will not be able to
communicate with other users whose clients implement this proposal completely,
due to the last two points.  Thus we encourage clients to implement
cross-signing as soon as possible, and to encourage users to cross-sign their
devices, and clients should delay the implementation of the last two points (or
make it optional) until most clients have implemented cross-signing.

The following clients support cross-signing:

- Cinny
- Element (all platforms), and derivatives such as Schildi Chat
- Fractal
- gomuks
- NeoChat
- Nheko
- pantalaimon
- Tammy
- Trixnity Messenger

The following encryption-capable clients do not support cross-signing:

- kazv

### Bots and application services

This is a special case to the issue above, but seems to be a large enough class
that it deserves its own mention: support for cross-signing in bots and
application services may be less common than in interactive clients.  When a
client fully implements this proposal, users will be unable to interact with
bots and application services in encrypted rooms if they do not support
cross-signing.

Some possible solutions for bots are:

- if a bot is the only device logged into a given account, the bot can create its
  own cross-signing keys and cross-sign its device.
- the bot administrator can provide the Secret Storage key to the bot so that
  the bot can fetch its self-signing private key and cross-sign its device.
- the bot can log its device keys so that the administrator can cross-sign it
  from a different device by manually comparing the device keys.  Note that many
  clients do not have the ability to verify by comparing device keys.

The following bots support cross-signing:

- [meowlnir](https://github.com/maunium/meowlnir)
- [Arnie](https://gitlab.com/andybalaam/arnie)
- [maubot](https://github.com/maubot/maubot)

The following bot SDKs support, or plan to support, cross-signing such that any
bots written using them will support cross-signing:

- [mautrix-go](https://github.com/mautrix/go) (planned support for Application Services)

## Alternatives

We could do nothing and leave things as they are, but the rules given in this
MSC provide improved security.

## Security considerations

Warning the user about cross-signing key changes can be circumvented by a
malicious server if it sends forged cross-signing keys the first time the user
sees them.  Therefore users should still verify other users when security is
important.

## Unstable prefix

No new names are introduced, so no unstable prefix is needed.

## Dependencies

Though not strictly dependencies, other MSCs improve the behaviour of this MSC:
- [Authenticated backups
  (MSC4048)](https://github.com/matrix-org/matrix-spec-proposals/pull/4048)
  will improve the user experience by ensuring that trust information is
  preserved when loading room keys from backup.  We may also need to add
  information to the backup about the cross-signing status of the device,
  but this can be addressed in a future MSC.
- [Including device keys with Olm-encrypted events
  (MSC4147)](https://github.com/matrix-org/matrix-spec-proposals/pull/4147)
  allows recipients to check the cross-signing status of devices that have been
  deleted.
- [Permitting encryption impersonation for appservices
  (MSC4350)](https://github.com/matrix-org/matrix-spec-proposals/pull/4350)
  allows a user to assert that a bridge is allowed to encrypt for them.
