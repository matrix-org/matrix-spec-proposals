# MSC4155: Invite filtering

Matrix supports ignoring users via the eponymous [module] and the `m.ignored_user_list` account data
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

All properties in `content` are optional arrays. A missing or `null` property MUST be treated like an
empty array. The array elements are [glob expressions] to be matched against user IDs and server names,
respectively.

When evaluating an invite against the contents of `m.invite_permission_config`, implementations should
apply the following order:

1.  If the invite matches any `allow_*` setting, stop processing and allow.
2.  If the invite matches any `ignore_*` setting, stop processing and ignore.
3.  If the invite matches any `block_*` setting, stop processing and block.
4.  Otherwise allow.

The semantics of "ignore" and "block" follow [MSC4283] which means ignoring hides the invite with no
feedback to the inviter whereas blocking rejects the invite.

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

Servers SHOULD enforce `m.invite_permission_config` against incoming invites but MAY also delegate
the task to clients to allow them to let users review ignored and blocked invites. Clients MUST
enforce the permission config, if their server doesn't do it. In either case, servers MUST communicate
their behaviour to clients through a new capability `m.invite_permission_config_enforced`.

```json5
{
  "capabilities": {
    "m.invite_permission_config_enforced": {
      "enabled": true
    }
  }
}
```

If `enabled` is set to `true`, the server enforces the permission config. If the capability is missing,
clients SHOULD behave as if `enabled` was set to `false`.


## Potential issues

None.


## Alternatives

A comprehensive comparison of existing invite filtering proposals may be found in [MSC4192]. The
present proposal is functionally inferior to some of the alternatives outline there. It does, for
instance, not cover the change history of the permission config or sharing the config among different
users. The proposal is, however, a straightforward and easy to implement extension of the existing
`m.ignored_user_list` mechanism. See also [this comment] for further details.


## Security considerations

None.


## Unstable prefix

Until this proposal is accepted into the spec, implementations should refer to `m.invite_permission_config`
and `m.invite_permission_config_enforced` as `org.matrix.msc4155.invite_permission_config` and
`org.matrix.msc4155.invite_permission_config_enforced`, respectively. Note that the [gematik specification],
which predates this MSC, uses an event type of `de.gematik.tim.account.permissionconfig.v1` and
a different event schema.


## Dependencies

This proposal depends on [MSC4283] for the semantics of "ignore" and "block".


[gematik specification]: https://github.com/gematik/api-ti-messenger/blob/9b9f21b87949e778de85dbbc19e25f53495871e2/src/schema/permissionConfig.json
[glob expressions]: https://spec.matrix.org/v1.14/appendices/#glob-style-matching
[MSC4192]: https://github.com/matrix-org/matrix-spec-proposals/pull/4192
[MSC4283]: https://github.com/matrix-org/matrix-spec-proposals/pull/4283
[module]: https://spec.matrix.org/v1.10/client-server-api/#ignoring-users
[this comment]: https://github.com/matrix-org/matrix-spec-proposals/pull/4192#discussion_r2025188127
