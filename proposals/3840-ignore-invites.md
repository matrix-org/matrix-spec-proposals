# MSC3840: Ignoring invites

Matrix supports an event "m.ignored_user_list" to entirely ignore some users.

In some cases, ignoring the user is the wrong granularity, e.g. we may wish to:

- ignore invites to rooms entirely;
- ignore invites from some servers entirely.

While both features are pretty easy to implement client-side, standardizing how this preference
is stored as part of the account is necessary to make sure that users can share this ignore list
across devices and sessions.

## Proposal


Matrix currently supports a type `m.ignored_users_list` with content:

| Content | Type | Description |
|---------|------|-------------|
| `ignored_users` | A maps of user ids to `{}` | A list of users to ignore |


We adopt a similar `m.ignored_invites` with content:

| Content | Type | Description |
|---------|------|-------------|
| `ignored_user_ids`   | optional map `UserId` => `IgnoreMetadata` | Ignore invites from these users. |
| `ignored_servers`    | optional map `domain` => `IgnoreMetadata` | Ignore invites from users in these homeservers. |
| `ignored_room_ids`   | optional map `RoomId` => `IgnoreMetadata` | Ignore invites towards these rooms. |
| `ignored_invites`    | optional map `RoomId` => map `UserId` => `IgnoreMetadata` | Ignore specific invites. |

where `IgnoreMetadata` is

| Content    | Type   | Description |
|------------|--------|-------------|
| `ts`       | timestamp | The instant at which the invite was received. Used for visual purposes (i.e. order by most recent) and/or cleanup. |
| `reason`   | optional string | A human-readable reason for ignoring the invite. |

### Client behaviour

If a user modifies `m.ignored_invites`, discard silently any matching pending invite
currently displayed.

### Server behaviour

None.

This is handled entirely client-side.

## Potential issues

### Event size

There is a risk that the list of ignored invites of some users may grow a lot, which might have
performance impact, both during initial sync and during filtering. We believe that this risk is
limited. If necessary, clients may decide to cleanup ignored invites after some time.

### Sync size

With this proposal, the server will repeat invites at each `/sync`. In time, this can grow expensive.

If necessary, clients may decide to convert ignored invites into rejected invites after a while.

## Alternatives

### Server-side filtering

Just as `m.ignored_users_list` is handled mostly on the server, we could handle `m.ignored_invites`
largely on the server. However, this would make it much harder to undo erroneous ignores (i.e.
implementing some sort of recovery from trashcan) on the client.

So we prefer handling things on the client, even if this may require more traffic.

## Security considerations

Can't think of any right now.

## Unstable prefix

During testing, `m.ignored_invites` should be prefixed `org.matrix.msc3840.ignored_invites`.

Fields `ignored_user_ids`, `ignored_servers`, `ignored_room_ids` of this new event should remain unprefixed.

