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

## Why is this important?

Use of common terminology should help further these goals:

* **to reduce confusion**: many members of the community are confused by the
  crypto features in Matrix clients, and the profusion of different words for
  the same thing makes it much worse. By reducing the *number* of words, and
  carefully choosing *good* words, we hope to develop a common language which
  makes Matrix easier to understand, and easier to explain.

* **to ease migration**: one of the key features of Matrix for end-users is the
  choice of clients, meaning no-one is locked in to a particular piece of
  software. If each client uses conflicting terminology, it becomes much more
  difficult to move to a different client, which works against the user's
  ability to migrate.

This proposal uses "SHOULD" language rather than "MUST", because there are many
good reasons why a particular client might choose different wording. In
particular, different clients may have very different audiences who communicate
in different ways and understand different metaphors. This proposal hopes to
nudge client developers towards consistency, but never at the cost of their
unique relationship with their users.

## Outcomes

We hope that Matrix client developers will like the terms and wording we
provide, and adapt their user interfaces and documentation to use them.
Element is using this MSC as its reference so will serve as an implementation
in terms of FCP approval.

The Matrix spec SHOULD additionally be updated to use the concepts
and terms from this proposal, where possible. For example, textual
descriptions of features should use the terms here, but the API 
endpoints and event types should *not* be updated. 

We hope that this MSC will:

* Cause small changes in the spec (as described in the previous paragraph), and
* Become part of the spec, with a description that makes clear that the
  contents are for UX/UI consideration rather than code.

Clients may, of course, choose to use different language. Some clients may
deliberately choose to use more technical language, to suit the profiles of
their users. This document is aimed at clients targeting non-technical users.

Where changes are made in the spec, we suggest that notes be added mentioning
the old name, as in [this
example](https://github.com/matrix-org/matrix-spec/pull/1819/files#diff-8b25d378e077f18eb06ebdb9c376e194c8a4c8b95cf909fca6448659a627f283R1326).

## Proposal

When communicating about cryptography with non-technical users, the following
terms and concepts SHOULD be used.

When referring to concepts outlined in this document in their user interface,
clients SHOULD use the language specified in **bold**, except where their own users are
known to understand different terms more easily. When making such exceptions,
clients SHOULD document how they deviate from this document, and why.

### Devices (Sessions)

Instances of a client are called **devices** or alternatively **sessions**.
Devices that have not been cross-signed by the user who owns them are
**unconfirmed**. It is important that devices are confirmed, to prevent
security problems like a compromised server creating fake devices that
can impersonate users (see
[MSC4153](https://github.com/matrix-org/matrix-spec-proposals/pull/4153)).

> "This device is not confirmed. Please confirm it to continue."

> "Confirm it's you" (when asking to confirm a device during login)

⚠️ Avoid using "cross-signing", which requires a deeper knowledge of
cryptography to understand.

⚠️ Avoid mentioning "device keys". While a device may have keys, the user
is only concerned about whether it is secure or not.

#### Logging out

In contrast to some other services, **logging out** (or **signing out**) of a
Matrix device is quite a significant operation: it means your encryption data on
the device is lost, and if you log out of all devices you will need to use your
recovery key to re-establish your identity and regain access to your old
messages.

If using a trusted physical device, the right choice for a user may well be not
to log out, but simply to close the app or browser and re-open it later. This
preserves their identity and their access to message history.

> "Are you sure you want to log out?"

> "If you log out of all devices, you will lose access to message history and
> will need to reset your identity."

### Verified user

When you verify a user they become **verified**. This means that you have
cryptographic proof that no-one is listening in on your conversations. (You need
this if you suspect someone in a room may be using a malicious homeserver.)

In many contexts, most users are **not verified**: verification is a manual
step ([scanning a QR code](https://spec.matrix.org/v1.12/client-server-api/#qr-codes) or [comparing emojis](https://spec.matrix.org/v1.12/client-server-api/#sas-method-emoji)). (In future, verification will
probably become more common thanks to [MSC2882 Transitive Trust](https://github.com/matrix-org/matrix-spec-proposals/pull/2882) or something similar).
When an unverified contact resets their identity, the user should be warned that
this happened.

If Alice is verified with Bob, and then Alice's identity changes
(i.e. Alice resets their master cross-signing key) then this is very important to
Bob: Bob verified Alice because they care about proof that no-one is listening,
and now someone could be. Bob can choose to **withdraw verification** (i.e.
"demote" Alice from being verified), or **re-verify** with Alice. Until Bob does
one or the other, Bob's communication with Alice should contain a prominent and
serious warning that Alice's **identity has been reset**.

> "This user is verified."

> "WARNING: Bob's identity has been reset!"

> "You verified this user's identity, but it has been reset. Please choose to
> re-verify them or withdraw verification."

⚠️ Avoid using "cross-signing", which requires a deeper understanding of
cryptography to understand.

⚠️ Avoid using "trust on first use (TOFU)", which is a colloquial name for noting
the identity of users who are not verified so that we can notify the user if it
changes. (This is a kind of "light" form of verification where we assume that
the first identity we can see is trusted.)

⚠️ Avoid confusing verification of users with confirmation of devices: the
mechanism is similar but the purpose is different. Devices must be confirmed to
make them secure, but users can optionally be verified to ensure no-one is
listening in or tampering with communications.

⚠️ Avoid talking about "mismatch" or "verification mismatch" which is very
jargony - it is the identity which is mismatched, not the verification process.
Just say "Bob's identity has been reset".

⚠️ Where possible, avoid talking about "cryptographic identity" which is very jargony.
In many contexts, just the word "identity" is sufficient: the dictionary definition of
identity meaning that someone is who they claim they are, not someone else. The
fact we confirm identity cryptographically is usually irrelevant to the user.

### Identity

A user's **identity** is proof of who they are, and, if you have verified them,
proof that you have a secure communication channel with them. Your own identity
proves who you are, and gives you access to key storage.

Technical note: we use "identity" here to describe a collection of keys: the
master signing key, user signing key, device signing key, key storage key and
others.

Your identity allows you to be identified by other users, and also allows you to
access key storage and therefore see message history. This identity may be
stored on the server by using recovery. The recovery key is not part of your
identity, but allows you to re-establish your identity if you lose all your
devices.

> When a non-verified user resets their identity:
> "Alice's identity has been reset."
>
> Longer explanation:
> This can happen if the user lost all their devices and the recovery key, but
> it can also be a sign of someone taking over the account. To be sure, please
> verify their identity by going to their profile.

> When a verified user resets their identity:
> "WARNING: Bob's identity has been reset!"

(During login, at the "Confirm it's you" stage):

> "If you don't have any other device and you have lost your recovery key, you
> can create a new identity. (Warning: you will lose access to your old
> messages!)" button text (in red or similar): "Reset my identity"

> "Are you sure you want to reset your identity? You will lose access to your
> message history."

⚠️ Avoid saying "master key" - this is an implementation detail.

⚠️ Avoid saying "Alice reset their encryption" - the change was to the user's
identity.

References:

* Wikipedia talks about "identity management":
  https://en.wikipedia.org/wiki/Identity_and_access_management
* OpenID talks about "identity": https://openid.net/foundation/
* Keyoxide talks about "identities": https://keyoxide.org/
* Keybase talks about "identity" and "identity proofs":
  https://book.keybase.io/docs/server
* WhatsApp talks about verifying your "identity":
  https://faq.whatsapp.com/1317564962315842/
* Signal avoids using a word for this, and talks about using a security number
  to "verify the security of messages with specific contacts":
  https://support.signal.org/hc/en-us/articles/360007060632-What-is-a-safety-number-and-why-do-I-see-that-it-changed
  but elsewhere does use the word "identity" in this context:
  https://support.signal.org/hc/en-us/articles/6829998083994-Phone-Number-Privacy-and-Usernames-Deeper-Dive#verification

All of the above are describing ways of proving who you are, which is close to
the use of "identity" here.

### Message key

A **message key** is used to decrypt a message. The metaphor is that messages
are "locked in a box" by encrypting them, and "unlocked" by decrypting them.

> "Store message keys on the server."

⚠️ Avoid saying "key" without a previous word saying what type of key it is.

⚠️ Avoid using "room key". These keys are used to decrypt messages, not rooms.

Note: this clashes with the term "message key" in the double ratchet. Since the
double ratchet algorithm is for a very different audience, this is not considered
a blocking conflict.

### Unable to decrypt

When we have an encrypted message but no message key to decrypt it, we are
unable to decrypt it. There are three different situations, which clients
should distinguish clearly:

#### Waiting for this message

When we expect the key to arrive, we are **waiting for this message**.

> "Waiting for this message" with a button: "learn more" that explains that the message key for
> this message has not yet been received, but that we expect it to
> arrive shortly. Further detail may be provided, for instance explaining that
> connectivity issues between the sender's homeserver and our own can cause
> key delivery delays.

#### You don't have access to this message

When the user does not have the message key for a permanent and well-understood
reason, for example if it was sent before they joined the room, we say **you
don't have access to this message**.

> "You don't have access to this message" e.g. if it was sent before the user
> entered the room, or the user does not have key storage set up.

#### An error occurred

When an error has occurred with the decryption process, we surface that error
with a different message e.g. "something went wrong with this message" - the
exact wording will depend on the communication style of the client.

Examples of errors like this include an incorrectly-formatted message, or a
problem with the client's storage of message keys.

### Message history

Your **message history** is a record of every message you have received or sent,
and is particularly used to describe messages that are stored on the server
rather than your device(s). Where messages are encrypted, the message keys are
required to be able to read them, so "message history" includes those keys,
which are held in key storage.

### Key storage

**Key storage** means message keys that are kept on the server, so that they can
be shared with the user's other devices (including new devices added in the
future).

The keys inside key storage are themselves encrypted, so that the server
operator is not able to access them and read your messages.

In the spec, key storage is referred to as
[server-side key backup](https://spec.matrix.org/v1.13/client-server-api/#server-side-key-backups).

> "Allow key storage"

> "Key storage holds the keys that allow you to read your message history."

> "Message history is unavailable because key storage is disabled."

⚠️ Avoid using "key backup" to talk about storing message keys: this is too
easily confused with exporting keys or messages to an external system. Key
storage is for day-to-day use (reading message history), not a redundant store
for disaster recovery.

⚠️ Avoid talking about more keys: "the backup key is stored in the secret
storage, and this allows us to decrypt the messages keys from key backup".
Instead, we simply say that both identity and message keys are
stored in key storage.

### Recovery

Recovery is useful when a user loses all their devices (or logs out of them
all).

If **recovery** is enabled, the user's identity is saved on the server, allowing
them to recover it if they lose all their devices. This in turn allows them to
recover their key storage and see message history. To recover their identity the
user must enter the **recovery key**.

The server is not able to read or manipulate the saved identity, because it is
encrypted using the recovery key.

If a user loses their recovery key, they may **reset** their identity. Unless
they have old devices, they will not be able to access old encrypted messages
because the new identity does not have access to the old key storage.

A **recovery key** (or **recovery code**) is a way of re-establishing your
identity if you lose all your devices. This in turn allows you to access key
storage, and therefore see message history. If you re-establish your identity
instead of resetting it, other users won't see "Alice's identity has been reset"
messages, and you will be able to read your message history, even if you logged
out everywhere or lost your devices.

A **recovery passphrase** is an easier-to-remember equivalent of the recovery
key that is user-entered instead of machine-generated. It has the same purpose
as the recovery key.

In the spec, recovery is referred to as
[secret storage](https://spec.matrix.org/v1.13/client-server-api/#secret-storage),
or "4S".

> "Write down your recovery key in a safe place"

> "If you lose access to your devices and your recovery key, you will need to
> reset your identity, meaning you will lose all your message history"

⚠️ Avoid "4S" or "quad-S" - these are not descriptive terms.

⚠️ Avoid using "security key", "security code", "master key". A
recovery key allows "unlocking" the key storage, which is a "box" that is on the
server, containing your identity and message keys. It is used to
recover the situation if you lose access to your devices. None of these other
terms express this concept so clearly.

⚠️ Remember that users may have historically been trained to refer to these
concepts as "security key" or "security passphrase", and so user interfaces
should provide a way for users to be educated on the terminology change (e.g. a
tooltip or help link): e.g. "Your recovery key may also have been referred to as
a security key in the past"

⚠️ Be aware that old versions of the spec use
["recovery key"](https://spec.matrix.org/v1.8/client-server-api/#recovery-key)
to refer to the private half of the backup encryption key, which is different
from the usage here. The recovery key described in this section is referred to
in the spec as the
[secret storage key](https://spec.matrix.org/v1.8/client-server-api/#secret-storage).

#### Losing the recovery key

If the user loses their recovery key, they no longer have a way to recover their
identity.

If the user still has a secure device, then that device has its own copy of the
identity information, so they can **change recovery key** without losing their
identity, meaning other users will not see "Alice's identity has been reset", and
they will be able to continue using key storage to access message history.

Note: users should be encouraged to change their recovery key if they have forgotten
their recovery key, because they are in a precarious position - if they lose
access to their device, they will be forced to reset their identity and lose
message history.

If the user does not have a device, or all their devices are insecure, then they
will need to reset their identity, meaning other users
see "Alice's identity has been reset", and they lose access to their old key
storage, meaning they cannot read message history.

> "If you lose your recovery key you can generate a new one if you are signed in
> elsewhere"

⚠️ Distinguish between "Reset identity" and "Change recovery key" - these are
very different actions: resetting identity is destructive, whereas changing
recovery key from a device that holds the full identity information is benign.

## Potential issues

Lots of existing clients use a whole variety of different terminology, and many
users are familiar with different terms. Nevertheless we believe that working
together to agree on a common language is the only way to address this issue
over time.

## Alternatives

### Device vs. Session and others

There is debate over whether "device" or "session" is the best word to identify
an instance of a client. In practice, many clients use both words, and there is
no consensus among the community for which is best.

This proposal initially chose "device" but it became clear that many people had
strong opinions in both directions, meaning that some clients would probably
stick with their wording even if the spec recommended otherwise, so it seemed
more pragmatic to allow either.

Several other words could also be used:

* "Login" is close in meaning to a device or session, but it could be confused
  with the actions of logging out or in, rather than an ongoing session.

* "Client" is commonly used in the context of email. This word originates in the
  technical idea of a client-server protocol, and is rarely used in
  non-technical contexts. Further, where it is used, it is most commonly
  referring to a program rather than a logged-in session.

* "App/Application" is very widely used, but is usually referring to a program
  rather than a logged-in session.

* "Account" is used quite widely, but is normally used to refer to a user's
  general identity or set of credentials, rather than a specific instance where
  the user logged in.

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
