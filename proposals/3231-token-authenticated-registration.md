# MSC3231: Token Authenticated Registration

Currently, homeserver administrators must choose between allowing anyone to
register and completely disabling registrations. This is a problem for
administrators who want to let certain people have an account on their server,
but do not want to register the accounts manually (possibly because the
initial password may not be changed by the user).

There are some existing external solutions (see the **Alternatives** section),
but these require additional effort from administrators and are disconnected
from Matrix clients. It would be useful for administrators to have a convenient
method of limiting registrations to certain people which requires minimal setup
and is integrated with existing clients.

## Proposal

The [/\_matrix/client/r0/register](https://spec.matrix.org/unstable/client-server-api/#post_matrixclientr0register)
endpoint uses the [User-Interactive Authentication API](https://spec.matrix.org/unstable/client-server-api/#user-interactive-authentication-api).
A new authentication type `m.registration.token` will be defined which requires
a `token` key to be present in the submitted `auth` dict. The token will be a
string which the homeserver can match against its records to authenticate the
registration request.

For example, when a client attempts registration with no `auth` dict, a server
may respond with:

```
HTTP/1.1 401 Unauthorized

{
	"flows": [
		{
			"stages": [ "m.registration.token" ]
		}
	],
	"params": {},
	"session": "xxxxx"
}
```

The client would then prompt the user to enter a token and send a new request
with an `auth` dict:

```
POST /_matrix/client/r0/register

{
	"auth": {
		"type": "m.registration.token",
		"token": "fBVFdqVE",
		"session": "xxxxx"
	}
	"device_id": "ABC",
	"initial_device_display_name": "Some Client",
	"password": "badpassword",
	"username": "bob"
}
```

If the server verifies that `fBVFdqVE` is a valid token then the account is
registered as normal, otherwise a `401` status is returned. On the successful
use of a token the server may alter the validity of the token. For example, the
token may be completely invalidated, or its number of permitted uses reduced.
Management of the tokens is left to the server implementation.

Using the User-Interactive Authentication API means clients' existing
registration logic will be unaffected, with a fallback available for clients
without native support for the new authentication type.


## Potential issues

The new authentication type would only apply to the
`/_matrix/client/r0/register` endpoint. This should not cause problems, but it
would be worth noting in any change to the specification.


## Alternatives

[matrix-registration](https://github.com/ZerataX/matrix-registration/) is an
application which provides token management and a standalone web interface.
It uses Synapse's admin API to do registrations.

[Midnight](https://github.com/KombuchaPrivacy/midnight) sits in front of a
homeserver and handles the `/_matrix/client/r0/register` endpoint. It provides
token management and does additional checks on the requested username.
Registration requests are forwarded to the homeserver once authenticated.
It uses the User-Interactive Authentication API in a very similar way to this
MSC, which could allow existing Matrix clients to be used.

[matrix-register-bot](https://github.com/krombel/matrix-register-bot) is a
Matrix bot which allows registrations done through the provided web interface
to be accepted or denied by users in a certain room. When a registration is
approved temporary credentials are sent to the user's verified email address.
It can use Synapse's admin API or [matrix-synapse-rest-auth](https://github.com/kamax-matrix/matrix-synapse-rest-password-provider#integrate)
to do the registration.


## Unstable prefix

Implementations should use `org.matrix.msc3231.registration.token` as the
authentication type until this MSC is part of a released version of the
specification.
