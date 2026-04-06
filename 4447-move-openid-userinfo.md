# MSC4447: Move OpenID userinfo endpoint out of `/_matrix/federation`

The Matrix specification includes [an endpoint](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1openiduserinfo), `/_matrix/federation/v1/openid/userinfo`, which allows a client to prove its identity to an external service. This endpoint is used by the [lk-jwt-service](https://github.com/element-hq/lk-jwt-service), among others. However, its location in the server-to-server API is strange -- it requires no authentication, and, unlike every other endpoint under `/_matrix/federation`, it isn't intended for use by other homeservers. This proposal moves it to a new endpoint prefix, `/_matrix/openid`, to separate it from the federation endpoints which it is unrelated to.

## Proposal

[`GET /_matrix/federation/v1/openid/userinfo`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1openiduserinfo) is moved to a new location, `GET /_matrix/openid/v1/userinfo`. No changes are made to the behavior of the endpoint itself. The old endpoint is marked for deprecation and removal in a future version of the Matrix specification.

Servers SHOULD NOT return a HTTP 3xx response to the old endpoint which points to the new endpoint. If a server wishes to support both endpoints, it should handle them identically.

## Potential issues

All software which uses the old endpoint will have to be updated to refer to the new endpoint before the old endpoint is removed from the specification.

## Security considerations

None. This proposal makes no functional changes to the behavior of the endpoint.

## Unstable prefix

No unstable name for the new endpoint is proposed, as introducing one would defeat the purpose of this proposal. Servers MAY indicate their support for this proposal by setting the `org.continuwuity.msc4447` field of `unstable_features` to `true` under [`/_matrix/client/versions`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientversions).

## Dependencies

None.
