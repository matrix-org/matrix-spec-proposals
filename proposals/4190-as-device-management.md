# MSC4190: Device management for application services

[MSC4326] gives appservices the ability to masquerade devices using the
`device_id` query parameter on C-S API requests, which eliminates the need to
maintain individual access tokens for each application service user.

However, application services don't have an endpoint to create devices for their
users, which means that, in practice, encrypted application services still use
`/login` with the `m.login.application_service` login type to create devices for
their users.

Consequently, such application services leave many unused but active access
tokens for those users.

Furthermore, the `/login` endpoint is no longer available for application services
to use on servers that have switched to OAuth2 ([MSC3861]).

This MSC proposes a dedicated API endpoint for application services to create
and delete devices for users, addressing the existing gap to enable encrypted
application services without `/login`.

## Proposal

This MSC proposes to extend existing endpoints to allow application services to
create and delete devices for their users without relying on the `/login` and
`/logout` mechanisms.

As all changes here only apply to application services, guest access is not
relevant.

### [**`PUT /_matrix/client/v3/devices/{deviceId}`**](https://spec.matrix.org/v1.16/client-server-api/#put_matrixclientv3devicesdeviceid)

This endpoint is updated to allow the creation of a new device for a user, if
the device ID does not exist. This behavior is only available to application
services.

This endpoint will use the 201 status code to indicate that a new device was
created, in addition to the existing 200 status code for existing devices.

The endpoint is rate limited. Servers may want to use login rate limits for
device creation, although in most cases application services will disable all
rate limits anyway.

### [**`DELETE /_matrix/client/v3/devices/{deviceId}`**](https://spec.matrix.org/v1.16/client-server-api/#delete_matrixclientv3devicesdeviceid)

This endpoint no longer requires User-Interactive Authentication for application services.

### [**`POST /_matrix/client/v3/delete_devices`**](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3delete_devices)

This endpoint no longer requires User-Interactive Authentication for application services.

### [**`POST /_matrix/client/v3/keys/device_signing/upload`**](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3keysdevice_signingupload)

This endpoint no longer requires User-Interactive Authentication for application services,
even if cross-signing keys already exist.

This is not technically a part of device management, but appservices will need
to be able to verify themselves including generating cross-signing keys for
[MSC4153] and replacing cross-signing keys is necessary in some cases (e.g. if
the appservice recovery key is misplaced).

[MSC4153]: https://github.com/matrix-org/matrix-spec-proposals/pull/4153

### [**`POST /_matrix/client/v3/login`**](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3login)

Logins with the [`m.login.application_service` type] will return HTTP 400 with a
new `M_APPSERVICE_LOGIN_UNSUPPORTED` error code if the homeserver has switched
to OAuth2.

[`m.login.application_service` type]: https://spec.matrix.org/v1.16/client-server-api/#appservice-login

### [**`POST /_matrix/client/v3/register`**](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3register)

Currently, the default behavior for `/register` is to create a new device and
access token (i.e. login) in addition to creating the user. Similar to `/login`,
creating an access token is no longer possible on servers that have switched to
OAuth2. However, creating users via the endpoint is still required, so unlike
`/login`, `/register` will not be removed entirely.

Therefore, application services on homeservers that have switched to OAuth2
MUST call the endpoint with `"inhibit_login": true`. Calls without the parameter,
or with a different value than `true`, will return HTTP 400 with the
`M_APPSERVICE_LOGIN_UNSUPPORTED` error code.

## Potential issues

The change to `/v3/register` is technically backwards-incompatible, but it will
break when switching to next-gen auth in any case, so a new endpoint version
would not be useful.

The endpoint could just stop returning access tokens to avoid breaking existing
appservices that don't read that field, but an explicit error was chosen to
avoid silent breakage of appservices that do depend on the field.

The breaking changes to `/login` and `/register` only apply to homeservers which
have switched to OAuth2. Homeservers MAY have implementation-specific methods of
opting into the breaking changes before switching to OAuth2 entirely to test
compatibility.

## Security considerations

This MSC lets application services delete devices and replace cross-signing keys
without the usual re-authentication requirement. It is considered an acceptable
risk, as application services have to be registered by the server admin.

## Alternatives

A new set of endpoints dedicated to application services could be added to the
specification, like `GET|PUT|DELETE /_matrix/client/v3/appservices/{appId}/devices/{deviceId}`.

This would have the advantage of not changing the behavior of existing endpoints.

## Dependencies

In order to use the devices created using this MSC, appservices need to be able
to use device IDs as a part of identity assertion, as defined by [MSC4326].

## Unstable prefix

`IO.ELEMENT.MSC4190.M_APPSERVICE_LOGIN_UNSUPPORTED` should be used as the
error code instead of `M_APPSERVICE_LOGIN_UNSUPPORTED`.

[MSC4326]: https://github.com/matrix-org/matrix-spec-proposals/pull/4326
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
