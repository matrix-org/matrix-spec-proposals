# Proposal to include device IDs in `/account/whoami`

There are some use cases (namely using
[Pantalaimon with bots](https://github.com/matrix-org/pantalaimon/issues/14))
which could benefit from knowing the `device_id` associated with a token.


## Proposal

The `/account/whoami` endpoint receives an additional response field for the `device_id`
associated with the access token. The field is optional because appservice users may not
have a real device associated with them. Non-appservice users should always have a device
associated with them.

Access tokens are already associated with at most 1 device, and devices are associated with
exactly 1 access token. Because of this, we do not need to worry about multiple devices
causing problems. For more information, see
https://matrix.org/docs/spec/client_server/r0.4.0.html#relationship-between-access-tokens-and-devices

*Note*: Pantalaimon would likely require a `device_id` be returned and error requests
otherwise. This should be considered expected behaviour by Pantalaimon in the MSC author's
opinion.


## Tradeoffs

We could introduce a `/device/whoami` endpoint, however that is a less superior option. Most
calls to `/device/whoami` would additionally need to call `/account/whoami` to determine the
user ID of the account. We had might as well bundle the two pieces of information into the
same request.
