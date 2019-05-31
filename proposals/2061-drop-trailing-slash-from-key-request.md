# MSC2061: make the trailing slash on `GET /_matrix/key/v2/server/` optional

## Background

The `GET /_matrix/key/v2/server/{keyId}` endpoint is used to request signing
keys from remote homeservers, so that received events and incoming federation
requests can be validated.

The
[specification](https://matrix.org/docs/spec/server_server/r0.1.1.html#get-matrix-key-v2-server-keyid)
for this endpoint says that the `keyId` parameter is deprecated; however, it does
not say that the trailing slash may be omitted. The correct way to call this
endpoint is therefore as `GET /_matrix/key/v2/server/`.

This MSC contends that the trailing slash is redundant, and inconsistent with
other endpoints, where we have recently made an effort to remove redundant
trailing slashes (cf [synapse#4935](https://github.com/matrix-org/synapse/pull/4935)).

For background on the deprecation of `keyId`, see
[matrix-doc#1423](https://github.com/matrix-org/matrix-doc/pull/1423/files/8e97b0ca8174190f8bca6170cd39f92d09598d87#diff-12247cb9a77e9a80c0aae288318cc3aa).

Synapse currently treats a request to `GET /_matrix/key/v2/server` (without the
trailing slash) the same as `GET /_matrix/key/v2/server/` (and, in fact, all
requests to `GET /_matrix/key/v2/server/{keyId}`, with any `keyId`): it returns
all known signing keys for the local server.

## Proposal

In line with other endpoints which offer an optional URL path param
([example](https://matrix.org/docs/spec/client_server/r0.4.0.html#get-matrix-client-r0-rooms-roomid-state-eventtype)),
`GET /_matrix/key/v2/server` should be specified as a separate endpoint, whose
behaviour should be identical to that of `GET /_matrix/key/v2/server/{keyId}`
with an empty `keyId` parameter.

## Tradeoffs

It's not entirely clear to me that the deprecation of `keyId` and the
recommendation to use the wildcard version of the endpoint is optimal, so an
alternative approach would be to reverse that deprecation and instead deprecate
the use of the wildcard lookup. However, that would be a more complex change
which is hard to justify at this point in the Matrix 1.0 release cycle.

## Security considerations

None forseen. This is largely a formalisation of existing behaviour.

## Conclusion

The trailing slash on `GET /_matrix/key/v2/server/` is redundant. Let's clarify
that it is optional.
