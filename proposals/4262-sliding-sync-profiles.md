# MSC4262: Sliding Sync Extension: Profile Updates

This MSC is an extension to Simplified Sliding Sync (specified by
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186)). As
that MSC did not specify the shape of extensions, this MSC assumes the base
shape from [MSC3575: Sliding
Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/3575) (the
predecessor to the ultimately accepted simplified variant).

This MSC adds support for receiving profile updates via Sliding Sync. It
complements
[MSC4429](https://github.com/matrix-org/matrix-spec-proposals/pull/4259), which
adds the same information to legacy sync. And it is related to
[MSC4259](https://github.com/matrix-org/matrix-spec-proposals/pull/4259) which
handles federation-level profile updates.

## Proposal

This extension adds support for receiving profile updates for other users they
share rooms with.

The proposal introduces a new extension called `profiles`. It processes the core
extension arguments `enabled`, `rooms`, and `lists`, and adds the following
optional arguments:

```json5
{
    "enabled": true,
    "fields": ["displayname", "avatar_url", "m.some_field"], // optional filter for specific profile fields
}
```

If `enabled` is `true`, then the sliding sync response MAY include profile
updates in the following format:

```json5
{
    // extensions is a top-level field in the response body.
    "extensions": {
        "profiles": {
            "users": {
                "@alice:example.com": {
                    // Optional. Fields that were newly set, or updated.
                    "updated": {
                        "displayname": "Alice",
                        "avatar_url": "mxc://example.com/abc123",
                        "org.example.language": "en-GB"
                    },
                    // Optional. A field has been removed from a user's profile.
                    "removed": ["com.example.other_field"]
                },
                // Client can stop tracking this user (they left all shared rooms).
                "@bob:remote.example.com": null
            },
        }
    }
}
```

Profile fields that are either newly added to a user's profile or recently
updated are found under `users-><user_id>->updated`. Likewise, any field IDs that
are cleared/removed from a user's profile will appear under
`users-><user_id>->removed`. Omitted fields are considered unchanged.

The `updated` field SHOULD only be present if there are changes to existing
fields on a user's profile. Otherwise, the field should not be present (i.e. if
fields were only removed). Likewise, the `removed` field should not be present
if there were only updated to existing fields (and none were cleared).

Only fields specified by the `fields` request parameter will be included in
these two sections. `fields` must be specified in every sync request; the
homeserver does not "remember" the client's requested `fields` from the last
sync request.

If the value directly underneath a user's ID is `null`
(`@bob:remote.example.com` in the above example), this is a signal to the client
that they may stop tracking this user, as that user has left all shared rooms.

### When are profile updates returned?

An individual sliding sync session (which persists over the lifetime of a
client's login) contains top-level `rooms` and `lists` parameters. From these,
the homeserver derives a list of rooms the client wants updates for.

When a room enters this subset in this connection for the first time, all
requested `fields` from profiles of users in that room MAY be sent down. This
gives the client a base set of information for which future field updates can be
applied on top of. The homeserver MAY omit some fields and profiles if it
believes that the client has already received them, likewise repeat profiles MAY
be sent down based on homeserver implementation.

Separately, any time a user who shares a room with the syncing user updates a
field on their profile, that update should be sent down. Even for users whose
rooms are not part of the room subset. While these profiles may not even be
rendered on the client yet, this covers the case where a room subset may shrink
to exclude certain users who then update their profile in the meanwhile. If the
room subset then grew to cover them again, the client would end up with stale
data.

Finally, if the list of `fields` expands to cover a new field ID, those fields
should be sent down for all users that are within the current room subset.
Future incremental updates will then include changes to this field.

Homeservers MUST include updates that the syncing user has made themselves to
allow a user's other devices to be aware of the changes.

### Lazy-loading user profiles

The above strategy restricts the profiles that are sent down to only those users
in rooms which are within the sliding window or direct subscriptions. However,
if a room like Matrix HQ, which has over 6000 users, is part of the that list
then the homeserver is forced to send down membership information for 6000 users
in a single response.

Sliding Sync offers the `lazy_members` boolean flag on a per-room basis, which
when `true` will only send down membership information for a user if:

- the user is one of the `sender`s of a timeline event included in the response
- membership event state keys in the timeline
- users in `required_state` member events that are returned
- heroes(? - not mentioned in the MSC, but seems like Synapse implements it)
- invite/knock stripped-state users/senders(? - likewise)

Similarly, when `lazy_members` is `true` for a given room, a user's full profile
will only be included if they meet the above criteria. If a user is in two rooms
and only one has `lazy_members: true`, the user's full profile should be sent
down anyways due to being in a room where `lazy_members: false` was set.

Lazy loading does not affect the fact that homeservers MUST include updates that
the syncing user has made themselves.

### Implementation-specific notes

#### Homeservers

Homeservers should only consider a profile field update "accepted" by a
client once the client returns with a new `/sync` request with the next `/sync`
token, NOT just after sending down the profile update. The client may never
receive response due to network conditions, or a bug in the client
implementation.

Homeservers are encouraged to maintain a record of which user profile fields
have been sent down in a given sliding sync connection. That way, as new rooms
enter the room subset, users who were already in rooms within the room subset
will not have their full profiles sent down a second time.

#### Clients

Upon receiving a notification, a client may want to show profile information in
the notification pop-up. Because the user in question may not be part of any of
the rooms that were included in the current sliding sync connection, or the
client may not have synced for a while, clients are recommended to request the
other user's profile directly using [`GET
/_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3profileuseridkeyname)
to build the notification UI, instead of relying on local profile cache.

## Potential Issues

1. Update Frequency
   - Some users might update profiles frequently
   - Implementations should consider rate limiting and batching updates (TODO: How?)
   - A `limit` parameter could be added to prevent too many updates being down sent at once.

## Alternatives

### Only send profile updates for users in rooms that are in the sliding sync room subset

The proposal asks for full profiles of users to only be sent down when the room
they're in *initially* enters the sliding sync room subset. Profile updates for
all users that share a room with the syncing user must then be sent down to
cover any gaps if the room subset shrinks again.

Instead, full profiles of users could be sent down *whenever* a room enters the
sliding sync window, even if it was there before. There's no real downside to
this approach; the chosen solution just fits Synapse's implementation better.

### Add a `lazy_loading` boolean to the extension settings

Instead of relying on the per-room lazy-loading configuration in sliding sync
today, one could add a global `lazy_loading` flag to the profile extensions
configuration. This might make implementation easier? Needs to be explored.

## Security Considerations

1. Profile information is considered public data in Matrix

2. The extension respects existing privacy boundaries:
   - Only returns updates for users in rooms the client can access
   - Follows the same authentication and authorization as the main sliding sync endpoint

## Unstable Prefix

Before this MSC is accepted, implementations should use
`org.matrix.msc4262.profiles` as the extension field name, rather than
`profiles`:

```json
{
    "extensions": {
        "org.matrix.msc4262.profiles": {
            "enabled": true
        }
    }
}
```

## Dependencies

This MSC depends on:

- [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding Sync, for the endpoint)
- [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575) (Sliding Sync, for the extensions shape)
