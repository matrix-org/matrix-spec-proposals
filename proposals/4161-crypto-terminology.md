# MSC4161: Crypto terminology for non-technical users

## Background

Matrix makes use of advanced cryptographic techniques to provide secure
messaging. These techniques often involve precise and detailed language that is
unfamiliar to non-technical users.

This document provides a list of concepts and explanations that are intended to
be suitable for use in Matrix clients that are aimed at non-technical users.

Ideally, encryption in Matrix should be entirely invisible to end-users (much as
WhatsApp or Signal users are not exposed to encryption specifics). This
initiative is referred to as "Invisible Cryptography" and is tracked as:

* [MSC4153](https://github.com/matrix-org/matrix-spec-proposals/pull/4153) -
  Exclude non-cross-signed devices,
* [MSC4048](https://github.com/matrix-org/matrix-spec-proposals/pull/4048) -
  Authenticated key backup,
* [MSC4147](https://github.com/matrix-org/matrix-spec-proposals/pull/4147) -
  Including device keys with Olm-encrypted events, and
* MSC4161 - this document

## Goals

We hope that Matrix client developers will like the terms and wording we
provide, and adapt their user interfaces and documentation to use them. (If this
MSC is accepted, Element will use it as a reference for English wording in its
clients.)

Where concepts and terms exactly match existing terms in the Matrix spec, we
propose changing the spec to use the terms from this document. Where they do not
match, we are very comfortable with different words being used in the spec,
given it is a highly technical document, as opposed to a client user interface.

We hope that this MSC will:

* Cause small changes in the spec (as described in the previous paragraph), and
* Become an appendix in the spec, with a description that makes clear that the
  intended audience is different from most of the spec, meaning different words
  are used from the main spec body.

Clients may, of course, choose to use different language. Some clients may
deliberately choose to use more technical language, to suit the profiles of
their users. This document is aimed at clients targeting non-technical users.

Where changes are made in the spec, we suggest that notes be added mentioning
the old name, as in [this
example](https://github.com/matrix-org/matrix-spec/pull/1819/files#diff-8b25d378e077f18eb06ebdb9c376e194c8a4c8b95cf909fca6448659a627f283R1326).

## Proposal

When communicating about cryptography with non-technical users, we propose using
the following terms and concepts.

### Devices

Instances of a client are called 'devices' (not 'sessions'). Aligned with
[MSC4153](https://github.com/matrix-org/matrix-spec-proposals/pull/4153), we take it as granted that all devices have been cross-signed by the
user who owns them, and we call these **devices**.

Devices which have not been cross-signed by the user are considered an error
state, primarily to be encountered during the transition to MSC4153 and/or due
to buggy/incomplete/outdated clients. These devices are referred to as **not
secure** and presence of them are considered a serious and dangerous error
condition, similar to an invalid TLS certificate.

> "This device is not secure. Please verify it to continue."

> "Ignoring 5 messages that were sent from a device that is not secure."

> "Confirm it's you" (when asking to verify a device during login)

⚠️ Avoid saying "secure device". All devices are considered secure by default;
the user doesn't typically need to worry about the fact that insecure devices
are a thing, given they should only ever occur in error (or transitional)
scenarios.

⚠️ Avoid saying "trusted device" or "verified device". Devices are not people,
and it is helpful to use different language for people vs. devices. (However, we
do use the verb "verify" to describe how to make a device secure. By using the
same verb, we help users understand the confusing fact that verifying devices
and verifying people are similar processes, but with different outcomes.)

⚠️ Avoid using "cross-signing", which requires a deeper understanding of
cryptography to understand.

⚠️ Avoid mentioning "device keys" - a device is just secure or not.

⚠️ Avoid "session" to mean device. Device better describes what most people
encounter, and is more commonly used in other products.

### Verified person

When you verify a person they become **verified**. This means that you have
cryptographic proof that no-one is listening in on your conversations. (You need
this if you suspect someone in a room may be using a malicious homeserver.)

In many contexts, most people are **not verified**: verification is a manual
step (scanning a QR code or comparing emojis). (In future, verification will
probably become more common thanks to "transitive trust" or "key transparency").
When an unverified person resets their cryptographic identity, we should warn
the user, so they are aware of the change.

If Alice is verified with Bob, and then Alice's cryptographic identity changes
(i.e. Alice resets their master cross-signing key) then this is very important to
Bob: Bob verified Alice because they care about proof that no-one is listening,
and now someone could be. Bob can choose to **withdraw verification** (i.e.
"demote" Alice from being verified), or **re-verify** with Alice. Until Bob does
one or the other, Bob's communication with Alice should contain a prominent and
serious warning that Alice's **verified identity has changed**.

> "This person is verified."

> "WARNING: Bob's verified identity has changed!"

> "You verified this person's identity, but it has changed. Please choose to
> re-verify them or withdraw verification."

⚠️ Avoid using "cross-signing", which requires a deeper understanding of
cryptography to understand.

⚠️ Avoid using "trust on first use (TOFU)", which is a colloquial name for noting
the identity of people who are not verified so that we can notify the user if it
changes. (This is a kind of "light" form of verification where we assume that
the first identity we can see is trusted.)

⚠️ Avoid confusing verification of people with verification of devices: the
mechanism is similar but the purpose is different. Devices must be verified to
make them secure, but people can optionally be verified to ensure no-one is
listening in or tampering with communications.

⚠️ Avoid talking about "mismatch" or "verification mismatch" which is very
jargony - it is the identity which is mismatched, not the verification process.
Just say "Bob's verified identity has changed".

⚠️ Avoid talking about "cryptographic identity" which is very jargony. Just call
it "identity" where possible - i.e. the non-technical dictionary definition of
identity such that someone is who they claim they are, not someone else. The
fact we confirm identity cryptographically is irrelevant to the user;
cryptography should be invisible.

### Identity

A person's **identity** is proof of who they are, and, if they are verified,
proof that you have a secure communication channel with them.

> "Warning: Alice's identity appears to have changed" (when a non-verified
> person resets their recovery key)

> "WARNING: Bob's verified identity has changed!" (when a verified person resets
> their recovery key)

(During login, at the "Confirm it's you" stage):

> "If you don't have any other device and you have lost your recovery key, you
> can create a new identity. (Warning: you will lose access to your old
> messages!)" button text (in red or similar): "Reset my identity"

⚠️ Avoid saying "master key" - this is an implementation detail.

⚠️ Avoid saying "reset their encryption" - the reason that Alice's identity
changed could be due to attack rather than because they reset their encryption
(plus "encryption" is jargony).

### Message key

A **message key** is used to decrypt a message. The metaphor is that messages
are "locked in a box" by encrypting them, and "unlocked" by decrypting them.

> "Store message keys on the server."

> "This message could not be decrypted because its key is missing."

⚠️ Avoid saying "key" without a previous word saying what type of key it is.

⚠️ Avoid using "room key". These keys are used to decrypt messages, not rooms.

Note: this clashes with the term "message key" in the double ratchet. Since the
double ratchet algorithm is for a very different audience, we think that this is
not a problem.

### Unable to decrypt

When we have an encrypted message but no message key to decrypt it, we are
unable to decrypt it.

When we expect the key to arrive, we are **waiting for this message**.

> "Waiting for this message" button: "learn more" which explains that the key to
> decrypt this message has not yet been received, but that we expect it to
> arrive shortly. Further detail may be provided, for instance explaining that
> connectivity issues between the sender's homeserver and our own can cause
> key delivery delays.

When the user does not have the message key for a permanent and well-understood
reason, for example if it was sent before they joined the room, we say **you
don't have access to this message**.

> "You don't have access to this message" e.g. if it was sent before the user
> entered the room, or the user does not have key storage set up.

### Message history

Your **message history** is a record of every message you have received or sent,
and is particularly used to describe messages that are stored on the server
rather than your device(s)

### Key storage

**Key storage** means keeping cryptographic information on the server. This
includes the user's cryptographic identity, and/or the message keys needed to
decrypt messages.

If a user loses their recovery key, they may **reset** their key storage. Unless
they have old devices, they will not be able to access old encrypted messages
because the message keys are stored in key storage, and their cryptographic
identity will change, because it too is stored in key storage.

> "Allow key storage"

> "Key storage holds your cryptographic identity on the server along with the
> keys that allow you to read your message history."

> "Message history is unavailable because key storage is disabled."

⚠️ Avoid distinguishing between "secret storage" and "key backup" - these are
both part of key storage.

⚠️ Avoid talking about more keys: "the backup key is stored in the secret
storage, and this allows us to decrypt the messages keys from key backup".
Instead, we simply say that both cryptographic identity and message keys are
stored in key storage.

⚠️ Avoid using "key backup" to talk about storing message keys: keeping things on
the server is not a "backup", but a reliable, cross-device place where this
information is stored. The word "backup" implies a redundant way to recover lost
information, but if the user loses their recovery key, this information is lost.
Clients and servers may wish to offer additional backup services that provide
true redundancy and disaster recovery, but key storage is not this.

⚠️ Avoid "4S" or "quad-S" - these are not descriptive terms.

⚠️ Avoid "private key" - this is an implementation detail and a term with
specific meaning from cryptography.

### Recovery key (and recovery passphrase)

A **recovery key** is a way of regaining access to key storage if the user loses
all their devices. Using key storage, they can preserve their cryptographic
identity (meaning other people don't see "Alice's identity appears to have
changed" messages), and also read old messages using the stored message keys.

A **recovery passphrase** is an easier-to-remember way of accessing the recovery
key and has the same purpose as the recovery key.

> "Write down your recovery key in a safe place"

> "If you lose access to your devices and your recovery key, you will need to
> reset your key storage, which will create a new identity"

> "If you lose your recovery key you can generate a new one if you are signed in
> elsewhere"

⚠️ Avoid using "security key", "security code", "recovery code", "master key". A
recovery key allows "unlocking" the key storage, which is a "box" that is on the
server, containing your cryptographic identity and message keys. It is used to
recover the situation if you lose access to your devices. None of these other
terms express this concept so clearly.

⚠️ Remember that users may have historically been trained to refer to these
concepts as "security key" or "security passphrase", and so user interfaces
should provide a way for users to be educated on the terminology change (e.g. a
tooltip or help link): e.g. "Your recovery key may also have been referred to as
a security key in the past"

⚠️ Be aware that at time of writing the spec uses
["recovery key"](https://spec.matrix.org/v1.8/client-server-api/#recovery-key)
to refer to the private half of the backup encryption key, which is different
from the usage here. The recovery key described in this section is referred to
in the spec as the
[secret storage key](https://spec.matrix.org/v1.8/client-server-api/#secret-storage).

## Potential issues

Lots of existing clients use a whole variety of different terminology, and many
users are familiar with different terms. Nevertheless we believe that working
together to agree on a common language is the only way to address this issue
over time.

## Further work

Several other concepts might benefit from similar treatment. Within
cryptography, "device dehydration" is a prime candidate. Outside cryptography,
many other terms could be agreed, including "export chat" (particularly in
contrast to "export message keys").

## Security considerations

In order for good security practices to work, users need to understand the
implications of their actions, so this MSC should be reviewed by security
experts to ensure it is not misleading.

## Dependencies

None

## Credits

Written by Andy Balaam, Aaron Thornburgh and Patrick Maier as part of our work
for Element. Richard van der Hoff, Matthew Hodgson and Denis Kasak contributed
many improvements before the first draft was published.
