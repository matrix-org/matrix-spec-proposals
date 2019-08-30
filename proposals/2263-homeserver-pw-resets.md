# MSC2263: Give homeservers the ability to handle their own 3PID registrations/password resets

In order to better protect the privacy of a user, Matrix is wanting to shift to
a model where identity servers have less control over the affairs of the homeserver.
Identity servers are currently used to reset the passwords of users on a given homeserver
as an identity verification technique, however there is no reason why the homeserver
itself can't handle the verification. This proposal allows for a homeserver to verify
the identity of users itself, without the use of an identity server.

## Proposal

The `id_server` parameter is to become optional on the following endpoints:

* `/_matrix/client/:version/account/3pid/:medium/requestToken`
* `/_matrix/client/:version/register/:medium/requestToken`
* `/_matrix/client/:version/account/password/:medium/requestToken`

The `id_server` parameter is additionally deprecated with intention of being removed
in a future specification release on the `/register/:medium` and `/account/password/:medium`
endpoints. Once appropriate adoption has been achieved, the specification can safely
remove the parameter as supported. The reason for this deprecation is to completely
remove the identity server's ability to be involved in password resets/registration.
Users wishing to bind their 3rd party identifiers can do so after registration, and
clients can automate this if they so desire.

Note that `bind_email` and `bind_msisdn` on `/register` have already been removed
by [MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140).

As per [MSC2140](https://github.com/matrix-org/matrix-doc/pull/2140), an `id_access_token`
is required only if an `id_server` is supplied.

Although not specified as required in the specification currently, the `id_server`
as part of User-Interactive Authentication is also optional if this proposal is accepted.
When the client requests a token without an `id_server`, it should not specify an
`id_server` in UIA.

Homeservers can reuse HTTP 400 `M_SERVER_NOT_TRUSTED` as an error code on the `/requestToken`
endpoints listed above if they do not trust the identity server the user is supplying.

In order to allow client implementations to determine if the homeserver they are developed
against supports `id_server` being optional, an unstable feature flag of `m.require_identity_server`
is to be added to `/versions`. When the flag is `true` or not present, clients must assume
that the homeserver requires an `id_server` (ie: it has not yet considered it optional).
If this proposal is accepted, clients are expected to use the supported specification versions
the homeserver advertises instead of the feature flag's presence.

## Tradeoffs

Homeservers may have to set up MSISDN/email support to their implementations. This is believed
to be of minimal risk compared to allowing the identity server to continue being involved
with password reset/registration.

## Security considerations

The identity server was previously involved with affairs only the homeserver cares about.
This is no longer the case.
