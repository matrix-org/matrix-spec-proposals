# MSC4326: Device masquerading for appservices

*History*: This proposal is split off from [MSC3202: Encrypted Appservices](https://github.com/matrix-org/matrix-spec-proposals/pull/3202).

Appservices today can make requests as any (local) user in their namespace through [identity assertion](https://spec.matrix.org/v1.15/application-service-api/#identity-assertion).
To support end-to-end encryption and other similar device-centric functionality, appservices need to
be able to also pick the device ID they are speaking as.

This proposal adds device ID to the identity assertion appservices can already perform, leaving other
aspects of end-to-end encryption support to other MSCs like MSC3202 (mentioned above).


## Proposal

To complement the (optional) `user_id` query string parameter during identity assertion, an also-optional
`device_id` parameter is also supported. The new `device_id` parameter is only available when `user_id`
is available to the caller - when authenticating using an `as_token`.

When both a `user_id` and `device_id` are provided, and both are known/registered, the server uses those
details for the remainder of the request. For many endpoints this means updating the "last seen IP"
and "last seen timestamp" for the device, though for some endpoints it may mean interacting with the
device specifically (such as when uploading one-time keys).

If the `device_id` does not already exist on the `user_id`, the server returns a `400 M_UNKNOWN_DEVICE`
standard error response.

If the `device_id` is present without a `user_id`, the `user_id` is assumed to be the appservice's
default sender (the user implied by `sender_localpart` in its registration). This is the same behaviour
as today when the appservice makes such requests.

If the `device_id` is present and the requester is not able to use identity assertion, the request
continues as though the `device_id` parameter was never present. This copies the behaviour of `user_id`.

### Examples

*All examples assume the `user_id` is within the appservice's scope.*

User ID asserted, but not device ID:

```text
GET /_matrix/client/v3/account/whoami?user_id=@alice:example.org
Authorization: Bearer as_token_here

{
  "user_id": "@alice:example.org",
  "is_guest": false
}
```

User ID and device ID asserted:

```text
GET /_matrix/client/v3/account/whoami?user_id=@alice:example.org&device_id=ABC123
Authorization: Bearer as_token_here

{
  "user_id": "@alice:example.org",
  "is_guest": false,
  "device_id": "ABC123"
}
```

Just device ID asserted:

```text
GET /_matrix/client/v3/account/whoami?device_id=ABC123
Authorization: Bearer as_token_here

{
  "user_id": "@the_appservice_sender:example.org",
  "is_guest": false,
  "device_id": "ABC123"
}
```

Nothing asserted:

```text
GET /_matrix/client/v3/account/whoami
Authorization: Bearer as_token_here

{
  "user_id": "@the_appservice_sender:example.org",
  "is_guest": false
}
```

## Potential issues

Appservices will need to create and manage their users' devices using another proposal or system. An
example is [MSC4190](https://github.com/matrix-org/matrix-spec-proposals/pull/4190).


## Alternatives

None relevant.


## Security considerations

The behaviour of `device_id` is largely copied from `user_id`, so should not increase or decrease an
appservice's capabilities beyond what it could already do. This is especially true for appservices
which cover "real" users in their namespaces: while they couldn't (and still can't) access data encrypted
before using something like [MSC3202](https://github.com/matrix-org/matrix-spec-proposals/pull/3202),
they could log out whatever devices they don't want and register new ones accordingly.


## Unstable prefix

For historical reasons, unstable implementations of this proposal should use `org.matrix.msc3202.device_id`
instead of `device_id`.

`ORG.MATRIX.MSC4326.M_UNKNOWN_DEVICE` is used as the error code instead of `M_UNKNOWN_DEVICE`.

## Dependencies

None relevant. Some MSCs depend on this MSC's functionality, however.
