# MSC3726: Safer Password-based Authentication with BS-SPEKE

In Matrix's `m.login.password` authentication mechanism, the client
sends their password to the server, using TLS to protect against
eavesdroppers in the network.
However, the password is still exposed to the server, as well as
to any caching proxies that terminate the TLS session.
This can be problematic for a number of reasons:

1. Owners of large servers (eg matrix.org) may feel the need to use
   content distribution networks (CDN's) like Cloudflare in order to
   handle massive amounts of traffic.
   In this case, the CDN learns the password of every user who logs in.

2. Users can be lazy, and they often re-use passwords across multiple
   accounts on different services.
   An attacker who can temporarily compromise the homeserver could learn
   the user's password at login; then they could use this password to
   log in to other services as that user.

3. In Matrix, users can use a password to securely back up their keys on
   the server and to verify their devices.
   In practice, doing so can significantly improve the reliability of 
   E2EE with multiple devices.
   However, we know that users tend to be lazy, and it is likely that
   many users will simply re-use their login password (or a slight 
   variation of it) for their recovery password.
   Such a user gets very little practical benefit from E2EE, since the
   server could easily guess their encryption password and recover all
   of their keys.
   On the other hand, the users who *do* choose good passwords now have
   the additional burden of remembering yet another complex password.
   It would be better for both groups of users if we could do everything
   securely from a single password.

Fortunately there exists a class of cryptographic protocols called
"Password Authenticated Key Exchange" (PAKE).
These provide a more secure way to authenticate users based on a password,
without ever revealing the plaintext of the password to the server.

## Proposal

This MSC proposes a new authentication login flow based on the PAKE protocol
[BS-SPEKE](https://tobtu.com/blog/2021/10/srp-is-now-deprecated/).

The sections below describe the proposed use of BS-SPEKE in the Matrix
client-server API endpoints for [registration](#registration),
[login](#login), and for changing the user's [password](#changing-passwords).

**Acknowledgement**: This MSC builds on work in a previous proposal,
[MSC3262](https://github.com/matrix-org/matrix-doc/pull/3262),
for Matrix login with an earlier PAKE protocol, SRP.
Many thanks to `@mathijs:matrix.vgorcum.com` and other members of 
`#secure-login:matrix.vgorcum.com` for their work on that MSC.
The decision was made to switch from SRP to BS-SPEKE only after
receiving strong feedback from experts in applied cryptography.

### Advantages of BS-SPEKE
BS-SPEKE is a direct descendant of the original PAKE protocol, Bellovin
and Merritt's Encrypted Key Exchange (EKE).
Unfortunately EKE and its successor SPEKE were previously patented, so
they saw only limited use.
However those patents expired in 2011 and 2017, respectively, and
as a result, SPEKE-derived protocols like BS-SPEKE can now be used freely.

BS-SPEKE comes highly recommended by experts in applied cryptography,
and it offers a number of advantages over earlier PAKE protocols, including:

* It is an "augmented" PAKE, meaning that the server never gains enough
  information to impersonate the client.
* It makes brute-force password recovery attacks very expensive,
  so even if the server is malicious or compromised, it is not easy
  for the adversary to recover the user's password.
* It is "quantum annoying", meaning that even if the adversary has a
  quantum computer and can compute discrete logarithms, the adversary
  still must compute a very large number of discrete logs before they
  can recover a user's password.
* It is built with standard and well-known cryptographic constructions,
  namely the Noise-KN key exchange and an efficient oblivious pseudorandom
  function (OPRF).

For more details, please see the [Appendix](#appendix-technical-background)
at the end of this document.


## Registration

### `/register` Request 1
To register for a new account using BS-SPEKE from the start, the client
sends an HTTP request to the `/register` endpoint with `kind` set to `user`
and the requested username in the JSON body.

```
POST /_matrix/client/v3/register&kind=user
```

```json
{
    "username": "alice"
}
```

### `/register` Response 1

A server that supports BS-SPEKE login will reply with a login flow that contains
`m.register.bsspeke.ecc`.

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

```json
{
  "flows": [
    {
      "stages": [ ..., "m.register.bsspeke.ecc"]
    }
  ],
  "session": "xxxxx",
  "params": {
    "m.register.bsspeke.ecc": {
      "curves": [supported elliptic curves],
      "hashes": [supported hash functions] 
	  }
    }		
}
```

Where

* `curves` is a list of the elliptic curves supported by the server.
  Currently, the only supported value is `curve25519`, for D.J. Bernstein's
  [Curve25519](https://cr.yp.to/ecdh.html).

* `hashes` is a list of the cryptographic hash functions supported by the server.
  The output length for the hash function MUST BE the effective byte width of the 
  elliptic curve group, e.g. 32 bytes for Curve25519.
  Currently supported hash functions for Curve25519 are `sha256`
  for SHA-256 and `blake2b` for Blake2b configured for 32 bytes of output.

To complete the `m.register.bsspeke.ecc` stage requires two additional round-trips.
In the first request/response pair, the client and server exchange the
information required for the oblivious PRF.
In the second request, the client sends its public parameters, computed
from the user's password and the OPRF.
If the registration request is successful, the server responds with the
user's `user_id` and (if `inhibit_login` is false) the new `device_id`
and `access_token` for the device.

### `/register` Request 2

```
POST /_matrix/client/v3/register&kind=user
```

```json
{
    "username": "alice",
    "auth_type": "m.login.bsspeke.ecc",
    "auth": {
        "type": "m.register.bsspeke.ecc",
        "session": "xxxxx",
        "curve": "curve25519",
        "hash": "blake2b",
        "blind": <base64-encoded curve point>,
    }
}
```

### `/register` Response 2

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

```json
{
  "flows": [
    {
      "stages": [ ..., "m.register.bsspeke.ecc"]
    }
  ],
  "session": "xxxxx",
  "params": {
    "m.register.bsspeke.ecc": {
      "curves": [supported elliptic curves],
      "hashes": [supported hash functions],
      "curve": "curve25519",
      "hash": "blake2b",
      "blind_salt": <base64-encoded curve point>
	  }
    }		
}
```

### `/register` Request 3

```
POST /_matrix/client/v3/register&kind=user
```

```json
{
    "username": "alice",
    "auth_type": "m.login.bsspeke.ecc",
    "auth": {
        "type": "m.register.bsspeke.ecc",
        "session": "xxxxx",
        "curve": "curve25519",
        "hash": "blake2b",
        "P": <base64-encoded curve point>,
        "V": <base64-encoded curve point>,
        "phf_params": {
            "name": "argon2i",
            "blocks": 100000,
            "iterations": 3,
        }
    }
}
```

### `/register` Response 3

```
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{
  "access_token": "abc123",
  "device_id": "GHTYAJCE",
  "user_id": "@alice:example.org"
}

```


## Login
The BS-SPEKE login is described by Steve Thomas (aka Sc00bz) in a
[Github gist](https://gist.github.com/Sc00bz/e99e48a6008eef10a59d5ec7b4d87af3).
This protocol can be mapped onto Matrix as follows.

Here we build on [MSC2835: Add UIA to the /login endpoint](https://github.com/matrix-org/matrix-doc/pull/2835)
and implement BS-SPEKE in Matrix's user-interactive authentication system.

### `/login`: Request 1

To start the login process, the client sends a `POST` request to `/_matrix/client/r0/login`

### `/login`: Response 1

A server that supports BS-SPEKE login will reply with

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

```json
{
  "flows": [
    {
      "type": "m.login.bsspeke.ecc"
    }
  ],
  "params": {
      "m.login.bsspeke.ecc": {
          "curve": "curve25519",
          "hash": "blake2b",
      }
  },
  "session": "xxxxxx"
}
```

The required parameters for `m.login.bsspeke.ecc` define something sort of
like a cipher suite, a collection of cryptographic primitives to be used to
instantiate the BS-SPEKE algorithm for this login stage.

* `curve` -- Defines which elliptic curve to use.
  Currently the only supported value is `curve25519`,
  although other curves may be added in the future.
* `hash` -- A (fast) cryptographic hash function.
  Currently supported hashes are `blake2b` and `sha256`.

The output length of the hash function MUST be AT LEAST the bit width
of the elliptic curve.


### `/login`: Request 2

At this point, we are ready to begin the BS-SPEKE protocol.

The client starts by generating its input for the OPRF.
It computes:

1. A point on the curve derived from the user ID, the server domain,
   and the user's password.
   ```
   HashToPoint( H( password || user_id || server_id ) )
   ```

   Here the `HashToPoint` function is [Elligator](https://elligator.cr.yp.to/),
   and `H` is the hash function `hash` from [Response 1](#login-response-1).

   *Note that here we're using the "standard" fast cryptographic
   hash, e.g. `blake2b` or `sha256`, even though we're hashing
   the user's password.
   Usually this kind of thing is unsafe, but it's actually OK here
   because we're about to "blind" (obscure) the value in Step 3
   below before we send it to the server.*

2. A large random number `r`, of the same bit width as the curve,
   e.g. 256 bits for Curve25519.

3. `blind`, the product of the random number `r` and the curve point
   defined by the user ID and password.
   ```
   blind = r * HashToPoint(H(password||user_id||server_domain))
   ```

The client sends a `POST` request to `/_matrix/client/r0/login`
containing the user ID and the blinded curve point `blind`.

```json
{
    "auth": {
        "type": "m.login.bsspeke.ecc",
        "identifier": {
            "type": "m.id.user",
            "user": "<user id or user localpart>"
        },
        "blind": "<base64-encoded curve point computed above>",
        "session": "xxxxxx"
    }
}
```

### `/login`: Response 2

Here the server begins the Noise-KN key exchange.
It looks up the base point `P` for the given user.
Then it generates an ephemeral private key `b` and multiplies
`b` by `P` to get its ephemeral public key.

```
P = LookupBasePoint(user_id)
b = random()
B = b * P
```

The server also provides its contribution to the OPRF,
hashing the salt that it stores for the given user, and
multiplying it by the client's blinded point `blind`.

```
salt = LookupSalt(user_id)
blind_salt = H(salt) * blind
```

The server sends its public key `B` and the blinded salt
`blind_salt` in its response to the client.

```json
{
  "completed": [],
  "flows": [
    {
      "stages": ["m.login.bsspeke.ecc"]
    }
  ],
  "params": {
      "m.login.bsspeke.ecc": {
          "curve": "curve25519",
          "hash": "blake2b",
          "phf_params": {
	      "name": "argon2i",
              "blocks": 100000,
              "iterations": 3
          },
          "B": "<base64-encoded B>",
          "blind_salt": "<base64-encoded blind_salt>"
      }
  },
  "session": "xxxxxx"
}
```

PHF params:
  These define the work factor of the password hash for protection
  against brute force attacks.
  Required parameters for `argon2i` are `blocks` and `iterations`.
  The only required parameter for `bcrypt` is `iterations`.

Clients should abort the login process if they receive a PHF work factor
below some minimum threshold.
The minimum thresholds should be AT LEAST:
* For `bcrypt`, `iterations=14`
* For `argon2i`, `iterations=3`, `blocks=FIXME`



### `/login`: Request 3

Upon receiving [Response 2](#login-response-2), the client finishes
the computation of the OPRF.
It multiplies `blind_salt` by `1/r` to remove the blinding and derive
the oblivious salt.
(This is the value that the BS-SPEKE spec confusing refers to as "BlindSalt".)

```
oblivious_salt = (1/r) * blind_salt
phf_salt = H( oblivious_Salt || user_id || server_id )
p || v = PHF(password,  phf_salt, phf_params)
```

The client then uses `p` and `v` to derive its long-term key pair.
It hashes `p` to a point on the curve to derive its own local
copy of the base curve point `P`.  (The server already has a copy
of `P`, which it stored when the user last set their password.)

```
P = HashToPoint(p)
```

The client then proceeds with its portion of the Noise-KN
key exchange.
It generates its ephemeral private key `a` and derives its
ephemeral public key `A` from the private key.

```
a = random()
A = a * P
```

The client computes its version of the shared key.

```
client_key = H( user_id || server_id || A || B || a * B || v * B )
```

It uses the shared key to compute a verifier that it can send
to the server.

```
client_veriifer = H( client_key || "client" )
```

The third request contains `A` and `client_verifier`:

```json
{
    "auth": {
        "type": "m.login.bsspeke.ecc",
        "identifier": {
            "type": "m.id.user",
            "user": "<user id or user localpart>"
        },
        "A": "<base64-encoded A>",
	"client_verifier": "<base64-encoded client_verifier>",
        "session": "xxxxxx"
    }
}
```

### `/login`: Response 3

On receiving [Request 3](#login-request-3), the server uses
`A` to compute its own local version of the shared key.

```
server_key = H( user_id || server_id || A || B || b * A || b * V )
```

The server verifies that `client_verifier == H( server_key || "client" )`.

If the check fails, the server returns `HTTP 403 Forbidden`

If the check succeeds, then the server marks the user as logged in.

It also generates a hash that the client can verify.
```
server_verifier = H( server_key || "server" )
```

The server returns the hash to the client in its response.

```
HTTP/1.1 200 Success
Content-Type: application/json
```

```json
{
  "completed": ["m.login.bsspeke.ecc"],
  "flows": [
    {
      "stages": ["m.login.bsspeke.ecc"]
    }
  ],
  "params": {
      "m.login.bsspeke.ecc": {
          "curve": "curve25519",
          "hash": "blake2b",
          "phf_params": {
	      "name": "argon2i",
              "blocks": 100000,
              "iterations": 3
          },
          "server_verifier": "<base64-encoded hash from the server>"
      }
  },
  "session": "xxxxxx"
}
```

### `/login`: Last Steps

The client MUST NOT consider the login successful until it has
successfully verified the server's hash.

If `server_verifier == H( client_key | "server" )` then mark the
user as logged in and return success.

Otherwise return failure.

## Changing Passwords

The process for changing an existing BS-SPEKE user's password looks
very much the same as the process outlined above for creating a new
account with BS-SPEKE.
The same procedure can also be used to upgrade an existing user from
the old-style `m.login.password` to the new BS-SPEKE cryptographic login.

### `/account/password` Request 1

The client indicates that it would like to configure a new password
for BS-SPEKE by setting the `auth_type` parameter to `m.login.bsspeke.ecc`.

```
POST /_matrix/client/v3/account/password
```

```json
{
    "auth_type": "m.login.bsspeke.ecc",
    ...
}
```

### `/account/password` Response 1

If the server supports BS-SPEKE cryptographic login, it should respond
with a UIA flow that includes the `m.register.bsspeke.ecc` stage described
above for [/register](#registration).

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

```json
{
  "flows": [
    {
      "stages": [ ..., "m.register.bsspeke.ecc"]
    }
  ],
  "session": "xxxxx",
  "params": {
    "m.register.bsspeke.ecc": {
      "curves": [supported elliptic curves],
      "hashes": [supported hash functions] 
	  }
    }		
}
```

### `/account/password` Request 2

Assuming that no other UIA stages are required by the server's policy,
the second request provides the client's `blind` for the OPRF.

```
POST /_matrix/client/v3/account/password
```

```json
{
    "auth_type": "m.login.bsspeke.ecc",
    "auth": {
        "type": "m.register.bsspeke.ecc",
        "session": "xxxxx",
        "curve": "curve25519",
        "hash": "blake2b",
        "blind": <base64-encoded curve point>,
    }
}
```

### `/account/password` Response 2

The server uses the client's `blind` to blind its private salt
for the user, and responds with the blind salt.

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
```

```json
{
  "flows": [
    {
      "stages": [ ..., "m.register.bsspeke.ecc"]
    }
  ],
  "session": "xxxxx",
  "params": {
    "m.register.bsspeke.ecc": {
      "curves": [supported elliptic curves],
      "hashes": [supported hash functions],
      "curve": "curve25519",
      "hash": "blake2b",
      "blind_salt": <base64-encoded curve point>
	  }
    }		
}
```


### `/account/password` Request 3

In the 3rd and final request, the client supplies the base point `P`
for the user, the user's new long-term public key `V`, and the parameters
for the password hashing function that it used to derive `P` and `V`
from the user's password.

The server will use `P` and `V` to authenticate the client on future
requests to [/login](#login), and it will supply future clients with
the PHF parameters because the user may be logging in from a different
device than the one used to change the password.

```
POST /_matrix/client/v3/account/password
```

```json
{
    "auth_type": "m.login.bsspeke.ecc",
    "auth": {
        "type": "m.register.bsspeke.ecc",
        "session": "xxxxx",
        "curve": "curve25519",
        "hash": "blake2b",
        "P": <base64-encoded curve point>,
        "V": <base64-encoded curve point>,
        "phf_params": {
            "name": "argon2i",
            "blocks": 100000,
            "iterations": 3,
        }
    }
}
```


### `/account/password` Response 3

If the user's new BS-SPEKE authentication parameters for the new
password were set up successfully, the server responds with a simple
HTTP `200 OK` with no content.

```
HTTP/1.1 200 OK
Content-Type: application/json
```

```json
{}
```

## Potential issues

**FIXME Add this section **


## Alternatives

### Client-side Hashing ([MSC3265](https://github.com/matrix-org/matrix-doc/pull/3265))
In the social media Matrix client Circles, the author of this MSC hacked together
a crude construction using client-side password hashing.
Instead of sending the user's raw password to the server, the client instead
uses a specially-crafted hash of the raw password as the new login password.
This prevents the server from learning the user's "real" password, but it does
not prevent a malicious CDN from logging in as the user.
A similar approach is reportedly used in BitWarden.

### SRP ([MSC3262](https://github.com/matrix-org/matrix-doc/pull/3262))
SRP is another PAKE protocol, originally developed to work around the patents
on EKE and SPEKE.
It has survived for many years without the discovery of any major vulnerabilities;
as one famous cryptographer put it, "It's not ideal, but it's real."
On the other hand, SRP uses some unique constructions that most cryptographers
are not excited about.
Unfortunately, some experts are now strongly recommending against using SRP
for anything new.
(See for example [SRP is Now Deprecated](https://tobtu.com/blog/2021/10/srp-is-now-deprecated/).)

### A New Home-Grown PAKE ([MSC2957](https://github.com/matrix-org/matrix-doc/pull/2957))

### Other PAKE Protocols
There are several other PAKE protocols available, including 
OPAQUE,
SCRAM,
[SPAKE2+](https://tools.ietf.org/id/draft-bar-cfrg-spake2plus-00.html).

Note that OPAQUE and SPAKE2+ include techniques that may be covered by
patents in the US/EU until 2023 or 2026.
(Source: [2019 CFRG PAKE Selection](https://github.com/cfrg/pake-selection#questions-for-round-2))
> (to all 4 remaining PAKEs) : Can the nominators/developers of the protocols please re-evaluate possible IPR conflicts between their candidates protocols and own and foreign patents? Specifically, can you discuss the impact of U.S. Patent 7,047,408 (expected expiration 10th of march 2023) on free use of SPAKE2 and the impact of EP1847062B1 (HMQV, expected expiration October 2026) on the free use of the RFC-drafts for OPAQUE?


## Security considerations

The overall security impact of this proposal will be to give users much stronger
protection for their passwords.

* Protects users' passwords against compromised or malicious CDN's

* In the near future, it will enable a more principled approach to something like
  MSC3265, where users only need to remember a single password for both login and
  recovery / backup / SSSS.

* Also, because BS-SPEKE is not just an authentication protocol, but a
  *key exchange protocol*, it sets up a secret symmetric key shared by
  the client and server but unknown to anyone else.
  This could be used in the future to encrypt and/or MAC messages sent
  between the client and the homeserver through a malicious or nosy CDN.

At the same time, there are some risks to be aware of:

* BS-SPEKE, like many modern cryptographic protocols, is a complicated beast, with
  a lot of moving parts.  Most implementors should not attempt to write elliptic 
  curve crypto code on their own.

* The client receives the parameters for the password hash from the server.
  A malicious server could send the client fake parameters carefully chosen
  to make the hash easier to brute-force.
  Client implementations should set a minimum work factor and refuse to 
  compute hashes with any work factor less than the minimum.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


Proposed final identifier       | Purpose    | Development identifier
------------------------------- | ---------- | ----
`m.login.bsspeke.*`             | login type | `org.futo.mscFIXME.login.bsspeke.*`

## Dependencies

This MSC builds on [MSC2835: Add UIA to the /login endpoint](https://github.com/matrix-org/matrix-doc/pull/2835).

Some of the basic changes to the CS API, for support for more flexible authentication
mechanisms in general, were moved out of this proposal and into [MSC3744](https://github.com/matrix-org/matrix-doc/pull/3744).

## Appendix: Technical Background

PAKE protocols are complex things.  In order to help reviewers make sense
of this proposal, this section attempts to give a brief introduction to
the technological underpinnings of BS-SPEKE.

BS-SPEKE can be viewed as the combination of three well-known
crytographic constructions:
1. An efficient one-round OPRF,
2. A trick from SPEKE for deriving Diffie-Hellman group parameters
   from a user's password,
3. The [Noise-KN handshake](https://duo.com/labs/tech-notes/noise-protocol-framework-intro#section3).


### Background: Noise-KN

The [Noise protocol framework](https://noiseprotocol.org/noise.html)
defines a suite of handhake protocols based on Diffie-Hellman key exchange.
In the "KN" handshake, the long-term public key of the initiator
(ie, the Matrix client) is known to the other party ("K"), while
the responder (ie, the homeserver) has no long-term key ("N").

In order for client Alice to authenticate to server Bob, the two
of them must have previously configured her account, so that Bob
knows her long-term public key `A`.

1. Alice sends her identifier (ie her username, or her Matrix
   `user_id`, or her long-term public key, etc) to Bob.

2. Bob looks up the public key `X` that he stored when Alice created
   her account.
   He generates an ephemeral key pair `y` and `Y`.
   He sends his ephemeral public key `Y` to Alice.

3. Alice generates an ephemeral key pair `x` and `X`.
   She sends her ephemeral public key `X` to Bob.

4. Both parties compute two Diffie-Hellman shared secrets.

  * The combination of Alice's ephemeral keypair with Bob's ephemeral keypair.
    Alice computes `SS1 = DH(x,Y)` and Bob computes `SS1 = DH(y,X)`.
    They both arrive at the same value because `DH(x,Y) == DH(y,X)`.

  * The combination of Alice's long-term keypair with Bob's ephemeral keypair.
    Alice computes `SS2 = DH(a,Y)` and Bob computes `SS2 = DH(y,A)`.
    They both arrive at the same value because `DH(a,Y) == DH(y,A)`.

5. They compute a secret key as a hash of their identifiers and
   the two shared secrets.


### Background: EKE and SPEKE

The key contribution of earlier EKE-based protocols was to use the
password itself to define the algebraic group over which the Diffie-Hellman
operations are performed.

For example, in SPEKE, Alice and Bob perform a mostly-standard
Diffie-Hellman key exchange in a multiplicative group of the integers
modulo a large prime.
But instead of using a fixed generator, e.g. `g = 2`, SPEKE derives
its generator from a hash of the user's password.
Thus, an adversary in the network who does not know the password
cannot even begin to launch a man-in-the-middle attack, because
he does not know the group parameters.

BS-SPEKE uses a similar trick.
It derives the base point for its elliptic curve Diffie-Hellman
group from an *oblivious PRF* of the user's password and a secret
salt known only to the server.


### Background: Oblivious PRF (OPRF)

A pseudorandom function (PRF) is like a keyed hash.
It allows anyone who knows a secret key `k` to compute the 
function `F(k, m)` for any message `m`.
An *oblivious* PRF (OPRF) allows two parties to compute the
function, where one party holds the key `k` and the other
party holds the message `m`, without either party revealing
their input to the other.

In BS-SPEKE's usage of the OPRF, the server holds a unique
(secret) salt for each user, and the client holds the user's
password.

BS-SPEKE uses a modified version of the Diffie-Hellman OPRF
that was originally proposed as part of the OPAQUE protocol.
The only difference is a change in the blinding mechanism to
work with elliptic curves rather than "classical" D-H groups.

The OPRF uses two hash functions:
* `H1 : {0|1}^* --> C` where `C` is the set of points on the curve.
* `H2 : {0|1}^* --> {0|1}^L` where `L` is the bit width, e.g. 256 bits for Curve25519

1. Alice hashes her password to a point `p` on the curve.
   Then she generates a large random integer `r` and multiplies
   her curve point by `r`.
   She does this in order to prevent dictionary attacks on `p`.
   ```
   p = H1( password )
   r = random()
   R1 = r * p
   ```
   She sends `R1` to Bob.

2. Bob receives `R1`.  He multiplies his secret salt by `R1`
   and returns the product `R2` to Alice.
   ```
   R2 = salt * R1
   ```

3. Alice removes the blinding by multiplying `R2` by the 
   (integer, mod N) multiplicative inverse of her original
   random blind `r`.
   ```
   S = (1/r) * R2
   ```

   This has the effect of setting `S = salt * H1( password )`,
   because `r` and `(1/r)` cancel each other out.

4. Finally, Alice computes the output of the OPRF as the 
   hash of her password with the salt `S`.
   ```
   F(salt, password) = H2( password | S )
   ```

The server learns nothing about her password, and Alice
has learned nothing about the server's salt.

Additionally, BS-SPEKE specifies that `H2()` should be a
password hashing function (PHF), such as bcrypt, scrypt,
PBDKF2, or Argon2.


### Putting the pieces together: BS-SPEKE with Curve25519

In this section, we put the component pieces together to
show the full BS-SPEKE protocol -- although still in a 
somewhat abstract form.

Note that some messages in BS-SPEKE combine parts of the
OPRF with parts of the handshake protocol; this is done
in order to achieve the whole thing in only two round-trips.

BS-SPEKE uses three hash functions:
* `H()` - a traditional cryptographic hash function
* `HashToCurve()` - a hash function that maps scalars to
points on the elliptic curve.
* `PHF()` - a password hashing function

1. Alice hashes her password to a point on the curve,
   and she "blinds" this point by multiplying by a random
   scalar value `r`.
   ```
   r = random()
   R = r * HashToCurve( password | Alice | Bob )
   ```

   Here she includes the identities of the two participants
   in the hash in order to prevent [message replay attacks](https://blogs.ncl.ac.uk/security/2014/09/29/the-speke-protocol-revisited/).

   She sends `R`, along with her identifier (username,
   `user_id`, etc), to Bob.

2. Bob provides his contribution to the OPRF by multiplying
   his salt `s` by the blinded point `R`.
   He also looks up the base point `P` for user Alice, and
   he uses `P` to generate an ephemeral keypair `b` and `B`.
   ```
   R_prime = s * R
   b = random()
   P = LookupBasePoint(Alice)
   settings = LookupSettings(Alice)
   B = b * P
   ```

   Bob sends `R_prime` and `B` back to Alice, along with the
   settings that Alice should use with the password hashing
   function in the next step.

3. Alice removes the blind `r` from `R_prime` by multiplying
   by the integer multiplicative inverse of `r`.
   ```
   S = (1/r) * R_prime
   ```

   She then uses the un-blinded oblivious salt `S` to derive a
   salt to use with the password hashing function.
   Again, she includes the identities of the participants in
   the computation to prevent messages from one instance of the
   protocol being used in a replay attack on another instance.

   ```
   phf_salt = H( S | Alice | Bob )
   p, v = PHF(password, S)
   ```

   She uses the output from the password hashing function to
   derive her long-term keypair.
   `p` determines the base point `P` on the curve.
   And `v` is her long-term private key.
   She uses these to derive her long-term public key `V`.
   ```
   P = HashToCurve(p)
   V = v * P
   ```

   Note that the server Bob should already have a copy of 
   `P` and `V`, provided to him when Alice originally set
   her current password.
   For details on how this works in Matrix, see [Registration](#registration)
   and [Changing Passwords](#changing-passwords).

   At this point, Alice also generates her ephemeral keypair
   `a` and `A`.

   ```
   a = random()
   A = a * P
   ```

   Now she is ready to compute her version of the shared secret key.

   ```
   K_c = H( Alice | Bob | A | B | a * B | v * B )
   ```

   In order to prove to Bob that she has derived the correct key,
   she uses that key to generate a hash that Bob can verify.

   ```
   verifier_C = H( K_c | "client" )
   ```

   She sends her ephemeral public key `A` and the verifier hash to Bob.

4. Bob computes his own local version of the key

   ```
   K_s = H( Alice | Bob | A | B | b * A | b * V )
   ```

   He verifies the hash that Alice sent, using his own version of the key.
   If the protocol was successful, and `K_s == K_c`, then his version of
   the hash will match what Alice sent.

   ```
   H( K_s | "client") == verifier_C
   ```

   He generates a similar hash that Alice can use to verify him.

   ```
   verifier_S = H( K_s | "server" )
   ```

   He sends `verifier_S` back to Alice.
   Alice is now logged in on the server.

5. Alice performs one last check to make sure the authentication
   was successful.
   She computes her own version of Bob's hash, and checks that it
   matches what was sent from Bob.

   ```
   H( K_c | "server") == verifier_S
   ```

