# Proposal for storing an encrypted recovery key on the server to aid recovery of megolm key backups

## Problem

[MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219) proposes an API for optionally storing encrypted megolm keys on your homeserver, so if a user loses all their devices, they can still recover their history.  The megolm keys are public-key encrypted using a private Curve25519 key that only the end-user has.

However, there are usability concerns about users having to store their Curve25519 recovery private key in a secure manner.  Casual users are likely to be scared away by having to file away a relatively long (e.g. 10 word) generated recovery key.

## Proposed solution

Taking inspiration from Apple’s [FileVault 2](https://hal.inria.fr/hal-01460615/document) full-disk encryption, we'd like to give the user the option to encrypt their key with a passphrase and store it on the server (much as Apple store encrypted copies of your FileVault AES key on your hard disk, encrypted by your UNIX account password).  This is also similar to storing a passphrased SSH private key on a server for convenience.

In practice, this means:
 * Mandating that clients use a high complexity passphrase to encrypt the recovery key - either by enforcing complexity requirements or by generating it for them (similar to 1Password's password creation UX).
 * Symmetrically encrypting the Curve25519 key by N rounds of PBKDF2(key, passphrase) where N=100,000 - similarly to how we encrypt [offline megolm key backups](https://github.com/matrix-org/matrix-doc/issues/1211) today.  (TODO: This needs to be fleshed out).
 * Storing the encrypted key on the server.

We propose storing it using the /account_data API:

```json
PUT /_matrix/client/r0/user/{userId}/account_data/m.recovery_key

{
	"algorithm": "m.recovery_key.v1.curve25519.pbkdf2",
	"data": <base64>,
	"m.hidden": true,
}
```

We propose extending the /account_data API with two conveniences:
 * the `m.hidden` event field to indicate to the server that such events should not be included in /sync responses to clients.
 * a `GET /_matrix/client/r0/user/{userId}/account_data/m.recovery_key` accessor, symmetrical to the existing PUT method, to access the data when needed.

We deliberately encrypt the Curve25519 private key rather than deriving it from the passphrase so that if the user chooses not to store their encrypted recovery key on the server, they can benefit from a Curve25519 key generated from a high entropy source of random rather than being needlessly derived from a passphrase of some kind.  (TODO: Is this accurate)?

## Security considerations

The proposal above is vulnerable to a malicious server admin performing a dictionary attack against the encrypted passphrases stored on their server to access history.  (It's worth bearing in mind that the server admin can also always hijack its user's accounts; the thing that stopping them from impersonating their users is E2E device verification.)

## Possible extensions

In future, we could consider supporting authenticating users for login based on their encrypted passphrase, meaning that users only have to remember one password for their Matrix account rather than a login password and a history-access passphrase.  However, this of course exposes the user's whole E2E history to the risk of dictionary attacks by public attackers (i.e. not just server admins), keysniffer-at-login attacks or clients which are lazy about storing account passwords securely.  There's also a risk that because login passwords are much more commonly entered than history passwords, they might encourage users to force a weaker password.  It's unclear whether this reduction in security-in-depth is worth the UX benefits of a single master password, so we suggest checking how this proposal goes first (given in general we expect key recovery to happen by cross-verifying devices at login rather than by entering a recovery key or passphrase).

## See also:

Notes from discussing this IRL are at https://docs.google.com/document/d/11fF1rbX5eTkrfxXRS8UhpW5sBENOCydYlLWzB8X1IuU/edit