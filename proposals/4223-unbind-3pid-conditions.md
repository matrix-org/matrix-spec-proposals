# MSC4223: Error code for disallowing threepid unbinding

Server owners and operators may wish to prevent their users from removing contact information attached
to their account. This may be to ensure there is always a contact address, or for compliance requirements
in some jurisdictions. Many servers may not require contact information, and may never use this MSC's
proposed functionality.

This proposal adds error codes to the [`/3pid/unbind`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3account3pidunbind)
and [`/3pid/delete`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3account3piddelete)
client-server API endpoints to allow for implementation-specific requirements to exist. Future proposals
may further expand upon this concept to *adding* 3PIDs.

This proposal does *not* affect the Identity Service API. The IS API is primarily used for discovery
rather than administration, and so is not affected by the use case described here.

## Proposal

Currently, the [unbind endpoint](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3account3pidunbind)
and [delete endpoint](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3account3piddelete)
do not describe any error responses at all - servers are expected to always return 200 OK. This
inhibits a server's ability to prevent users from removing the last 3PID on their account, for example,
and requires modernizing. Thus, a new error response is added for this implementation-specific use case:

A 403 `M_FORBIDDEN` [standard error response](https://spec.matrix.org/v1.12/client-server-api/#standard-error-response)
is able to be returned from the homeserver. If an `id_server` is supplied, the error response MUST
include `id_server_unbind_result`. Currently, `id_server_unbind_result` may only be `success` or
`no-support`. If a server refuses to proxy the unbind request to the identity server, a new `denied`
result MUST be included.

Clients should note that it is possible to receive `M_FORBIDDEN` with an `id_server_unbind_result` of
`success`. This indicates that the server is refusing to remove the local contact information, but has
removed the discovery component from the identifier. Clients may also receive `no-support`, per normal
specification.

It is illegal under this MSC to use `denied` as `id_server_unbind_result` outside of a 403 `M_FORBIDDEN`
error response.

The `error` message included with `M_FORBIDDEN` should be as descriptive as possible to the user. A
common example may be "The last email address associated with this account may not be removed.".

Servers are *not* required to implement any specific requirements around unbinds. This new error code
allows for *optional* functionality to exist in a spec-compliant manner.

## Potential issues

Bumping the endpoint versions should be considered, as this may be a perceptual breaking change to
clients. However, in general, clients should anticipate errors on endpoints because a 5xx response
may happen at any time without formal specification. The `id_server_unbind_result` change may be
of different concern.

## Alternatives

None explored.

## Security considerations

The majority of security considerations here are privacy ones. Some servers may be operating in areas
where they *cannot* interfere with a user's ability to remove their email address/phone number. This
proposal supports this environment by making the behaviour optional.

Servers may also wish to implement measures which impede desirable user experience, such as refusing
to permit unbinds *at all*. This is not an issue the specification should be concerned with.

## Unstable prefix

While this proposal is not considered stable, implementations should refrain from responding with 403
errors on the endpoints. This may mean an implementation is required to stay as an open Pull Request
until this MSC can become stable.

## Dependencies

This MSC has no direct dependencies.
