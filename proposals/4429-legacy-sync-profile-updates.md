# MSC4429: Profile Updates for Legacy Sync

[Custom profile
fields](https://spec.matrix.org/v1.17/client-server-api/#profiles) allow users
to attach arbitrary data to their public user information. This can be anything
from a timezone (`m.tz`) to whether the user is currently in the office (e.g.
[MSC4426](https://github.com/matrix-org/matrix-spec-proposals/pull/4426)).

Clients may wish to display without user interaction. For example, the `emoji`
field from
[MSC4426](https://github.com/matrix-org/matrix-spec-proposals/pull/4426) could
be shown next to each user's display name in the timeline of a room. This would
be similar to features in other messaging apps, such as Slack:

![A screenshot of Slack depicting an emoji next a user's display name in the
timeline. Hovering over the emoji shows the full user's status
message](./images/4429-slack-timeline-status-emoji.png)

To implement the above, clients could use the existing [`GET
/_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3profileuseridkeyname)
endpoint to fetch the relevant profile data. But to ensure that the user has the
latest information, the client would then need to *poll* that endpoint
frequently. Doing so for every user in a room (or that the client is aware of)
does not scale.

Instead, we need a mechanism for the server to *push* individual updates to the
client as they happen.
[Sync](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync)
is the typical mechanism for delivering updates to the client in Matrix, and this
proposal aims to add profile updates to it.

This is the legacy sync ([`GET
/_matrix/client/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync))
equivalent to
[MSC4262](https://github.com/matrix-org/matrix-spec-proposals/pull/4262), which
adds profile updates to sliding sync.

## Proposal

### New `users` field for `/sync`

A new top-level key is added to the response body of [`GET
/_matrix/client/v3/sync`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync)
named `users`. It features the following implied schema:

```json
{
  "users": {
    "@user:example.org": {
      "profile_updates": {
        // A field was updated.
        // Field taken from MSC4426.
        "m.status": {
          "text": "Swimming in the Great Lakes!",
          "emoji": "🏊️"
        },
        // A field was cleared.
        "m.call": null,
        "m.something_else": { /* ...fields defined elsewhere... */ }
      }
    }
  }
  // Other `/sync` fields...
}
```

The field name `users` fits in alongside `rooms`. Using a nested
`profile_updates` dictionary allows extending the dictionary beneath each user
ID in the future if desired.

Each entry in `profile_updates` represents a profile field and any changes to
its value. If its value is `null`, the field is treated as having been removed
from the user's profile (rather than literally being set to `null`).

The value of a profile field change MUST entirely override the existing value
for that profile field. For example, if the local state of another user's
`m.call` (from
[MSC4426](https://github.com/matrix-org/matrix-spec-proposals/pull/4426))
profile field is:

```json
{
  "call_joined_ts": 1770140640
}
```

and the following `m.call` update arrives:

```json
{}
```

the receiving client must update the local state for that user's field to `{}`.

This is in contrast to treating every inner field as a "diff", assuming "no
`call_joined_ts` means the field is unchanged from before". This simplifies the
processing logic for these fields. Recall that the value of profile fields may
have any JSON value (including simply a string, in the case of `m.tz`).

### Filtering profile updates by field ID

Clients must *opt-in* to receive these updates. The bandwidth required would be
wasted on older clients, or clients that don't have any features that make use
of these real-time updates.

Controlling what information is returned by `/sync` is done via
[Filtering](https://spec.matrix.org/v1.17/client-server-api/#filtering). A new
possible field, `profile_fields`, is added to filters. It has a single key,
`ids`, that is a list of strings representing profile field IDs. For
example:

```json
{
  "profile_fields": {
    "ids": ["m.status", "displayname", "avatar_url"]
  }
}
```

The default value for `profile_fields.ids` (if it is not set) is `[]`, meaning no
profile field updates will be returned. The `/sync` endpoint MUST only return
profile fields which the client explicitly asks for using a filter.

Using a nested field allows for additional fields to be added later. For
instance, a future MSC may add a `dms_only` field which filters profile field
updates to only those from users you share a DM with, or a `users` field to
filter updates by specific user IDs.

### Scope of profile updates

Homeservers SHOULD include updates for all users that a user shares a room with
- however it is left up to implementations if they wish to restrict that set
further by default. Homeservers SHOULD NOT send profile updates for users who do
not share at least one room (lest you receive updates for the entire
federation).

Filtering updates by user or room ID is left out of scope for this
proposal (and would be better served by sliding sync).

Updates made since the last `since` token MUST be returned to clients. If
multiple updates have happened since the provided `since` token, only the latest
update should be returned. A `/sync` request with no `since` token MUST have all
*current* profile field values sent to the client (in line with the `ids` they
requested).

## Implementation notes

The following are implementation-specific recommendations.

### Homeservers

Legacy sync works by having the client provide the `next_batch` token as the
`since` query parameter in the next request. This allows the homeserver to track
which changes the client has yet to see. This does not mean homeservers now need
to track historical values of profiles - users will typically only ever care
about the latest profile information for another user.

Homeservers may instead assign every profile update an incrementing identifier,
and compare that against an identifier stored within the provided `since` token
to know whether a client has yet to receive a given profile update.

### Clients

Upon login, clients will make a single legacy `/sync` request with no `since`
parameter - fetching *all* initial client state. This is colloquially known as
an "initial sync".

A client could naively fetch all profile field values it's interested in for all
other users on startup. However, this could potentially include a huge amount of
data - that the user may not even see. Fetching that information would also
extend the already long waiting times for an initial sync to complete.

Instead, it may be more efficient for a client to use the one-off [`GET
/_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3profileuseridkeyname)
endpoint to get the initial state of a user's profile field the first time it's
seen, while waiting for updates to come down via incremental (non-initial)
syncs.

## Potential issues

None identified.

## Alternatives

Clients could poll the profile fields of other users every N seconds. This would
result in both a large number of client requests, as well as a lag of up to N
seconds for a client to be made aware of a change in a user's profile.

## Security considerations

This proposal does not expose any more user information than which could already
be fetched by the existing profile endpoints.

This proposal does add more work for the homeserver to do when handling each
`/sync` request. This is considered acceptable, and the proposal provides tips
for implementors to reduce the load on the homeserver when making use of the
feature.

## Unstable prefix

Until this proposal is accepted, implementations should use the following
unstable prefixes:

| **Identifier** | **Unstable** |
|----------------|--------------|
| `users` /sync field | `org.matrix.msc4429.users` |
| `profile_fields` Filter field | `org.matrix.msc4429.profile_fields` |

Homeservers SHOULD add an unstable feature flag to the response of [`GET
/_matrix/client/versions`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientversions)
with the following format:

```json
{
  // ...
  org.matrix.msc4429: true
}
```

A value of `true` indicates experimental support for this proposal has been
implemented. `false`, or the field being absent, means experimental support for
the feature is not implemented.

After this feature has been stabilised, but not yet included in a stable Matrix
spec release, homeservers SHOULD add the field `org.matrix.msc4429.stable` to
the `/versions` response body. This allows clients to know that they can use the
stable field identifiers, even if the homeserver does not yet advertise support
for the Matrix spec version that this proposal ends up landing in. A value of
`true` indicates support for the stable fields.

## Dependencies

None.
