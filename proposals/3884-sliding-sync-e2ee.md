# MSC3884: Sliding Sync Extension: E2EE

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
which includes support for end-to-end encrypted room fields in the `/sync` response.

## Proposal

MSC3575 does not include support for end-to-end encrypted rooms. This extension will add support for
end-to-end encrypted fields, specifically one-time keys, changed devices and fallback key types.

The prosposal is to introduce a new extension called `e2ee` with the following request parameters:
```js
{
    "enabled": true, // sticky
}
```
If `enabled` is `true`, then the sliding sync response MAY include the following response fields in
the `e2ee` extension response:
```json
{
    "device_one_time_keys_count": {
        "signed_curve25519": 50
    },
    "device_lists: {
        "changed": ["@alice:example.com"],
        "left": ["@bob:example.com"]
    },
    "device_unused_fallback_key_types": [
        "signed_curve25519"
    ]
}
```

The semantics of these fields is exactly the same as the current `/sync` implementation, as implemented
in v1.3 of the Client-Server Specification. `device_lists` may be omitted if there are no users who
have changed/left.

For sliding sync, an initial response will include all fields. When there are updates, only the
_changed_ fields are returned. That is to say, if `device_one_time_keys_count` has not changed between
requests, it will be omitted which means to use the previous value. This deviates from the current
`/sync` implementation which always includes this field. Likewise for `device_unused_fallback_key_types`.

## Potential issues

It's unclear if `device_unused_fallback_key_types` and `device_one_time_keys_count` should always be
included or not, as this extension deviates from the logic as v1.3 of the Specification which is not
clear on this. If it is always included, this adds extra bytes and therefore consumes needless
bandwidth. In practice, Synapse _always_ includes these fields, when this is probably not needed.
Changing this behaviour may break clients which expect these fields to always exist.

## Alternatives

The alternative is to not include this extension at all, making it impossible to include reliable
E2EE support in Sliding Sync. As this extension is opt-in, as all Sliding Sync extensions are, this
feels undesirable to not provide this extension.

## Security considerations

No additional security considerations beyond what the current `/sync` implementation provides.

## Unstable prefix

No unstable prefix as Sliding Sync is still in review. To enable this extension, just add this to
your request JSON:
```js
{
    "extensions: {
        "e2ee": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC builds on MSC3575, which at the time of writing has not yet been accepted into the spec.
