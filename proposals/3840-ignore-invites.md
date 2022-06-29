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
| `ignored_user_ids`   | optional `string[]` | Ignore invites from these users. |
| `ignored_servers`    | optional `string[]` | Ignore invites from users in these homeservers. |
| `ignored_room_ids`   | optional `string[]` | Ignore invites towards these rooms. |

### Client behaviour

If a user modifies `m.ignored_invites`, discard silently any matching pending invite
currently displayed.

### Server behaviour

Wherever the server could filter out an event because of a `m.ignored_users_list`:
- if the event is an invite; and
- if `m.ignored_invites` is present in the recipient user's account; and
- if the issuer is part of `ignored_user_ids` or the issuer is an account on `ignored_servers` or the invite room is part of `ignored_room_ids`, then filter out the event silently.

## Potential issues

There is a risk that the list of ignored invites of some users may grow a lot, which might have
performance impact, both during initial sync and during filtering. We believe that this risk is
limited. If necessary, clients may decide to cleanup ignored invites after some time.

## Alternatives

Can't think of any right now.

## Security considerations

Can't think of any right now.

## Unstable prefix

During testing, `m.ignored_invites` should be prefixed `org.matrix.msc3840.ignored_invites`.

Fields `ignored_user_ids`, `ignored_servers`, `ignored_room_ids` of this new event should remain unprefixed.

