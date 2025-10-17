# MSC0000: M_CAPABILITY_NOT_ENABLED error code for when capability is not enabled on an API endpoint

The [capabilities negotiation] feature in the [Client-Server API] provides a mechanism for clients
to discover whether specific capabilities are available to a user.

However, the endpoints that use capabilities do not currently specify what error response a client
should expect if they try to use an API that does not have the capability enabled for the user.

I believe this is an omission in the current spec that should be addressed for existing capabilites
and be checked for future MSCs that use capabilities.

For background: this MSC originates from a
[spec PR](https://github.com/matrix-org/matrix-spec/pull/2212) that has since been closed.

## Proposal

Define a new [other error code] of `M_CAPABILITY_NOT_ENABLED`.

Define the following behaviour for existing API endpoints that use capabilities:

Capability|Endpoint(s)|Current spec|Proposed behaviour
-|-|-|-
[`m.change_password`](https://spec.matrix.org/v1.16/client-server-api/#mchange_password-capability)|[`POST /_matrix/client/v3/account/password`](https://pr2212--matrix-spec-previews.netlify.app/client-server-api/#post_matrixclientv3accountpassword)|Not defined|Return `403` with `M_CAPABILITY_NOT_ENABLED` if `m.change_password`.`enabled` is `false`
[`m.profile_fields`](https://spec.matrix.org/v1.16/client-server-api/#mprofile_fields-capability)|[`PUT /_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.16/client-server-api/#put_matrixclientv3profileuseridkeyname) [`DELETE /_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.16/client-server-api/#delete_matrixclientv3profileuseridkeyname)|`403` for `PUT`. Maybe `403` for `DELETE`. Error code not specified for either|Return `403` with `M_CAPABILITY_NOT_ENABLED` if: `m.profile_fields`.`enabled` is `false`; or, `m.profile_fields`.`disallowed` contains `{keyName}`;
[`m.set_displayname`](https://spec.matrix.org/v1.16/client-server-api/#mset_displayname-capability)|As per `m.profile_fields`|As per `m.profile_fields`|Return `403` with `M_CAPABILITY_NOT_ENABLED` if: `m.profile_fields`.`enabled` is `false`; or, `m.profile_fields`.`disallowed` contains `{keyName}`; or, `m.set_displayname`.`enabled` is `false`;
[`m.set_avatar_url`](https://spec.matrix.org/v1.16/client-server-api/#mset_avatar_url-capability)|As per `m.profile_fields`|As per `m.profile_fields`|Return `403` with `M_CAPABILITY_NOT_ENABLED` if: `m.profile_fields`.`enabled` is `false`; or, `m.profile_fields`.`disallowed` contains `{keyName}`; or, `m.set_avatar_url`.`enabled` is `false`;
[`m.3pid_changes`](https://spec.matrix.org/v1.16/client-server-api/#m3pid_changes-capability)|[`POST /_matrix/client/v3/account/3pid`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3account3pid) [`POST /_matrix/client/v3/account/3pid/add`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3account3pidadd) [`POST /_matrix/client/v3/account/3pid/delete`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3account3piddelete)|Not defined|Return `400` with `M_CAPABILITY_NOT_ENABLED` if `m.3pid_changes`.`enabled` is `false`
[`m.get_login_token`](https://spec.matrix.org/v1.16/client-server-api/#mget_login_token-capability)|[`POST /_matrix/client/v1/login/get_token`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv1loginget_token)|Maybe `400` with undefined error code if `m.get_login_token`.`enabled` is `false`|`403` with `M_CAPABILITY_NOT_ENABLED` if `m.get_login_token`.`enabled` is `false`

## Potential issues

TODO: Change in behaviour on `m.get_login_token`.

## Alternatives

Base on existing implementations. This is what was originally in https://github.com/matrix-org/matrix-spec/pull/2212

## Security considerations

None.

## Unstable prefix

Whilst this proposal is under development the `IO.ELEMENT.MSCXXXX_CAPABILITY_NOT_ENABLED` value
should be used instead of `CAPABILITY_NOT_ENABLED`.

## Dependencies

None.

[capabilities negotiation]: https://spec.matrix.org/v1.16/client-server-api/#capabilities-negotiation
[Client-Server API]: https://spec.matrix.org/v1.16/client-server-api/
[other error code]: https://spec.matrix.org/v1.16/client-server-api/#other-error-codes
