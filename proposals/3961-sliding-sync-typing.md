# MSC3961: Sliding Sync Extension: Typing Notifications

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
which includes support for typing notifications in the `/sync` response.

## Proposal

MSC3575 does not include support for typing notifications. This extension will add support for it.

The proposal is to introduce a new extension called `typing`. It processes the
core extension arguments `enabled`, `rooms` and `lists`, but defines no 
arguments of its own.
```json5
{
    "enabled": true, // sticky
    "lists": ["rooms", "dms"], // sticky
    "rooms": ["!abcd:example.com"] // sticky
}
```
If `enabled` is `true`, then the sliding sync response MAY include the following response fields in
the `typing` extension response:
```json5
{
    "rooms": {
        "!foo:bar": {
            // m.typing EDU
        },
        "!foo2:bar": {
            // m.typing EDU
        }
    }
}
```

If a `lists` or `rooms` argument is given to the extension, the `typing` extension
response SHOULD only include rooms belonging at least one of the sliding windows
in `lists`, or rooms whose IDs are in `rooms`. See also MSC3575's "Extensions"
section.

The `m.typing` event in this response is the same event that would appear in the array
`rooms.join["!foo:bar"].ephemeral.events` under a traditional "v2" `/sync`.

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
```json
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
