# MSCxxxx: Support for Flexible Authentication

In the Matrix client-server API, the `/login` endpoint allows the client
to specify which authentication mechanism should be used to log the user
in, e.g. `"type": "m.login.password"`.
However, the CS API lacks a way to set up other authenticators for the
user beyond a simple password.

This proposal describes changes to the CS API to enable clients to
configure other authentication methods, for both new and existing accounts.
The changes proposed here would be required for improving the security of
Matrix's login in various ways, for example by using cryptographic password
authentication protocols
([MSC3726](https://github.com/matrix-org/matrix-doc/pull/3726))
or by adding support two-factor authentication (e.g.
[MSC1998](https://github.com/matrix-org/matrix-doc/pull/1998))
to be used alongside the traditional `m.login.password`.

## Proposal

### No change to `POST /login`
The `/login` API endpoint already supports authentication types beyond just
`m.login.password`.

### Changes to `POST /register`

Instead of sending the user's password as a top-level element of the JSON body,
the client should now provide a dictionary of authenticators for the login type(s)
that the user wishes to use.
The keys of the dictionary are authentication types, e.g. `m.login.password`,
and the values are the authenticator data.
The contents of the authenticator data will vary from one authentication
type to the next.

For example, to register an account that will use traditional password login,
the JSON body from the CS API documentation becomes:

```json
{
  "auth": {
    "example_credential": "verypoorsharedsecret",
    "session": "xxxxx",
    "type": "example.type.foo"
  },
  "device_id": "GHTYAJCE",
  "initial_device_display_name": "Jungle Phone",
  "username": "cheeky_monkey"
  "authenticators": {
    "m.login.password": {
      "password": "ilovebananas",
    }
  }
}
```

As another example, consider the BS-SPEKE protocol in [MSC3726](https://github.com/matrix-org/matrix-doc/pull/3726).
There, the server needs to know the user's base elliptic curve point
`P`, their public key `V`, and their parameters for the password hashing
function (PHF).
To register a user with only BS-SPEKE authentication, the JSON body might be:

```json
{
  "auth": {
    "example_credential": "verypoorsharedsecret",
    "session": "xxxxx",
    "type": "example.type.foo"
  },
  "device_id": "GHTYAJCE",
  "initial_device_display_name": "Jungle Phone",
  "username": "cheeky_monkey"
  "authenticators": {
    "m.login.bsspeke.ecc": {
      "P": "<user's base64-encoded curve25519 base point>",
      "V": "<user's base64-encoded long-term curve25519 public key>",
      "phf_params": {
        "name": "argon2i",
        "blocks": 100000,
        "iterations": 3,
      },
    }
  }
}
```

### New `GET /register` endpoint
The client also needs some way to know which authenticators are supported
by the server.
The proposed approach is to add a new `GET` method for `/register`, similar
to what is already done for `/login`.
The server responds with a list of the supported authentication types.

```json
{
  "auth_types": [
      "m.login.password",
  ]
}
```


### Deprecation of the old `/account/password` endpoint

Under this proposal, the `/account/password` endpoint would be deprecated
in favor of the new, more general `account/authenticator` endpoint described
below.

### New `POST /account/authenticator` endpoint

This replaces the old `/account/password` endpoint with a more flexible
version that can handle more different types of authenticators.

The request body should contain a dictionary of authenticators, where the
keys are authentication types, e.g. `m.login.password`, and the values
are the authenticator data.
The contents of the authenticator data will vary from one authentication
type to the next.

For example, for traditional password authentication:

`POST /account/authenticator`

```json
{
    "m.login.password": {
        "password": "<user's login password>"
    },

}
```

As another example, consider the BS-SPEKE protocol in MSC3726.
There, the server needs to know the user's base elliptic curve point
`P`, their public key `V`, and their parameters for the password hashing
function (PHF).
Setting up a user to log in with BS-SPEKE might look like this:

`POST /account/authenticator`

```json
{
    "m.login.bsspeke.ecc": {
        "P": "<user's base64-encoded curve25519 base point>",
        "V": "<user's base64-encoded long-term curve25519 public key>",
        "phf_params": {
            "name": "argon2i",
            "blocks": 100000,
            "iterations": 3,
        },
    },
}
```

**NOTE:** Just like the old `/account/password` endpoint, the new
`/account/authenticator` endpoint requires user-interactive authentication.
Cryptographic authentication mechanisms, such as BS-SPEKE or Webauthn,
typically require multiple rounds of communication between client and
server in order to set up a new authenticator for the user.
These protocols can use a UIA stage to implement the initial round(s)
of their setup ceremony.
Servers that wish to support these protocols then MUST include those
UIA stages in the UIA flows for this endpoint.

### New `DELETE /account/authenticator/<auth_type>/<authenticator_id>` endpoint

To un-register an authenticator, the client calls

```
DELETE /account/authenticator/auth_type
```

For example,

```
DELETE /account/authenticator/m.login.password
```

Some authentication mechanisms allow the user to configure multiple
authenticators of the same type.
For example, with WebAuthn, a user might have two FIDO2 keys, Apple
TouchID, and Apple FaceID.
Each of these authenticators should have a unique identifier.
If the `auth_type` for WebAuthn is `m.login.webauthn`, and one of the
WebAuthn authenticators has id `abcdwxyz`, then the client can remove
the authenticator, leaving all other WebAuthn authenticators intact,
by calling

```
DELETE /account/authenticator/m.login.webauthn/abcdwxyz
```





## Potential issues

**Backwards compatibility.**
For the immediate future, servers should continue to accept the old style requests.

* For `/register`, if the request's JSON body does not include an
  `authenticators` object, the server should look for an old style
  `password`.

* Requests for `POST /account/password` should be treated as an alias
  for `POST /account/authenticator` with a type of `m.login.password`.


## Alternatives

**OpenID Connect.**
Rather than implementing more authentication types in the Matrix CS 
API, Matrix could switch to using OpenID Connect.
Then all the complexity of handling different authentication mechanisms
is pushed out into the OIDC Provider.

OIDC might be the proper direction to go in the long run.
But for now, as a stop-gap measure, we can build better security using
the building blocks that we have in the existing CS API.
Also, some installations may not want to depend on a third party OIDC
Provider for a foundational thing like authentication; this proposal
provides a way for such homeservers to achieve better security with no
third parties.

## Security considerations
1. Two-factor authentication is quickly becoming a baseline requirement
  for many organizations.
  This proposal provides an important step toward enabling two-factor auth
  in Matrix, without the need for integrating with any external system.

2. Any proposal for authenticating users with a cryptographic protocol
  will need some way for the client to register the user's authenticators
  for that protocol on the server.
  This proposal provides that mechanism.

3. The approach proposed here would allow clients to configure multiple
  password-based authentication mechanisms for a single user, for example,
  `m.login.password` and a cryptographic password authentication protocol
  such as MSC3726.
  If the user sets the same password for both authentication mechanisms,
  then much of the security benefit of the cryptographic login is lost.

  * Clients should not automatically register both types of authenticators
    from a single password, and they should take some care to detect when
    a user chooses to set the same password for both types of auth.

  * Note that this is not *always* bad.
    For example, if the user started with the legacy `m.login.password` auth,
    then it is probably better to allow them to upgrade to a more secure
    auth scheme, even if they don't make the optimal choice of also setting
    a new password when they upgrade.

  * On the other hand, if a user is already set up for cryptographic login,
    and they attempt to set up `m.login.password` using the same password,
    then the client should do its best to alert them of the risk.
    Perhaps the downgrade functionality should be hidden behind some sort
    of "advanced options", and/or disabled by default.
  


## Potential issues

???



## Unstable prefix

TBD

## Dependencies

None
