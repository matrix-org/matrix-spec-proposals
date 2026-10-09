# MSC4369: M_CAPABILITY_NOT_ENABLED error code for when capability is not enabled on an API endpoint

The [capabilities negotiation] feature in the [Client-Server API] provides a mechanism for clients
to discover whether specific capabilities are available to a user.

However, the endpoints that use capabilities do not currently specify what error response a client
should expect if they try to use an API that does not have the capability enabled for the user.

I believe this is an omission in the current spec that should be addressed for existing capabilities
and be checked for future MSCs that use capabilities.

For background: this MSC originates from a
[spec PR](https://github.com/matrix-org/matrix-spec/pull/2212) that has since been closed.

## Proposal

Define a new [other error code] of `M_CAPABILITY_NOT_ENABLED`.

Define the following behaviour for existing API endpoints that use capabilities:

Capability|Endpoint(s)|Current spec|Proposed behaviour
-|-|-|-
[`m.change_password`]|[`POST /_matrix/client/v3/account/password`]|Not defined|Return `403` with `M_CAPABILITY_NOT_ENABLED` if `m.change_password`.`enabled` is `false`
[`m.profile_fields`]|[`PUT /_matrix/client/v3/profile/{userId}/{keyName}`] [`DELETE /_matrix/client/v3/profile/{userId}/{keyName}`]|`403` for `PUT`. Maybe `403` for `DELETE`. Error code not specified for either|Return `403` with `M_CAPABILITY_NOT_ENABLED` if: `m.profile_fields`.`enabled` is `false`; or, `m.profile_fields`.`disallowed` contains `{keyName}`;
[`m.set_displayname`]|As per `m.profile_fields`|As per `m.profile_fields`|Return `403` with `M_CAPABILITY_NOT_ENABLED` if: `m.profile_fields`.`enabled` is `false`; or, `m.profile_fields`.`disallowed` contains `{keyName}`; or, `m.set_displayname`.`enabled` is `false`;
[`m.set_avatar_url`]|As per `m.profile_fields`|As per `m.profile_fields`|Return `403` with `M_CAPABILITY_NOT_ENABLED` if: `m.profile_fields`.`enabled` is `false`; or, `m.profile_fields`.`disallowed` contains `{keyName}`; or, `m.set_avatar_url`.`enabled` is `false`;
[`m.3pid_changes`]|[`POST /_matrix/client/v3/account/3pid`] [`POST /_matrix/client/v3/account/3pid/add`] [`POST /_matrix/client/v3/account/3pid/delete`]|Not defined|Return `403` with `M_CAPABILITY_NOT_ENABLED` if `m.3pid_changes`.`enabled` is `false`
[`m.get_login_token`]|[`POST /_matrix/client/v1/login/get_token`]|Maybe `400` with undefined error code if `m.get_login_token`.`enabled` is `false`|`403` with `M_CAPABILITY_NOT_ENABLED` if `m.get_login_token`.`enabled` is `false`

## Potential issues

### Possible change in behaviour on `m.get_login_token`

The spec for [`POST /_matrix/client/v1/login/get_token`] says:

> **Status** 400
> The request was malformed, or the user does not have an ability to generate tokens for their devices, as implied by
> the User-Interactive Authentication API.
> Clients should verify whether the user has an ability to call this endpoint with the m.get_login_token capability.

So, it doesn't explicitly say that `400` is the expected response if the capability is not available to the user. But,
it might imply it and it is possible that some implementations might rely on this.

However, a mitigation is that since [`POST /_matrix/client/v1/login/get_token`] was introduced by [MSC3882] it has
always had a capability associated with it and so clients should know to check the capability in advance.

### Changes from implementations in the wild

This is what Synapse currently returns:

Endpoint(s)|Synapse current
-|-
[`POST /_matrix/client/v3/account/password`]|`403` with `M_FORBIDDEN`
[`PUT /_matrix/client/v3/profile/{userId}/{keyName}`] [`DELETE /_matrix/client/v3/profile/{userId}/{keyName}`]|`400` with `M_FORBIDDEN`
[`POST /_matrix/client/v3/account/3pid`] [`POST /_matrix/client/v3/account/3pid/add`] [`POST /_matrix/client/v3/account/3pid/delete`]|`400` with `M_FORBIDDEN`
[`POST /_matrix/client/v1/login/get_token`]|`404` with `M_UNRECOGNIZED`

The [`POST /_matrix/client/v1/login/get_token`] one is interesting as it suggests that the `400` from the previous
section isn't used in the wild.

## Alternatives

### Codify existing Synapse behaviour

We could simply codify what is in the existing Synapse implementation (see above). This is what was originally proposed
in https://github.com/matrix-org/matrix-spec/pull/2212.

However, that doesn't consider non-Synapse implementations.

### Increment version on affected endpoints

Deprecate the old version and introduce a new version with the updated error responses.

e.g.
`POST /_matrix/client/`**`v3`**`/account/password` would be deprecated and continue to return `403` with `M_FORBIDDEN` and
`POST /_matrix/client/`**`v4`**`/account/password` would return `403` with `M_CAPABILITY_NOT_ENABLED`

### Allow client to specify versions

Perhaps this has been discussed elsewhere previously, but clients could specify a spec version alongside each request
(perhaps in an HTTP header) and the server used that to determine what error code to return.

e.g.

```http
POST /_matrix/client/v3/account/password
Host: example.com
Matrix-Version: v1.16
```

Would return `403` with `M_FORBIDDEN`. But if a later version specified then the new error code is given:

```http
POST /_matrix/client/v3/account/password
Host: example.com
Matrix-Version: v1.17
```

Could return `403` with `M_CAPABILITY_NOT_ENABLED`.

That way clients effectively opt-in to the change in format.

## Security considerations

None.

## Unstable prefix

Whilst this proposal is under development the `IO.ELEMENT.MSC4369_CAPABILITY_NOT_ENABLED` value
should be used instead of `CAPABILITY_NOT_ENABLED`.

## Dependencies

None.

[capabilities negotiation]: https://spec.matrix.org/v1.16/client-server-api/#capabilities-negotiation
[Client-Server API]: https://spec.matrix.org/v1.16/client-server-api/
[other error code]: https://spec.matrix.org/v1.16/client-server-api/#other-error-codes
[MSC3882]: https://github.com/matrix-org/matrix-spec-proposals/pull/3882
[`m.change_password`]: https://spec.matrix.org/v1.16/client-server-api/#mchange_password-capability
[`m.profile_fields`]: https://spec.matrix.org/v1.16/client-server-api/#mprofile_fields-capability
[`m.set_displayname`]: https://spec.matrix.org/v1.16/client-server-api/#mset_displayname-capability
[`m.set_avatar_url`]: https://spec.matrix.org/v1.16/client-server-api/#mset_avatar_url-capability
[`m.3pid_changes`]: https://spec.matrix.org/v1.16/client-server-api/#m3pid_changes-capability
[`m.get_login_token`]: https://spec.matrix.org/v1.16/client-server-api/#mget_login_token-capability
[`POST /_matrix/client/v3/account/password`]: https://pr2212--matrix-spec-previews.netlify.app/client-server-api/#post_matrixclientv3accountpassword
[`PUT /_matrix/client/v3/profile/{userId}/{keyName}`]: https://spec.matrix.org/v1.16/client-server-api/#put_matrixclientv3profileuseridkeyname
[`DELETE /_matrix/client/v3/profile/{userId}/{keyName}`]: https://spec.matrix.org/v1.16/client-server-api/#delete_matrixclientv3profileuseridkeyname
[`POST /_matrix/client/v3/account/3pid`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3account3pid
[`POST /_matrix/client/v3/account/3pid/add`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3account3pidadd
[`POST /_matrix/client/v3/account/3pid/delete`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3account3piddelete
[`POST /_matrix/client/v1/login/get_token`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv1loginget_token
