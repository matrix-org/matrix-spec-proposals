# MSC4192: Comparison of proposals for ignoring invites

Matrix supports ignoring specific users via the eponymous [module] and the
`m.ignored_user_list` account data event.

```json5
{
  "type": "m.ignored_user_list"
  "content": {
    "ignored_users": {
      "@someone:example.org": {}
    }
  },
}
```

Servers MUST NOT forward invites from ignored users to clients. For the
purposes of ignoring invites, this feature is, however, quite limiting
because:

* Ignoring users also hides their events in existing rooms which might not
  be desirable
* There's no support for globs or wildcards
* The module only supports block-list but no allow-list semantics
* Users cannot review or unignore specific ignored invites
* There's no built-in concept of sharing ignore lists between users

Several attempts at designing a scheme for ignoring invites specifically
have been made so far. This documents provides a brief comparison of the
different proposals and serves as an entry point for further research.


## [MSC2270] – Proposal for ignoring invites

A new account data event `m.ignored_room_list` is introduced. The event
has the exact same semantics as `m.ignored_user_list` but tracks room IDs
rather than user IDs.

```json5
{
  "type": "m.ignored_room_list"
  "content": {
    "ignored_rooms": {
      "!something:example.org": {}
    }
  },
}
```

A key drawback of this scheme is that it's not possible to blanketly ignore
invites from specific users or servers. Spammers could, therefore, send
invites repeatedly.


## [MSC3840] – Ignore invites

A new account data event `m.ignored_invites` is introduced. The event has
separate fields for ignoring invites:

- From specific users
- From specific servers
- Into specific rooms
- Into specific rooms by specific users

```json5
{
  "type": "m.ignored_invites"
  "content": {
    "ignored_user_ids": {
      "@someone:example.org": {
        "ts": 1726138169160,
        "reason": "..."
      },
    },
    "ignored_servers": {
      "example.org": {
        "ts": 1726138169160,
        "reason": "..."
      },
    },
    "ignored_room_ids": {
      "!something:example.org": {
        "ts": 1726138169160,
        "reason": "..."
      },
    },
    "ignored_invites": {
      "!something:example.org": {
        "@someone:example.org": {
          "ts": 1726138169160,
          "reason": "..."
        },
      },
    },
  },
}
```

A key improvement over [MSC2270] is the ability to ignore entire users
and servers.

Contrary to `m.ignored_user_list` and [MSC2270], `m.ignored_invites` is
handled exclusively on the client side. This allows users to review and
unignore ignored invites but also means that ignored invites will be
repeated in `/sync` which can cause performance issues over time.


## [MSC4155]: Invite filtering

A new account data event `m.invite_permission_config` is introduced to
maintain a configuration for invite filtering with:

- A global default to allow / block all invites
- Per-user & per-server exceptions that override the default

```json5
{
  "type": "m.invite_permission_config",
  "content": {
    "default": "allow | block",
    "user_exceptions": {
      "@someone:example.org": {},
      ...
    },
    "server_exceptions": {
      "example.org": {},
      ...
    }
  }
}
```

Similar to [MSC3840], this scheme allows to ignore entire users and servers.
A key advantage though is the ability to create both block-list and allow-list
configurations.

Unlike [MSC3840], processing the ignore configuration can happen on either the
client or the server.


## [MSC3847] – Ignoring invites with policy rooms

The invite filtering configuration is tracked in [moderation policy lists].
These are already part of the spec and allow formulating glob rules against
users, rooms and servers via state events in a policy room.

```json5
{
  "type": "m.policy.rule.user | m.policy.rule.room | m.policy.rule.server",
  "state_key": "...arbitrary...",
  "content": {
    "entity": "@someone:example.org | !abcdefg:example.org | example.org | *example.org",
    "reason": "...",
    "recommendation": "m.ban"
  }
}
```

Users can hook into policy rooms for invite filtering via a new account data
event `m.policies` which defines:

- A room into which the user will write their own custom policy rules (`target`)
- A list of policy rooms to be executed against invites (`sources`). This
  should generally include `target` but may also list other rooms such as
  policy rooms recommended by the home server.

```json5
{
  "type": "m.policies",
  "content": {
    "m.ignore.invites": {
      "target": "!my-policies:example.org",
      "sources": [
        "!my-policies:example.org",
        "!bobs-policies:example.org"
      ]
    }
  }
}
```

Unlike the previous proposals, the ignore configuration can easily be shared
and reused across different users.

Another key advantage is the ability to match users, rooms and servers against
glob expressions. This could probably be added into the other proposals as well,
however.

Similar to [MSC3840], the ignore configuration is processed exclusively on the
client which comes with the same advantages and disadvantages.

Finally, when combined with [MSC4150], this scheme also allows for allow-list
configurations.


## [MSC3659] – Invite Rules

A system akin to push rules is defined. Rules are stored as a flat list
in a new account data event `m.invite_rules`.

Each rule has a type that is accompanied with additional data to determines
how the rule matches against invites. Rule types include:

- `m.user`, accompanied with a field `user_id` that matches against a user
  ID glob expression
- `m.target_room_id`, accompanied with a field `room_id` that matches against
  a room ID glob expression
- `m.shared_room`, accompanied with a field `room_id` that matches if the
  inviter and invitee already share a specific room

Each rule is accompanied with two actions. One is to be executed if the rule
matches, the other if the rule fails. Actions must have one of the values
`allow`, `deny` and `continue`. `allow` and `deny` permit and reject the
invite, respectively, and terminate the rulelist evaluation. `continue` skips
ahead to the next rule in the list.

```json5
{
  "type": "m.invite_rules",
  "content": {
    "rules": [{
      "type": "m.user",
      "user_id": "*:badguys.com",
      "pass": "deny",
      "fail": "continue"
    }, {
      "type": "m.target_room_id",
      "room_id": "*:badguys.com",
      "pass": "deny",
      "fail": "continue"
    }, {
      "type": "m.user",
      "user_id": "@someone:example.org",
      "pass": "allow",
      "fail": "continue"
    }]
  }
}
```

Similar to [MSC3847] glob expressions as well as block-list and allow-list
configurations are supported.


## [MSC4264] – Tokens for Contacting Accounts

This proposal adapts the subaddressing functionality known from email to
Matrix IDs. Users manage a set of "tokens" which are extensions of their
MXIDs, e.g. in the form `@localpart::token:domain`. Invites are only processed
when they include a valid token.


## Summary

The table below compares the proposals in terms of different features. It's
worth noting that some features such as glob matching could easily be extended
to all proposals.

|                      | [MSC2270] | [MSC3840] | [MSC4155]     | [MSC3847]           | [MSC3659] | [MSC4264]     |
|----------------------|-----------|-----------|---------------|---------------------|-----------|---------------|
| Ignore room          | ✅        | ✅        | ❌            | ✅                  | ✅        | ❌            |
| Ignore user          | ❌        | ✅        | ✅            | ✅                  | ✅        | ✅            |
| Ignore server        | ❌        | ✅        | ✅            | ✅                  | ✅        | ❌            |
| Glob matching        | ❌        | ❌        | ❌            | ✅                  | ✅        | ❌            |
| Client-side          | ❌        | ✅        | ✅ (optional) | ✅                  | ❌        | ✅ (optional) |
| Block-list semantics | ✅        | ✅        | ✅            | ✅                  | ✅        | ❌            |
| Allow-list semantics | ❌        | ❌        | ✅            | ✅ (with [MSC4150]) | ✅        | ✅            |


[moderation policy lists]: https://spec.matrix.org/v1.11/client-server-api/#moderation-policy-lists
[module]: https://spec.matrix.org/v1.10/client-server-api/#ignoring-users
[MSC2270]: https://github.com/matrix-org/matrix-spec-proposals/pull/2270
[MSC3659]: https://github.com/matrix-org/matrix-spec-proposals/pull/3659
[MSC3840]: https://github.com/matrix-org/matrix-spec-proposals/pull/3840
[MSC3847]: https://github.com/matrix-org/matrix-spec-proposals/pull/3847
[MSC4150]: https://github.com/matrix-org/matrix-spec-proposals/pull/4150
[MSC4155]: https://github.com/matrix-org/matrix-spec-proposals/pull/4155
[MSC4264]: https://github.com/matrix-org/matrix-spec-proposals/pull/4264
