# MSC3682: Sending Account Data to Application Services

Application services logically represent many clients, but currently don't receive
updates for the Account Data of their users through `/transactions` like clients
do through `/sync`.

This MSC proposes sending Account Data to Application Services, in a format slightly
adapted to the multi-user nature of Application Services.

Sending Account Data to Application Services enables Application Services to use
features such as Online Key Backup and Cross-Signing more efficiently.


## Proposal

We extend `PUT /_matrix/app/v1/transactions/{txnId}` so that the request body
additionally has an `account_data` field, which is equivalent to the [`account_data`
field available in the response body of `GET /_matrix/client/v3/sync`][^AccountData], but wrapped in
a mapping from User ID to Account Data object.

[^AccountData]: See the table titled 'Account Data' under [`/sync`](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3sync)

**Example**
`PUT /_matrix/app/v1/transactions/{txnId}`
```json5
{
    "events": [ ... ],
    "account_data": {
        "@asuser1:example.org": {
            "events": [
                {
                    "content": {
                        "custom_config_key": "custom_config_value"
                    },
                    "type": "org.example.custom.config"
                }
            ]
        }
    }
}
```

The particulars of this proposed field are as follows:

- The `account_data` field may be omitted if there are no changes to communicate
  to the Application Service.
- User IDs may be absent from the `account_data` map if there are no changes
  to communicate for those users' account data.
- The values of the `account_data` map are the same format as that defined by
  `GET /_matrix/client/v3/sync`, which means client-side libraries can likely
  be reused with minimal modification.
  This also makes it clear how potential future extensions to the Client-Server
  `account_data` format will affect the format used for Application Services.
- The presence of Account Data for a User ID does not necessarily mean there have
  been changes.


## Potential issues

This introduces additional implementation complexity to homeservers which now need to detect when
account data changes and send changes. Specifically, it shifts the interaction from a pull model to a push model, which some homeserver implementations may not have been designed for initially.

Some Application Services may not benefit from this additional information in which case it would
be wasteful of computational resources to compute and transmit it.
⇒ **TODO** opt-in/out in the AS registration file. Good idea or not?


## Alternatives

Application Services could poll Account Data from the Client-Server API, but this approach is not
thought to be well-scalable given that Application Services can logically represent many users.


## Security considerations

There are no known security considerations; the Application Service could retrieve the same data by
polling `/sync` for each of its users.


## Unstable prefix

Until such time as this MSC Proposal may become one with the specification, the unstable-prefixed form
`org.matrix.msc3682.account_data` must be used in lieu of `account_data`.

## Dependencies

This MSC is independent of any other MSC, however readers may be interested in similar
proposals for extensions to what Application Services are sent in transactions:

- [MSC2409](https://github.com/matrix-org/matrix-doc/pull/2409): Ephemeral Data Units (EDUs)
- [MSC3202](https://github.com/matrix-org/matrix-doc/pull/3202): device lists, device one-time keys and device fallback key usage states
