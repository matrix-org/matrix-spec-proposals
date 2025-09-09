# MSC4155: Invite filtering

Matrix supports ignoring users via the ["Ignoring Users" module] and the `m.ignored_user_list` account data
event. This is a nuclear option though and will suppress both invites and room events from the ignored
users. Additionally, the `m.ignored_user_list` event only allows for block-list configurations that ignore
specific users but doesn't have a mechanism to ignore entire servers. These shortcomings make the module
insufficient for use cases such as tightly locked down applications where ignoring needs to be the default
behaviour.

This proposal generalises the ignoring users [module] to allow filtering invites specifically. The scheme
outlined below was conceptually borrowed from the [gematik specification].


## Proposal

To allow users to configure which other users are allowed to invite them into rooms, a new account data
event `m.invite_permission_config` is introduced.

```json5
{
  "type": "m.invite_permission_config",
  "content": {
    // Global on/off toggle
    "enabled": true,
    // User-level settings
    "allowed_users": [ "@john:goodguys.org", ... ],
    "ignored_users": [ ... ],
    "blocked_users": [ ... ],
    // Server-level settings
    "allowed_servers": [ ... ],
    "ignored_servers": [ ... ],
    "blocked_servers": [ "*" ] // A feature of all the fields at this level, globs
  }
}
```

`enabled` is a boolean property and defaults to `true` if omitted. It provides clients with a convenience on/off
toggle that lets them deactivate the configuration without purging it.

All other properties in `content` are optional arrays. The array elements are [glob expressions]. Any `*_users`
glob is to be matched against full user IDs (localpart and domain). Any `*_servers` glob is to be matched
against server names / domain parts of user IDs after stripping any port suffix. This matches the way the
globs from [server ACLs] are applied.

When evaluating an invite, implementations MUST first apply the existing `m.ignored_user_list` as per
the current spec. If the invite didn't match, implementations MUST then apply `m.invite_permission_config`.
The complete processing logic is as follows:

1.  Verify the invite against `m.ignored_user_list`:
    1.  If it matches `ignored_users`, stop processing and ignore.
2.  Verify the invite against `m.invite_permission_config`:
    1.  If `enabled` is `false`, stop processing and allow.
    2.  If it matches `allowed_users`, stop processing and allow.
    3.  If it matches `ignored_users`, stop processing and ignore.
    4.  If it matches `blocked_users`, stop processing and block.
    5.  If it matches `allowed_servers`, stop processing and allow.
    6.  If it matches `ignored_servers`, stop processing and ignore.
    7.  If it matches `blocked_servers`, stop processing and block.
3.  Otherwise, allow.

The semantics of "ignore" and "block" follow [MSC4283] which means ignoring hides the invite with no
feedback to the inviter whereas blocking rejects (or refuses, in the case of servers) the invite.

When blocking an inviter, the server must respond to the following endpoints with an error:

- `PUT /_matrix/federation/(v1|v2)/invite/{roomId}/{eventId}`
- `POST /_matrix/client/v3/rooms/{roomId}/invite`
- `POST /_matrix/client/v3/createRoom` (checking the `invite` list)
- `PUT /_matrix/client/v3/rooms/{roomId}/state/m.room.member/{stateKey}` (for invite membership)

The error SHOULD be `M_INVITE_BLOCKED` with a HTTP 403 status code.

When ignoring an invite, these endpoints MUST handle an invite normally as if accepted. However, the server
MUST not include the invite down client synchronization endpoints such as `GET /_matrix/client/v3/sync` or
MSC4186's sliding sync endpoint. In addition, these invites MUST be ignored when calculating push notifications.
For clarity, this means that the invited user will get a regular `invite` membership event in the target room
but will never be notified about that event. Similar, to `m.ignored_user_list`, clients SHOULD perform an
initial `/sync` after relaxing their ignore configuration in order to receive potentially pending invites.

Otherwise, all other endpoints (such as `GET /_matrix/client/v3/rooms/{roomId}/state`) should work as before. 

Servers are not expected to process these rules for appservice users when calculating events to send down
`PUT /_matrix/app/v1/transactions`. Appservices are not expected to be run directly by client users, and
should be able to handle their own spam prevention.

The semantics and order of evaluation enable a number of use cases, for instance:

```json5
// Invites from everyone
{
  "type": "m.invite_permission_config",
  "content": { }
}

// No invites at all
{
  "type": "m.invite_permission_config",
  "content": {
    "blocked_servers": [ "*" ]
  }
}

// Only invites from goodguys.org
{
  "type": "m.invite_permission_config",
  "content": {
    "allowed_servers": [ "goodguys.org" ],
    "blocked_servers": [ "*" ]
  }
}

// Invites from everyone except badguys.org
{
  "type": "m.invite_permission_config",
  "content": {
    "blocked_servers": [ "badguys.org" ]
  }
}

// Only invites from goodguys.org except for @notactuallyguy:goodguys.org
{
  "type": "m.invite_permission_config",
  "content": {
    "blocked_users": [ "@notactuallyguy:goodguys.org" ],
    "allowed_servers": [ "goodguys.org" ]
    "blocked_servers": [ "*" ]
  }
}

// No invites from badguys.org unless it's @goodguy:badguys.org
{
  "type": "m.invite_permission_config",
  "content": {
    "allowed_users": [ "@goodguy:badguys.org" ],
    "blocked_servers": [ "badguys.org" ]
  }
}

// Only invites from goodguys.org and don't provide feedback to reallybadguys.org
{
  "type": "m.invite_permission_config",
  "content": {
    "allowed_servers": [ "goodguys.org" ],
    "ignored_servers": [ "reallybadguys.org" ],
    "blocked_servers": [ "*" ]
  }
}
```

Servers MUST enforce `m.invite_permission_config` against incoming new invites. Additionally, Servers
SHOULD apply the config against existing pending invites as well.


## Potential issues

Enforcing the permission configuration exclusively on the server means users have no way to review
processed invites. This is desirable in most cases as a spam protection measure. It does mean, however,
that if the user has accidentally blocked a good actor and is informed about it through a different
communication channel, they'll have to update their permission configuration and request a re-invite.


## Alternatives

Instead of introducing a separate account data event, the existing `m.ignored_user_list` could have
been expanded. This would, however, not only effect invites but also events in existing rooms which
makes it a much more nuclear option. Additionally, the existing schema of `m.ignored_user_list`
complicates morphing it into something that optionally supports allow-list semantics.

Regarding `m.invite_permission_config`, the split between user settings and server settings is
technically not needed because glob expressions are powerful enough to allow matching either.
Splitting them is more explicit and prevents unintended globbing mistakes, however. The fact that
a user glob and a server glob can overlap does not seem problematic because this proposal includes
a deterministic processing order for all settings.

A previous version of this proposal included a base setting of block / allow all with user and
server exceptions applied on top. In this scheme, flipping the base setting also inverts the semantics
of all exceptions, however, which makes changing the configuration quite complicated.

A comprehensive comparison of existing invite filtering proposals may be found in [MSC4192]. The
present proposal is functionally inferior to some of the alternatives outline there. It does, for
instance, not cover the change history of the permission config or sharing the config among different
users. The proposal is, however, a straightforward and easy to implement extension of the existing
`m.ignored_user_list` mechanism. See also [this comment] for further details. This proposal is additionally
extensible for further types of blocking in the future. For example, a future MSC could create definitions
and behaviours to block/ignore/allow invites from contacts, of a particular type (DM, space, etc), 
to a particular room, or even with given keywords.


## Security considerations

None.


## Unstable prefix

Until this proposal is accepted into the spec, implementations should refer to `m.invite_permission_config`
and `m.invite_permission_config_enforced` as `org.matrix.msc4155.invite_permission_config` and
`org.matrix.msc4155.invite_permission_config_enforced`, respectively. Note that the [gematik specification],
which predates this MSC, uses an event type of `de.gematik.tim.account.permissionconfig.v1` and
a different event schema.

The error `M_INVITE_BLOCKED` should be `ORG.MATRIX.MSC4155.M_INVITE_BLOCKED` until this proposal is accepted into the spec.
## Dependencies

This proposal loosely depends on [MSC4283] for the semantics of "ignore" and "block".


[gematik specification]: https://github.com/gematik/api-ti-messenger/blob/9b9f21b87949e778de85dbbc19e25f53495871e2/src/schema/permissionConfig.json
[glob expressions]: https://spec.matrix.org/v1.14/appendices/#glob-style-matching
[MSC4192]: https://github.com/matrix-org/matrix-spec-proposals/pull/4192
[MSC4283]: https://github.com/matrix-org/matrix-spec-proposals/pull/4283
["Ignoring Users" module]: https://spec.matrix.org/v1.10/client-server-api/#ignoring-users
[this comment]: https://github.com/matrix-org/matrix-spec-proposals/pull/4192#discussion_r2025188127
[server ACLs]: https://spec.matrix.org/v1.15/client-server-api/#mroomserver_acl
