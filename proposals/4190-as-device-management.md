# MSC4190: Device management for application services

[MSC3202] allows application services to handle and send encrypted events.
One part of [MSC3202] is the ability to masquerade devices using the `device_id` query parameter on C-S API requests, which eliminates the need to maintain individual access tokens for each application service user.

However, application services don't have an endpoint to create devices for their users, which means that, in practice, encrypted application services still use `/login` with the `m.login.application_service` login type to create devices for their users.

Consequently, such application services leave many unused but active access tokens for those users.

Furthermore, if [MSC3861] were adopted, the `/login` endpoint would no longer be available for application services to use.

This MSC proposes a dedicated API endpoint for application services to create and delete devices for users, addressing the existing gap to enable encrypted application services without `/login`.

## Proposal

This MSC proposes to extend existing endpoints to allow application services to create and delete devices for their users without relying on the `/login` and `/logout` mechanisms.

### **`PUT /_matrix/client/v3/devices/{deviceId}`**

This endpoint is updated to allow the creation of a new device for a user, if the device ID does not exist.
This behavior is only available to application services.

This endpoint will use the 201 status code to indicate that a new device was created, in addition to the existing 200 status code for existing devices.

### **`DELETE /_matrix/client/v3/devices/{deviceId}`**

This endpoint no longer requires User-Interactive Authentication for application services.

### **`POST /_matrix/client/v3/delete_devices`**

This endpoint no longer requires User-Interactive Authentication for application services.

### **`POST /_matrix/client/v3/register`**

This endpoint no longer generates a new access token, as if `inhibit_login` was set to `true` in the request by default.

## Alternatives

A new set of endpoints dedicated to application services could be added to the specification, like `GET|PUT|DELETE /_matrix/client/v3/appservices/{appId}/devices/{deviceId}`.

This would have the advantage of not changing the behavior of existing endpoints.

## Unstable prefix

Until this MSC is stable, application services must opt-in to the new behavior by setting the `msc4190_device_management` flag to `true` in their registration file.

[MSC3202]: https://github.com/matrix-org/matrix-spec-proposals/pull/3202
[MSC3861]: https://github.com/matrix-org/matrix-spec-proposals/pull/3861
