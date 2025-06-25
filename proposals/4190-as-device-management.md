# MSC4190: Device management for application services

[MSC3202] allows application services to handle and send encrypted events.
One part of [MSC3202] is the ability to masquerade devices using the `device_id`
query parameter on C-S API requests, which eliminates the need to maintain
individual access tokens for each application service user.

However, application services don't have an endpoint to create devices for their
users, which means that, in practice, encrypted application services still use
`/login` with the `m.login.application_service` login type to create devices for
their users.

Consequently, such application services leave many unused but active access
tokens for those users.

Furthermore, if [MSC3861] were adopted, the `/login` endpoint would no longer be
available for application services to use.

This MSC proposes a dedicated API endpoint for application services to create
and delete devices for users, addressing the existing gap to enable encrypted
application services without `/login`.

## Proposal

This MSC proposes to extend existing endpoints to allow application services to
create and delete devices for their users without relying on the `/login` and
`/logout` mechanisms.

As all changes here only apply to application services, guest access is not
relevant.

### **`PUT /_matrix/client/v3/devices/{deviceId}`**

This endpoint is updated to allow the creation of a new device for a user, if
the device ID does not exist. This behavior is only available to application
services.

This endpoint will use the 201 status code to indicate that a new device was
created, in addition to the existing 200 status code for existing devices.

The endpoint is rate limited. Servers may want to use login rate limits for
device creation, although in most cases application services will disable all
rate limits anyway.

### **`DELETE /_matrix/client/v3/devices/{deviceId}`**

This endpoint no longer requires User-Interactive Authentication for application services.

### **`POST /_matrix/client/v3/delete_devices`**

This endpoint no longer requires User-Interactive Authentication for application services.

### **`POST /_matrix/client/v3/register`**

Currently, the default behavior for `/register` is to create a new device and
access token (i.e. login) in addition to creating the user. Similar to `/login`,
creating an access token would no longer be possible with [MSC3861]. However,
creating users via the endpoint is still required, so unlike `/login`, `/register`
will not be removed entirely.

Therefore, application services MUST call the endpoint with `inhibit_login=true`.
Calls without the parameter, or with a different value than `true`, will return
HTTP 400 with a new `M_APPSERVICE_LOGIN_UNSUPPORTED` error code.

## Potential issues

The change to `/v3/register` is technically backwards-incompatible, but it will
break when switching to next-gen auth in any case, so a new endpoint version
would not be useful.

The endpoint could just stop returning access tokens to avoid breaking existing
appservices that don't read that field, but an explicit error was chosen to
avoid silent breakage of appservices that do depend on the field.

## Security considerations

This MSC lets application services delete devices without the usual
re-authentication requirement. It is considered an acceptable risk, as
application services have to be registered by the server admin.

## Alternatives

A new set of endpoints dedicated to application services could be added to the
specification, like `GET|PUT|DELETE /_matrix/client/v3/appservices/{appId}/devices/{deviceId}`.

This would have the advantage of not changing the behavior of existing endpoints.

## Dependencies

None. While this MSC is meant for next-gen auth, it can be used independently.

## Unstable prefix

Until this MSC is stable, application services must opt-in to the new behavior
by setting the `io.element.msc4190` flag to `true` in their registration file.

[MSC3202]: https://github.com/matrix-org/matrix-spec-proposals/pull/3202
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
