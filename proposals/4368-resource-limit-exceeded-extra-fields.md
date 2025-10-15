# MSC4368: Add limit_type to M_RESOURCE_LIMIT_EXCEEDED error code

## Proposal

1. Add an optional `limit_type` field to the body of the [`M_RESOURCE_LIMIT_EXCEEDED`] error response that has the same
definition as it does for [`m.server_notice`]:

> The kind of usage limit the server has exceeded

And on the possible values:

> The specified values for `limit_type` are:
> `monthly_active_user` The server’s number of active users in the last 30 days has exceeded the maximum. New
> connections are being refused by the server. What defines “active” is left as an implementation detail, however
> servers are encouraged to treat syncing users as “active”.

2. Update the description of `admin_contact` so that instead of "a place to reach out to" that it is the same definition
as the `admin_contact` field on the [`m.server_notice`] which says "a URI giving a contact method for the server
administrator".

This amounts to unifying the representation of a server resource limit being exceeded in an error code and the server
notice.

## Potential issues

None anticipated. Optional extra fields on the error.

## Alternatives

None considered.

## Security considerations

None.

## Unstable prefix

Ideally implementations would use an unstable prefix of something like `io.element.mscXXX.limit_type` whilst the
MSC is in development.

However, it is noted that the implementation in Synapse has existed since
[2018](https://github.com/matrix-org/synapse/pull/3707) and so the unprefixed `limit_type` is being used in the wild.
As such some clients also support this unprefixed version.

## Dependencies

None.

[`M_RESOURCE_LIMIT_EXCEEDED`]: https://spec.matrix.org/v1.16/client-server-api/#other-error-codes
[`m.server_notice`]: https://spec.matrix.org/v1.16/client-server-api/#mroommessagemserver_notice
