# MSC3885: Sliding Sync Extension: To-Device

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
which includes support for to-device messages in the `/sync` response.

## Proposal

MSC3575 does not include support for to-device events. This extension will add support for
to-device events. There is a **critical** problem in the current to-device implementation, which is
that events are implicitly acknowledged when the user advances the `/sync` token. This causes problems
when clients need to have 2 or more sync streams open at a time, e.g a push notification process _and_
a main process. This can cause the two processes to race to fetch the to-device events, resulting in
the need for complex synchronisation rules to ensure the token is correctly and atomically exchanged
between processes. Sliding Sync's implementation of to-device events removes this requirement by
associating an _explicit_ token **just for to-device events**. This token uses the same terminology
of the current `/sync` implementation: `since` and `next_batch`.

The proposal is to introduce a new extension called `to_device` with the following request parameters:
```js
{
    "enabled": true, // sticky
    "limit": 100, // sticky, max number of events to return, server can override
    "since": "some_token" // optional, can be omitted on initial sync / when extension is enabled
}
```
If `enabled` is `true`, then the sliding sync response includes the following response fields in
the `to_device` extension response:
```js
{
    "next_batch": "some_token", // REQUIRED: even if no changes
    "events": [ // optional, only if there are events since the last `since` value.
        { ... to device event ... }
    ]
}
```

The client MUST persist the `next_batch` value to persistent storage between requests in case the client is
killed by the OS.

The semantics of the `events` field is exactly the same as the current `/sync` implementation, as implemented
in v1.3 of the Client-Server Specification. The server MUST NOT send more than `limit` events: it may send
less than `limit` events if the value provided was too large.

The `events` are treated as "acknowledged" when the server receives a new request with the `since`
value set to the previous response's `next_batch` value. When this occurs, acknowledged events are
permanently deleted from the server, and MUST NOT be returned to the client should another request
with an older `since` value be sent.

If a response is lost, the client will retry the request with the same `since` value. When this happens,
the server MAY bundle together more events if they arrived in the interim. 

## Potential issues

This proposal introduces a new sync token type for clients to manage. It is done for good reasons but
it does slightly increase the complexity of designing a correct client implementation. 

## Alternatives

The alternative is to include to-device events like normal events in a different section, without
making use of dedicated `since` and `next_batch` tokens, instead relying on the `pos` value. This
would revert to-device events to be implicitly acknowledged, which has caused numerous [issues](https://github.com/vector-im/element-ios/issues/3817) in
the past.

## Security considerations

No additional security considerations beyond what the current `/sync` implementation provides.

## Unstable prefix

No unstable prefix as Sliding Sync is still in review. To enable this extension, just add this to
your request JSON:
```js
{
    "extensions": {
        "to_device": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC builds on MSC3575, which at the time of writing has not yet been accepted into the spec.
