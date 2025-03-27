# MSC4262: Sliding Sync Extension: Profile Updates

This MSC is an extension to [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)
(and its proposed successor [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186))
which adds support for receiving profile updates via Sliding Sync. It complements
[MSC4259](https://github.com/matrix-org/matrix-spec-proposals/pull/4259) which handles
federation-level profile updates.

## Proposal

MSC3575 currently does not include support for receiving global profile field updates through the
`/sync` endpoint. This extension adds support for receiving profile updates for users who are
members of rooms the client is subscribed to.

The proposal introduces a new extension called `profiles`. It processes the core extension
arguments `enabled`, `rooms`, and `lists`, and adds the following optional arguments:

```json5
{
    "enabled": true,           // sticky
    "lists": ["rooms", "dms"], // sticky
    "rooms": ["!abcd:example.com"], // sticky
    "fields": ["displayname", "avatar_url"], // optional filter for specific profile fields
    "include_history": false   // optional, defaults to false
}
```

If `enabled` is `true`, then the sliding sync response MAY include profile updates in the following format:

```json5
{
    "users": {
        "@alice:example.com": {
            "displayname": "Alice",
            "avatar_url": "mxc://example.com/abc123",
            "org.example.language": "en-GB"
        },
        "@bob:example.com": {
            "displayname": null  // Field removal
        }
    }
}
```

### Behaviour

1. The extension only returns profile updates for users who are members of rooms that the client is
   subscribed to via either:
   - Room IDs explicitly listed in the `rooms` argument
   - Rooms that fall within the sliding windows specified in `lists`

2. The optional `fields` argument allows clients to filter which profile fields they want to receive
   updates for. If omitted, all profile field updates are included.

3. The optional `include_history` argument controls whether the initial sync includes recent
   historical profile changes:
   - If false (default), only current profile states are sent on initial sync
   - If true, the server MAY include recent profile changes that occurred before the sync

4. On an initial sync:
   - Profile data MUST only be sent for rooms returned in the sliding sync response
   - If `include_history` is false, only current profile states are sent
   - If `include_history` is true, recent profile changes MAY be included

5. When live streaming:
   - Profile updates MUST be sent as the server receives them
   - For rooms which initially appear (`initial: true`) due to direct subscriptions or rooms moving
     into the sliding window, current profile states MUST be included
   - A null value for a field indicates the field has been removed
   - Omitted fields should be considered unchanged

### Implementation Notes

- Servers SHOULD implement appropriate batching and rate limiting of profile updates to prevent
  overwhelming clients

- While this extension provides real-time profile updates, implementations should note:
  - Network issues could cause missed updates
  - Clients MAY implement periodic full profile refreshes if they require stronger consistency guarantees
  - The frequency of such refreshes should be balanced against resources and desired freshness

- Profile updates are typically infrequent compared to other real-time events like typing
  notifications, so including them in sliding sync is considered efficient

## Potential Issues

1. Large Initial Sync Payload
   - With `include_history` enabled, the initial sync could be large for rooms with many members
   - Servers should consider implementing reasonable limits on historical profile data

2. Update Frequency
   - Some users might update profiles frequently
   - Implementations should consider rate limiting and batching updates

## Alternatives

1. Separate Profile Sync API
   - Could provide more granular control over profile syncing
   - Would increase complexity by requiring another connection
   - Would duplicate much of sliding sync's room subscription logic

2. Push-based Profile Updates
   - Could use a separate WebSocket connection for profile updates
   - Would increase complexity and connection overhead
   - Would duplicate room subscription logic

## Security Considerations

1. Profile information is considered public data in Matrix

2. The extension respects existing privacy boundaries:
   - Only returns updates for users in rooms the client can access
   - Follows the same authentication and authorization as the main sliding sync endpoint

3. Rate limiting helps prevent abuse

## Unstable Prefix

No unstable prefix as Sliding Sync is still in review. To enable this extension, add this to your
request JSON:

```json
{
    "extensions": {
        "profiles": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC builds on:

- [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575) (Sliding Sync) or its
  proposed successor [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186)
  (Simplified Sliding Sync), neither of which are yet accepted into the spec
