# MSC3839: primary identity as public / private key-pair

In Matrix in general and most homeservers in particular, users are
registered and authenticated using a username and password.
Additionally, tokens are used and sessions are registered as separate entities.  
Encryption keys are quite often yet another datafile stored on a homeserver
encrypted using yet another password.

Users that need to backup or migrate their data are finding this
challenging at best.

*Note: The initial author is absolutely not a Matrix protocol expert, the
proposal here is likely to lack the historical or even technical
understanding of Matrix.  
The author asks those better known with Matrix to help out improve this
idea into a fully usable upgrade for the Matrix ecosystem.*

Password based authentication is also getting more frowned upon in the
wider tech industry, and for good reason. The amount of password leaks has
increased dramatically in the last years with billions of username/password
pairs being available on the darknet.
The suggestion that people come up with better passwords or stop reusing
them is simply trying to fix the wrong thing. Passwords are on its way out
because many in the industry are realizing that you can't change human
behavior.

Passwords are also a home-server operator nightmare. The current Matrix
design makes the password plain text available to the server and thus the
server operator. Next to that, the one solution to allow a password reset
is to add an email address. But that instantly gets you into the territory
of privacy laws and those issues makes the homeserver a target for hacking.
Paired with this is the issue that plenty of accounts on public homeservers
simply are abandoned because their owner never wrote down the password or
username and lost access.

An established cryptographers concept called pubic/private key technology
can be used to provide a much better user experience and at the same time
increase the security all round.

Wikipedia; https://en.wikipedia.org/wiki/Public-key\_cryptography

## Proposal

A user identity can be coupled to a cryptographic public key where the
users device / app holds the private key. Doing a backup simply saves the
private key in a file or prints it in one QR code.

This allows a chat-client to authenticate the user to a homeserver without
username or password for more security and a better user experience.
Naturally a homeserver may choose to support web-app users and keep the
password design for those that don't want to have an actual app, this
proposal doesn't demand a removal of the old login but does aim to replace
all non-webbrowser based chat-identities with public keys.

The basic idea is that a user-device generates a random private key on
first account creation and derives a public key from that which will be the
main identification of the user from then on. Homeservers will be able to
store the public key instead of a username/password pair for identity.
Login can be implemented by the homeserver sending a random token (with a
timestamp to avoid replay attacks). The client simply signs it using the
private key and returns it to the homeserver which can validate the
signature using the public key that is the users-ID.

A chat application that creates or receives messages in an end-to-end
encrypted chat will also create local keys (possibly tied to that session).
Such a client can use the private-key-as-identity in order to encrypt the
keys-used-for-end2end encryption. Uploading those to the users homeserver
is then safe and hassle free. Same with cross-signing.

Matrix has a lot of security features and for the average user they can be
overwhelming. The goal of making Matrix clients at least as easy as the
competition will be much easier to reach when username and passwords are
removed. Some of the really big chat apps do not have them either.
At the same time the option stays open to be as strict on security as the
user deems needed. The reader may have worked with ssh and knows they can
put a password on their private key, the same can be added in clients.
Again, should the user feel this is needed.

A login feature that competitors have, where the main client scans a QR
from a webbrowser to login the web-app can also be easily implemented
for users using a public key as identity. Even with minimal homeserver
support. A client that gets a challenge can simply show this in a QR
for the user to scan and sign in her main chat-app, to send that answer to
the server allowing the webapp to authenticate their session without
password.
Some way to resolve the public key from the related account name is needed
on the server side.

## Potential issues

The relation between a user-secret and a user-session is expected to stay
unchanged. A client requests a token and has a session.  
But having a password change is no longer something that happens on the
server, it happens completely local on the client. Many users will simply
have an empty password since the private key is protected from leakage by
their OS.
So, when a user resets a password this has no effect on sessions unless the
user explicitly goes and invalidates those sessions.

As such the risk increases where a user that somehow shared their private
key which had no password will not be able to protect their account from
others taking over.

In my opinion this is an acceptable risk. The attack model doesn't really
change and phone-local (or laptop local) protections are the same as any
other sensitive data stored on that device.

## Alternatives

None yet.

## Security considerations

Public key crypto is well established and there are many different options
to choose from. The main consideration is likely going to be what
already-in-use libraries provide.

## Dependencies

None
