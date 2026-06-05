# MSC4429: Profile Updates for Legacy Sync

[Custom profile
fields](https://spec.matrix.org/v1.17/client-server-api/#profiles) allow users
to attach arbitrary data to their public user information. This can be anything
from a timezone (`m.tz`) to whether the user is currently in the office (e.g.
[MSC4426](https://github.com/matrix-org/matrix-spec-proposals/pull/4426)).

Clients may wish to display these fields without user interaction. For example,
the `emoji` field from
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
optional field, `profile_fields`, is added to filters. It has a single key,
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

Updates made since the last `since` token MUST be returned to clients. If
multiple updates have happened since the provided `since` token, only the latest
update should be returned. A `/sync` request with no `since` token MUST have all
*current* profile field values sent to the client (in line with the `ids` they
requested).

### Displaying profile information initially

When a client builds a timeline of users and events to display to the user, it
should be able to show relevant profile information for every user. However, if
the homeserver only ever communicates profile *updates* down `/sync`, then a
client wouldn't show any information for a given user until they update their
profile.

To bridge this gap, homeservers MAY communicate fields from a user's profiles to
a client using the `users.<user_id>.profile_fields` `/sync` entry; even if those
fields have not been updated recently. This may be useful if, for instance, a
user has just joined a room with users that it hasn't seen before. The client
should be able to display appropriate profile field information immediately
without having to query the homeserver for each new user's profile.

### Lazy-loading user profiles

To help reduce the number of user profiles that would be returned in a `/sync`
response, homeservers MAY send a reduced set of profile information to clients
when [lazy-loading room
members](https://spec.matrix.org/v1.18/client-server-api/#lazy-loading-room-members)
is enabled. The rationale is that there's little point in sending profile
information about a user if a client won't actually display them yet.

## Implementation notes

The following are implementation-specific recommendations.

### Homeservers

Legacy sync works by having the client provide the `next_batch` token as the
`since` query parameter in the next request. This allows the homeserver to track
which changes the client has yet to see. This does not mean homeservers now need
to track the history of profiles - users will typically only ever care
about the latest profile information for another user.

Homeservers may instead assign every profile update an incrementing identifier,
and compare that against an identifier stored within the provided `since` token
to know whether a client has yet to receive a given profile update.

Ensuring that clients have a coherent copy of all other user profiles is
especially nuanced. One implementation path is to include profiles (filtered to
only the fields the client asks for) of users during an initial sync, so that
the client has access to profile information without needing to wait for an
update to occur. But returning these profiles, especially on an initial sync,
can lead to a lot of data being returned.

Homeservers should encourage clients to enable lazy-loading, on initial and
incremental syncs, and then only send down profile information for relevant
users (i.e. the `senders` of events in the sync response, room heroes, etc.).
This is similar to how lazy-loading memberships work; sending the membership of
every user in every room to the client is unnecessary if the client will only
display the last X events in the room.

Even then, a DM with a given user will result in multiple incremental syncs with
events from a single user; and thus their profile being returned over and over
again. This can be alleviated by the homeserver maintaining a lossy cache of
which user profile fields it has already communicated to a given user_id/device_id
combination. This lessens the number of redundant user profiles that are
communicated. It's OK if the cache is lossy (evicted based on size/time/etc.) as
the worst that will happen is a redundant profile is sent to the client.

These injections of *current* user profiles allows a client to always display
the profile information for a user, even if it hasn't changed recently.

Profile *updates*/diffs should *always* be sent in an incremental sync response.
They're naturally infrequent enough that there's little need to filter them with
the currently defined use cases.

### Clients

Clients are recommended to enable lazy-loading in their `/sync` requests to
limit the profile information to only those users that are initially relevant
(i.e. senders of events that are initially returned to the client).

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
