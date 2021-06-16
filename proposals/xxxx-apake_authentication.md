# \[WIP]MSCXXXX: aPAKE authentication

Like most password authentication, matrix's [login](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-login) requires sending the password in plain text (though usually encrypted in transit with https). This requirement has as (obvious) downside that a man in the middle attack would allow reading the password, but also requires that the server has temporary access to the plaintext password (which will subsequently be hashed before storage).

A Password Authenticated Key Exchange (PAKE) can prevent the need for sending the password in plaintext for login, and an aPAKE (asymmetric or augmented) allows for safe authentication without the server ever needing access to the plaintext password. OPAQUE is a modern implementation of an aPAKE that is [currently an ietf draft](https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-opaque-05), but as it's still pending and doesn't have many open source implementations using it would require implementing it ourselves. As such choosing to use SRP ([rfc2945](https://datatracker.ietf.org/doc/html/rfc2945)) makes more sense. SRP has as downside that the salt is transmitted to the client before authentication, allowing a precomputation attack which would speed up a followup attack after a server compromise. However, should a server be compromised, it is probably simpler to generate an access token and impersonate the target that way.

## Proposal

Add support for the SRP 6a login flow, as `"type": "m.login.srp6a"`.

### Login flow

To start the login flow the client sends it's username to obtain the salt and SRP group as:

`POST /_matrix/client/r0/login`
```
{
  "type": "m.login.srp6a.init",
  "username": "cheeky_monkey"
}
```
The server responds with the salt and SRP group:
```
{
  "prime": N,
  "generator": g,
  "salt": s,
  "servervalue": B
}
```
Here N is the prime and g is the generator of the SRP group. s is the stored salt for the user as supplied in the `POST` and B is the public server value.

**TODO:** explain the SRP calculation done clientside and serverside?

The client will then respond with
`POST /_matrix/client/r0/login`
```
{
  "type": "m.login.srp6a.verify",
  "evidencemessage": M1,
  "clientvalue": A
}
```
Here `M1` is the client evidence message, and A is the public client value.
Upon successful authentication the server will respond with the regular login success status code 200:

*We can also prove the identity of the server here by adding M2, probably worth it?*
```
{
  "user_id": "@cheeky_monkey:matrix.org",
  "access_token": "abc123",
  "device_id": "GHTYAJCE",
  "well_known": {
    "m.homeserver": {
      "base_url": "https://example.org"
    },
    "m.identity_server": {
      "base_url": "https://id.example.org"
    }
  }
}
```

## Potential issues

Adding this authentication method requires client developers to implement this in all matrix clients.

SRP is vulnerable to precomputation attacks and it is incompatible elliptic-curve cryptography.
Matthew Green judges it as ["It’s not ideal, but it’s real." and "not obviously broken"](https://blog.cryptographyengineering.com/2018/10/19/lets-talk-about-pake/) and it's a fairly old protocol.

## Alternatives

OPAQUE is the more modern protocol, which has the added benefit of not sending the salt in plain text to the client, but rather uses an 'Oblivious Pseudo-Random Function' and can use elliptic curves.

*Bitwardens scheme can be mentioned here as well, since it does allow auth without the server learning the plaintext password, but it isn't a PAKE, but rather something along the lines of a hash of the password before sending the has to the server for auth, practically making the hash the new password, and as such it doesn't protect against a mitm.*


## Security considerations

Probably loads, though SRP and OPAQUE have had lots of eyes, I would assume.

## Unstable prefix


