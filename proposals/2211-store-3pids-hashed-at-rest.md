# Identity Servers Storing Threepids Hashed at Rest

The purpose of an identity server is to store mappings between third-party
identities (3PIDs) and Matrix User IDs. This allows users to associate an
email or a phone number with their Matrix account, for the purpose of letting
people who already know their phone number/email address find them on Matrix.

Since the inception of identity servers, 3PIDs have always been stored as
plaintext addresses. Due to protocol endpoints requiring plaintext addresses,
major implementations have always stored 3PID data as plaintext at rest. An example is the [GET /_matrix/identity/api/v1/3pid/getValidated3pid](https://matrix.org/docs/spec/identity_service/unstable#get-matrix-identity-api-v1-3pid-getvalidated3pid) endpoint, which accepts a lookups by users sending over plaintext 3PIDs, and thus the
identity server needs to store those plaintext values in order to compare
them.

Plaintext 3PIDs are a massive liability. If the database of the identity
server is ever compromised, 3PID addresses and mediums, as well as the Matrix
IDs they are associated with, are immediately compromised. If 3PIDs were
stored as hashes, attackers would need to first build a rainbow table to
reverse them, significantly increasing the expense of compromising user's
personal information.

Through protocol changes we can rectify this situation. As recently done with
[GET
/_matrix/identity/api/v1/lookup](https://matrix.org/docs/spec/identity_service/unstable#get-matrix-identity-api-v1-lookup),
endpoints can be modified to only accept hashes.

## Proposal

The following endpoints would need to be modified for identity servers to be able to store 3PID hashes at rest:

* [POST /_matrix/identity/api/v1/validate/email/requestToken](https://matrix.org/docs/spec/identity_service/unstable#post-matrix-identity-api-v1-validate-email-requesttoken)

This endpoint needs a plaintext 3PID to send an email, but while waiting it can store the address hashed.

* [GET /_matrix/identity/api/v1/3pid/getValidated3pid](https://matrix.org/docs/spec/identity_service/unstable#get-matrix-identity-api-v1-3pid-getvalidated3pid)

This endpoint needs to be changed to return a hash instead of `medium` and `address` parameters.

* [POST /_matrix/identity/api/v1/3pid/unbind](https://matrix.org/docs/spec/identity_service/unstable#post-matrix-identity-api-v1-3pid-unbind)

This endpoint needs to be changed to have `threepid` be a hash instead.

* [POST /_matrix/identity/api/v1/store-invite](https://matrix.org/docs/spec/identity_service/unstable#post-matrix-identity-api-v1-store-invite) 

This endpoint needs to be changed to remove parameters `medium`, and `address`, and instead just have a new field containing a hash value.

Each of these endpoints will need to be changed to `v2`, and at the same time
we should drop the `/api/` part, since it's redundant (we know this is an
API). This lines up with what was done for `/_matrix/identity/v2/lookup` in
[MSC2134](https://github.com/matrix-org/matrix-doc/pull/2134).

Thus, the new endpoints should be:

* POST /_matrix/identity/v2/validate/email/requestToken
* POST /_matrix/identity/v2/3pid/unbind
* POST /_matrix/identity/v2/store-invite
* GET /_matrix/identity/v2/3pid/getValidated3pid

The last could probably be argued that it should be `GET
/_matrix/identity/v2/3pid/getValidated` instead.

The `v1` versions of these endpoints should continue to work but be
deprecated, and eventually removed once clients/identity servers have
sufficiently implemented them.

Endpoints that would already work are:

* [GET/POST /_matrix/identity/api/v1/validate/(email|phone)/submitToken](https://matrix.org/docs/spec/identity_service/unstable#post-matrix-identity-api-v1-validate-email-submittoken)
* [POST /_matrix/identity/api/v1/3pid/bind](https://matrix.org/docs/spec/identity_service/unstable#post-matrix-identity-api-v1-3pid-bind)

These endpoints just take token/session information, so no changes are needed.

## Tradeoffs

There's still the GDPR concern that if an identity server does get
compromised, the administrators are obligated to notify everyone that hashes
were taken. Either Matrix can be used as the communication medium (does the
law disallow this?) or identity servers send a message to Homeservers who do
have the plaintext 3PIDs that they should send an email (this could be
horribly abused by an evil IS though, and not all homeservers have email
settings configured).

## Potential issues

Another sticking point to consider is identity servers that hook into
third-party data sources, such as LDAP, may have trouble answering requests
that only feature a hash value. This may be solvable in implementation but
requires futher thought.

## Conclusion

With a few endpoint changes, we can enable identity servers to store user
contact information in a hashed format, thereby reducing the impact of a
compromised database.

While it can be argued that these hashes could be reversed, doing so is more
effort for an attacker than simply gleaming a large database of plaintext
addresses.
