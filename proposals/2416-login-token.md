# MSC2416: Enhance m.login.token authentication type
An appservice might want to log in to the homeserver as another user or a system administrator might
want an easy way to authenticating as someone else to be able to investigate an issue. Currently
two solutions for that exist: either using [shared secret auth](https://github.com/devture/matrix-synapse-shared-secret-auth)
or synapses undocumented and unspeced `org.matrix.login.jwt`. Neither solution seems good: The shared secret
auth provider seems like a hack on `m.login.password` and `org.matrix.login.jwt` is neither documented nor
speced. Instead, it is proposed to add a new type of token allowed to the `m.login.token` type.

## Proposal
The proposal adds JWTs ([Json Web Token](https://jwt.io/)) to the authentication type `m.login.token`.
It is expected that the tokens are signed by a secret key. The algorithm of the JWT can be
configured by the homeserver. As this endpoint is meant to be used by automated processes like
application services there is no need to provide a mechanism to generate such tokens for clients.
A homeserver may enforce the presence of the `exp` claim. Whether to register new users via this
endpoint or not is up to the homeserver. The `sub` claim is to be either the localpart or the full
mxid of the user to identify as.

An example JWT could look as follows:

Header:
```json
{
  "alg": "HS512",
  "typ": "JWT"
}
```

Payload:
```json
{
  "sub": "alice",
  "exp": 1579373788
}
```

A POST request to the `/_matrix/client/r0/login` endpoint could look as follows:
```json
{
  "type": "m.login.token",
  "token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsImV4cCI6MTU3OTM3Mzc4OH0.4YXhRYNfzdns8qf60fE7pu9RKFt3uhxqj6y-Gy4d2bbDkQ5-mTbTNgDdi350ZMrY5VV22WHp_-BOjtGFkwOqgA"
}
```

## Potential Issues
The homeserver implementation might have to implement multiple token validators. If one successfully
validates that token, that one should be used. Compareable to synapses auth providers.

## Alternatives
A `m.login.password` auth provider could be used to log in as someone as a special user. This,
however, feels rather hacky and not the intended purpose of `m.login.password`.

Synapses `org.matrix.login.jwt` could be introduced properly in the spec as `m.login.jwt`, however,
as it seems to be identical to `m.login.token` it makes sense to merge it into `m.login.token`.
(Note: Only got a very weak opinion on this, can also see arguments for the two being separate and
would gladly adapt the MSC, if wanted)

## Security considerations
Possession of the secret allows you to be logged in as anyone on that homeserver. As such, this
secret has to be kept securely.
