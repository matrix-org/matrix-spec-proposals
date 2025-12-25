# MSC3959: Sliding Sync Extension: Account Data

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
which includes support for global and room account data in the `/sync` response.

## Proposal

MSC3575 does not include support for account data. This extension will add support for both global
and room account data.

The prosposal is to introduce a new extension called `account_data`.
It processes the core extension arguments `enabled`, `rooms` and `lists`, but
defines no arguments of its own.
```json5
{
    "enabled": true, // sticky
    "lists": ["rooms", "dms"], // sticky
    "rooms": ["!abcd:example.com"] // sticky
}
```
If `enabled` is `true`, then the sliding sync response MAY include the following response fields in
the `account_data` extension response:
```json5
{
    "global": [
        {
           // account data JSON
        }
    ],
    "rooms": {
        "!foo:bar": [
           {
              // account data JSON
           },
           {
              // account data JSON
           }
        ],
        "!foo2:bar": [
            {
               // account data JSON
            }
        ]
    }
}
```

If a `lists` or `rooms` argument is given to the extension, the `typing` extension
response SHOULD only include rooms belonging at least one of the sliding windows
in `lists`, or rooms whose IDs are in `rooms`. See also MSC3575's "Extensions"
section.

All keys are optional and clients MUST check if they exist prior to use. The semantics of these fields
is exactly the same as the current `/sync` implementation whereby:
 - This extension's `global` key maps to the top-level `account_data.events` field in `/sync`.
 - This extension's `rooms` key maps to a joined room's `account_data` field in `/sync`, e.g the path
   `rooms.join["!foo:bar"].account_data.events`.

For sliding sync, an initial response must include all global account data. This data is subject to delta
tokens and SHOULD be omitted when delta tokens are used and the client already has these events. Only
rooms returned in the sliding sync response will be included in the `rooms` key. The server MUST NOT
send room account data for rooms the client is not aware of. This prevents the sliding sync response
from scaling with the amount of room account data on the client. These events are also subject to delta
tokens and SHOULD be omitted when the client already has these events.


## Potential issues

If clients do not use delta tokens, every initial sliding sync response will include all global account data.
In practice, this can be very large: specifically the `m.push_rules` and `m.direct` account data events
scale sub-linearly with the number of rooms on the clients account. For very large accounts, these two
events can take >100KB, which impacts time-to-first-use on clients. Delta tokens can be used to prevent
these events from being sent all the time. Similarly, room account data is sent every time sliding sync
sends an `initial: true` room response. If rooms frequently reappear in the sliding window this can result
in needless bandwidth consumption. This can also be mitigated via delta tokens.

There is no filtering capabilities in this extension. Clients may not care about some kinds of events but
are unable to filter them out of the response.

## Alternatives

This extension could be bundled into the core MSC3575, but this would force all clients to receive this
data. In practice clients can function extremely well without the need for account data, so forcing all
clients to receive this data feels like the wrong design.

This extension could also not exist, but this would mean that Sliding Sync has no way to push live-updated
account data to clients, relying on clients to manually GET the HTTP endpoints `/user/<user_id>/account_data/<type>`
and `/user/{userId}/rooms/{roomId}/account_data/{type}`.

## Security considerations

No additional security considerations beyond what the current `/sync` implementation provides.

## Unstable prefix

No unstable prefix as Sliding Sync is still in review. To enable this extension, just add this to
your request JSON:
```json
{
    "extensions": {
        "account_data": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC builds on MSC3575, which at the time of writing has not yet been accepted into the spec.
