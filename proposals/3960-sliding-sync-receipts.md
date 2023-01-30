# MSC3960: Sliding Sync Extension: Receipts

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
which includes support for room receipts in the `/sync` response.

## Proposal

MSC3575 does not include support for receipts. This extension will add support for both public
and private room receipts.

The prosposal is to introduce a new extension called `receipts` with the following request parameters:
```js
{
    "enabled": true, // sticky
}
```
If `enabled` is `true`, then the sliding sync response MAY include the following response fields in
the `receipts` extension response:
```json
{
    "rooms": {
        "!foo:bar": {
            m.receipt EDU
        },
        "!foo2:bar" {
            m.receipt EDU
        }
    }
}
```

The `m.receipt` event in this response is the same event that would appear in the array
`rooms.join["!foo:bar"].ephemeral.events` under `/sync`. This includes the `m.read.private` key in the
receipt EDU for private read receipts.

Receipts MUST only be sent for rooms returned in the sliding sync response. Receipts MUST only be
returned for events sent in the `timeline` section for each room of the sliding sync response. Delta
tokens MUST be ignored when calculating the events in the `timeline`, or else additional read receipts
for the same event would never be returned to the client. The receipts themeselves MAY be subject to
delta tokens such that only read receipt deltas are returned to the client.

Overall, these steps prevent the sliding sync response from scaling with the amount of rooms on the client.
This contrasts with the existing `/sync` mechanism which sends all receipts for all users in all rooms.


## Potential issues

By not sending receipts for events not in the returned `timeline`, the client will not have receipt
information for old events (e.g retrieved via `/messages`). An additional MSC would be required to add
receipt information to events returned from `/messages`. It is unacceptable to return receipts not in
the returned `timeline` because this can be extremely large e.g for Matrix HQ this is 50,000+ read receipts
just for that room, for events that the client will potentially never view!

## Alternatives

This extension could be bundled into the core MSC3575, but this would force all clients to receive this
data. In practice clients can function extremely well without the need for read receipts, so forcing all
clients to receive this data feels like the wrong design.

## Security considerations

No additional security considerations beyond what the current `/sync` implementation provides.

## Unstable prefix

No unstable prefix as Sliding Sync is still in review. To enable this extension, just add this to
your request JSON:
```js
{
    "extensions": {
        "receipts": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC builds on MSC3575, which at the time of writing has not yet been accepted into the spec.
