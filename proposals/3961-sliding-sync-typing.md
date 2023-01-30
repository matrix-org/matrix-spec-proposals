# MSC3961: Sliding Sync Extension: Typing Notifications

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
which includes support for typing notifications in the `/sync` response.

## Proposal

MSC3575 does not include support for typing notifications. This extension will add support for it.

The prosposal is to introduce a new extension called `typing` with the following request parameters:
```js
{
    "enabled": true // sticky
}
```
If `enabled` is `true`, then the sliding sync response MAY include the following response fields in
the `typing` extension response:
```json
{
    "rooms": {
        "!foo:bar": {
            m.typing EDU
        },
        "!foo2:bar" {
            m.typing EDU
        }
    }
}
```

The `m.typing` event in this response is the same event that would appear in the array
`rooms.join["!foo:bar"].ephemeral.events` under `/sync`. 

On an initial sync, typing notifications MUST only be sent for rooms returned in the sliding sync response.
When live streaming, typing notifications MUST be sent as the server receives typing updates. Rooms which
initially appear (`initial: true`) due to direct subscriptions or rooms moving into the sliding window MUST
have typing notification data added _if_ there are typing users, else it can be omitted from the typing response.

## Potential issues

No issues identified.

## Alternatives

This extension could be bundled into the core MSC3575, but this would force all clients to receive this
data. In practice clients can function extremely well without the need for typing notifications, so forcing all
clients to receive this data feels like the wrong design.

## Security considerations

No additional security considerations beyond what the current `/sync` implementation provides.

## Unstable prefix

No unstable prefix as Sliding Sync is still in review. To enable this extension, just add this to
your request JSON:
```js
{
    "extensions": {
        "typing": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC builds on MSC3575, which at the time of writing has not yet been accepted into the spec.
