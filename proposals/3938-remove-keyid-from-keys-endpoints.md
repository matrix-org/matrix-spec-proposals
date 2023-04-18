# MSC3938: Remove deprecated `keyId` parameters from `/keys` endpoints

The `keyId` path parameter on
[`GET /_matrix/key/v2/server/{keyId}`](https://spec.matrix.org/v1.5/server-server-api/#get_matrixkeyv2serverkeyid)
and [`GET /_matrix/key/v2/query/{serverName}/{keyId}`](https://spec.matrix.org/v1.5/server-server-api/#get_matrixkeyv2queryservernamekeyid)
has been deprecated since before the Matrix spec was formally versioned
([pull request](https://github.com/matrix-org/matrix-spec-proposals/pull/1423)).

The reason for deprecation was primarily that it was never implemented
correctly: making a request with a `keyId` had the same effect as making a
request without one.

## Proposal

The deprecated `keyId` path parameter should be removed from
[`GET /_matrix/key/v2/server/{keyId}`](https://spec.matrix.org/v1.5/server-server-api/#get_matrixkeyv2serverkeyid)
and [`GET /_matrix/key/v2/query/{serverName}/{keyId}`](https://spec.matrix.org/v1.5/server-server-api/#get_matrixkeyv2queryservernamekeyid).

Furthermore, a trailing slash at the end of the endpoint path will no longer be permitted.

The new endpoints will simply be `GET /_matrix/key/v2/server` and `GET
/_matrix/key/v2/query/{serverName}` respectively, and they will return all
available keys for the given server.

## Potential issues

This is a breaking change: some servers (such as Synapse, until [very
recently](https://github.com/matrix-org/synapse/pull/14525)) may include the
`{keyId}` in outgoing requests.


