# Invalidating devices during password modification

There are multiple use cases for why a user might want to modify their password:

* Adopting a password manager (to use a unique password or more secure password).
* Password rotation.
* Re-secure a compromised account.
* ... probably tons of others ...

These can be summarized into two groups:

1. "My account has been compromised and I need to re-secure it."
2. "I just want to change my password."

The [current Matrix specification](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-account-password)
does not provide a way to differentiate between these use cases. It gives no
guidance into what should happen to other sessions / devices when a password is
modified and leaves it up to the implementation.

It is reasonable for a client to want to specify this behavior to offer two
different workflows:

1. Modify a password and log all other devices out (for use when an account has
   been compromised).
2. Modify a password and do not touch any session data (for use in a
   non-malicious situations).

Alternately a client may default to whichever workflow is best for their users.

## Proposal

An optional field is added to the JSON body body of the [password reset endpoint](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-account-password)
called `logout_devices`. This is a boolean flag (defaulting to `true`) that
signals to whether other devices and sessions should be invalidated after
modifying the password.

## Potential issues

The specification states:

> The homeserver SHOULD NOT revoke the access token provided in the request,
> however all other access tokens for the user should be revoked if the request
> succeeds.

Defaulting `logout_devices` to `true` should be backwards compatible.

## Alternatives

A new endpoint could be provided in a future version of the specification that
supports an additional field (as described above).

## Security considerations

By defaulting to invalidating devices and sessions the security considerations
of this endpoint should remain intact. A client will need to be modified to
choose to keep other devices active.
