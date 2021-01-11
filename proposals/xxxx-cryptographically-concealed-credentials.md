# MSCxxxx: Cryptographically Concealed Credentials

When logging in to Matrix using the `POST /login` endpoint, the client
transmits the password to the server, so the server is able to see the user's
password.  It is generally expected that the server would handle the password
securely, for example, only storing the password in a salted and hashed
format.  However a malicious server could store the user's password.  If a user
re-uses their password on other services, the server administrator could then
use the stored password to log in to the user's other accounts.  Also, this
means that the user's login password should not be the same as the password
that they use for [Secret
Storage](https://matrix.org/docs/spec/client_server/unstable#storage).

This proposal defines a way for users to authenticate without sending their
password to the server.  Additional goals of this proposal include:

- relatively simple to implement
- the data stored on the server cannot be used (apart from attacking the
  underlying cryptographic operations) to authenticate with the server
- the user can verify that the server that they are authenticating against is
  the same as the server where they originally created their account
- a malicious user who unsuccessfully tries to authenticate against the server
  does not gain any information about the user's password.  For example, an
  attacker cannot take any of the server's responses to perform any offline
  computations or guesses to try to obtain the user's password.


## Proposal

### Protocol overview

#### Notation

- A Curve25519 key pair is denoted <K<sub>priv</sub>,K<sub>pub</sub>>, where
  K<sub>priv</sub> is the private key and K<sub>pub</sub> is the public key.
- ECDH(A<sub>priv</sub>,B<sub>pub</sub>): the elliptic curve Diffie-Hellman of
  the private key A<sub>priv</sub> and the public key B<sub>pub</sub>.
- HKDF(K, S, I, L): HKDF-SHA-256 where K is the initial key material, S is the
  salt, I is the info, and L is the number of bits to generate.

#### Registration

When registering, the client generates an ephemeral Curve25519 key pair <C<sub>priv</sub>,C<sub>pub</sub>>, and
sends to the server:

- the user's desired Matrix ID
- C<sub>pub</sub>

The server generates its own ephemeral Curve25519 key pair
<S<sub>priv</sub>,S<sub>pub</sub>>, and sends the S<sub>pub</sub> to the user.

The client calculates K<sub>1</sub> = ECDH(C<sub>priv</sub>,S<sub>pub</sub>)
and then calculates

- K<sub>AES</sub> = HKDF(K<sub>1</sub>, "", "`encryption key|`\<Matrix ID>`|`C<sub>pub</sub>`|`S<sub>pub</sub>", 256)
- K<sub>MAC</sub> = HKDF(K<sub>1</sub>, "", "`mac key|`\<Matrix ID>`|`C<sub>pub</sub>`|`S<sub>pub</sub>", 256)

where \<Matrix ID> is the user's desired Matrix ID.

The client then takes the user's password and generates the base key
K<sub>base</sub> using PBKDF2 (K<sub>base</sub> can be used as the Secret
Storage key).  The client then calculates the Curve25519 private key
A<sub>priv</sub> = HKDF(K<sub>base</sub>, "", "`authentication key|`\<Matrix
ID>", 256), and the corresponding public key A<sub>pub</sub>.  The client sends
to the server, encrypted with AES-256-CBC using K<sub>AES</sub> the AES key
generated above:

- A<sub>pub</sub>
- the PBKDF2 parameters used

The ciphertext is MACed using HMAC-SHA-256 using K<sub>MAC</sub> as the key.

The server stores A<sub>pub</sub> securely stores the result of
K<sub>conf</sub> = HKDF(ECDH(S<sub>priv</sub>, C<sub>pub</sub>) ||
ECDH(S<sub>priv</sub>, A<sub>pub</sub>), "", "`confirmation key|`\<Matrix
ID>`|`A<sub>pub</sub>`|`C<sub>pub</sub>`|`S<sub>pub</sub>", 256), called the
confirmation key.

The client calculates K<sub>conf</sub> = HKDF(ECDH(C<sub>priv</sub>,
S<sub>pub</sub>) || ECDH(A<sub>priv</sub>, S<sub>pub</sub>), "", "`confirmation
tag|`\<Matrix ID>`|`A<sub>pub</sub>`|`C<sub>pub</sub>`|`S<sub>pub</sub>", 256),
and calculates HKDF(K<sub>conf</sub>, "", "`security check|`\<Matrix
ID>`|`A<sub>priv</sub>", 3), giving a number between 0 and 7.  The client then
displays the emoji (or the text equivalent) from the SAS verification emoji
list corresponding to that number.  The user remembers/records the emoji for
later verification.

#### Logging in

The client generates an ephemeral Curve25519 key pair
<C'<sub>priv</sub>,C'<sub>pub</sub>> and sends their Matrix ID and
C'<sub>pub</sub> to the server.

The server then generates its own ephemeral Curve25519 key pair
<S'<sub>priv</sub>,S'<sub>pub</sub>> and calculates K'<sub>AES</sub> = HKDF(ECDH(S'<sub>priv</sub>,
A<sub>pub</sub>) || ECDH(S'<sub>priv</sub>, C'<sub>pub</sub>), "", "`server
encryption|`\<MATRIX ID>`|`A<sub>pub</sub>`|`C'<sub>pub</sub>`|`S'<sub>pub</sub>", 256).

- the PBKDF2 parameters to use,
- S'<sub>pub</sub>
- a random 32-byte nonce
- K<sub>conf</sub>, encrypted with AES-256-CBC using K'<sub>AES</sub>

The client performs PBKDF2 on the user's password using the given parameters to
generate the base key K<sub>base</sub>.  It then calculates

- the Curve25519 private key A<sub>priv</sub> = HKDF(K<sub>base</sub>, "",
  "`authentication key|`\<Matrix ID>", 256) and the corresponding public key
  A<sub>pub</sub>
- K'<sub>AES</sub> = HKDF(ECDH(A<sub>priv</sub>, S'<sub>pub</sub>) ||
  ECDH(C'<sub>priv</sub>, S'<sub>pub</sub>), "", "`server encryption|`\<MATRIX
  ID>`|`A<sub>pub</sub>`|`C'<sub>pub</sub>`|`S'<sub>pub</sub>", 256), and
  decrypts K<sub>conf</sub> using K'<sub>AES</sub>.
- HKDF(K<sub>conf</sub>, "", "`security check|`\<Matrix ID>`|`A<sub>priv</sub>",
  3)

The client displays the emoji (or text equivalent) from the SAS verification
emoji list corresponding to the number given by the last calculation, and
allows the user to check that the emoji matches the one displayed when the user
registered their account.  This allows the user to verify (to a degree of
confidence) that they entered their password correctly, and that they are
communicating with the same entity that they were communicating with when they
registered.

The client then calculates K'<sub>MAC</sub> = HKDF(ECDH(A<sub>priv</sub>,
S'<sub>pub</sub>) || ECDH(C'<sub>priv</sub>,S'<sub>pub</sub>), "", "`client
MAC|`\<Matrix
ID>`|`A<sub>pub</sub>`|`C'<sub>pub</sub>`|`S'<sub>pub</sub>`|`K<sub>conf</sub>",
256), and sends an HMAC of the nonce using this key to the server.

The server calculates K'<sub>MAC</sub> = HKDF(ECDH(S'<sub>priv</sub>,
A<sub>pub</sub>) || ECDH(S'<sub>priv</sub>,C'<sub>pub</sub>), "", "`client
MAC|`\<Matrix
ID>`|`A<sub>pub</sub>`|`C'<sub>pub</sub>`|`S'<sub>pub</sub>`|`K<sub>conf</sub>",
256) and K''<sub>MAC</sub> = HKDF(ECDH(S'<sub>priv</sub>,
A<sub>pub</sub>) || ECDH(S'<sub>priv</sub>,C'<sub>pub</sub>), "", "`server
MAC|`\<Matrix
ID>`|`A<sub>pub</sub>`|`C'<sub>pub</sub>`|`S'<sub>pub</sub>`|`K<sub>conf</sub>",
256), verifies the HMAC sent by the client, and responds with an HMAC of the
nonce using K''<sub>MAC</sub>.

### Protocol details

TODO:

## Security characteristics

### Replay attacks

If an attacker tries to replay the client's messages to the server to
authenticate with it, the authentication will fail since authentication depends
on the randomly chosen ephemeral key and nonce which will be different for the
attacker's session.

### Data breach

If the server's database is leaked, this could reveal A<sub>pub</sub> and
K<sub>conf</sub>.

An attacker could try to brute-force the user's password by trying various
passwords and performing the PBKDF2 and HKDF operations to see if it yields a
Curve25519 private key that matches A<sub>pub</sub>.  However, PBKDF2 will slow
down the attacker's attempts.  This is no worse than the current practice of
storing a hashed version of the user's password.  This can also be made more
secure by encrypting A<sub>pub</sub> using a key that is stored separately from
the database, similarly to how Synapse allows specifying a "pepper" value that
is used when hashing the user's password.  In this way, an attacker who only
has the database, and not the additional encryption key, cannot retrieve
information about the user's password.

If the attacker obtains A<sub>pub</sub> and K<sub>conf</sub>, they can
impersonate the server to the user.  Again, this can be partially mitigated by
encrypting K<sub>conf</sub> in addition to A<sub>pub</sub> using a key that is
stored separately from the database.

Since the server does not know the private key A<sub>priv</sub>, the attacker
cannot use the data stored on the server to authenticate as the given user
short of attacking Curve25519 to obtain A<sub>priv</sub> from A<sub>pub</sub>.

### Deniability

Even though the protocol allows the server to authenticate the user, it cannot
prove to a third party that the user authenticated with it, even if it produces
a full transcript of the authentication process.  All information contained in
the client's requests is either known to the server or could be created by the
server, so the server cannot prove that the requests were created by the user
and not fabricated by the server.

### Offline computation

If an attacker initiates a login attempt, the server does not reveal any
information that would help the attacker determine the user's password.  The
server only reveals: the PBKDF2 parameters to use (which should be viewed as
public information, and do not give any information about the password),
S'<sub>pub</sub> and a random 32-byte nonce (which are single-use and are not
related to the user's password), and an encrypted version of K<sub>conf</sub>.

If the attacker knows K<sub>conf</sub>, they could try to brute-force the
user's password until they can decrypt the encrypted version of
K<sub>conf</sub> to obtain the known value of K<sub>conf</sub>.  However, if
the attacker knows K<sub>conf</sub>, they would also know A<sub>pub</sub>,
which would already allow them to try to brute-force the user's password, so in
this case, the attacker does not gain any information by attempting to log in.
Note that in this case, it is important that the encryption of K<sub>conf</sub>
is done in an unauthenticated manner to ensure that an attacker is not given
any information about whether or not they have guessed the right decryption
key.

It should be noted that an attacker who shoulder-surfs when the user registers
or logs in will be able to see the emoji security check displayed to the user.
The attacker may then use this to reduce the search space when trying
passwords.  Since there are eight possible emoji, this reduces the search space
by a factor of 8, which can be compensated for by the user adding an extra
character to their password.  As well, the attacker still needs to test each
password by submitting requests to the server, and so can be rate-limited by
the server.  Since the emoji security check provides some feedback to the user
on whether they mistyped their password (a mistyped password would have a 7/8
chance of displaying the wrong emoji), servers can more aggressively rate-limit
login attempts when using this method.

### Man-in-the-middle attacks

TODO: ...

### Phishing

TODO: ...

### ...

## Potential issues

This proposal cannot be used by users who log in using SSO, or whose passwords
are managed by an external system.

...

## Alternatives

TODO: compare with various PAKEs

TODO: compare with SCRAM

### Argon2

Argon2 would likely be a better option than PBKDF2 for generating a key from
a password.  However, this proposal uses PBKDF2 for compatibility with Secret
Storage, which used PBKDF2 due to the availability of implementations of both
algorithms.  (For example, WebCrypto includes a PBKDF2 implementation, but not
an Argon2 implementation.)  In the future, we may switch to Argon2 for both
authentication and Secret Storage.

## Security considerations

### Old clients

If a user tries to log into their account using a server that does not follow
this proposal may send the user's password to the server by trying to log in
using the current `POST /login` endpoint.  This can be partially mitigated in
two ways.

1. Deployments in which the choice of clients is not well controlled should not
   enable this feature until most of the commonly-used clients are updated to
   support this feature.  It is up to individual server administrators to
   determine when to do this.

2. Users should be educated to expect to see and verify the emoji security
   check before submitting the password.  Old clients will not display the
   emoji, providing a hint to users that the client does not support this
   authentication method.

## Unstable prefix

TODO:
