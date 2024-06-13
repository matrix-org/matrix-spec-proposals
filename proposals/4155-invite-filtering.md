# MSC4155: Invite filtering

Matrix supports ignoring users via the eponymous [module] and the `m.ignored_user_list` account data
event. This is a nuclear option though and will suppress both invites and room events from the ignored
users. Additionally, the `m.ignored_user_list` event only allows for block-list configurations that ignore
specific users but doesn't have a mechanism to ignore entire servers. These shortcomings make the module
insufficient for use cases such as tightly locked down applications where ignoring needs to be the default
behaviour.

This proposal generalises the ignoring users [module] to allow filtering invites specifically. The scheme
outlined below is conceptually borrowed from the [gematik specification]. The main purpose of this proposal
is to ensure that this option is available for comparison with [other existing MSCs] that attempt to address
invite filtering.


## Proposal

To allow users to configure which other users are allowed to invite them into rooms, a new account data
event `m.invite_permission_config` is introduced.

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

The `default` field defines the standard setting that is applied to all invites that don't match an
exception. Exceptions invert the default setting and are provided via the `user_exceptions` and
`server_exceptions` fields which follow the format of the `ignored_users` field in `m.ignored_user_list`.

As an example, a block-list configuration that ignores invites from `@badguy:scam.org` but allows invites
from any other user would look like this:

```json5
{
  "type": "m.invite_permission_config",
  "content": {
    "default": "allow",
    "user_exceptions": {
      "@badguy:scam.org": {},
    }
  }
}
```

In contrast, an allow-list configuration that permits invites from users on goodguys.org but blocks invites
from all other servers would look like this:

```json5
{
  "type": "m.invite_permission_config",
  "content": {
    "default": "block",
    "server_exceptions": {
      "goodguys.org": {},
    }
  }
}
```

Note that since the default setting for entities that don't match an exception is part of the configuration,
an exception for a user does _not_ need to be accompanied by an exception for their server[^1].

Servers MAY suppress invites for which the configuration evaluates to `block` and not send them to the recipient.
They MAY additionally reject the invite.

Clients SHOULD hide invites from users for which the permission configuration evaluates to `block`. They MAY
allow reviewing ignored invites in a dedicated section of their UI.


## Potential issues

Larger permission configurations could run into the [event size limit] of 65536 bytes. This issue also exists
with the `m.ignored_user_list` event.


## Alternatives

As mentioned above, the main goal of this proposal is to offer an alternative so that the question of invite
filtering can be answered holistically. Therefore, this section will not attempt to make a case for why the
current proposal is better than others and instead simply list the alternatives known to the author at the
time of writing:

- [MSC2270] (which borrows from `m.ignored_user_list` to ignore rooms and invites)
- [MSC3659] (which introduces a push-rule-like grammar to filter invites)
- [MSC3840] (which is similar to this proposal but only supports block-list semantics)
- [MSC3847] (which ignores invites by building on [moderation policy lists] and could be combined with
  [MSC4150] to support both block-list and allow-list use cases)


## Security considerations

None.


## Unstable prefix

Until this proposal is accepted into the spec, implementations should refer to `m.invite_permission_config`
as `org.matrix.msc4155.invite_permission_config`. Note that the [gematik specification], which predates
this MSC, uses an event type of `de.gematik.tim.account.permissionconfig.v1` and slightly different field
names. Given that the general JSON scheme of the event is the same though, implementations of the
[gematik specification] should largely be equivalent to implementations of this MSC.


## Dependencies

None.


[^1]: This is in contrast to e.g. [Mjolnir] which requires two `org.matrix.mjolnir.allow` rules, one for
      the user ID and one for the server name, to build an allow list that only permits a single user.

[event size limit]: https://spec.matrix.org/v1.10/client-server-api/#size-limits
[gematik specification]: https://github.com/gematik/api-ti-messenger/blob/9b9f21b87949e778de85dbbc19e25f53495871e2/src/schema/permissionConfig.json
[Mjolnir]: https://github.com/matrix-org/mjolnir
[MSC2270]: https://github.com/matrix-org/matrix-spec-proposals/pull/2270
[MSC3659]: https://github.com/matrix-org/matrix-spec-proposals/pull/3659
[MSC3840]: https://github.com/matrix-org/matrix-spec-proposals/pull/3840
[MSC3847]: https://github.com/matrix-org/matrix-spec-proposals/pull/3847
[MSC4150]: https://github.com/matrix-org/matrix-spec-proposals/pull/4150
[moderation policy lists]: https://spec.matrix.org/v1.10/client-server-api/#moderation-policy-lists
[module]: https://spec.matrix.org/v1.10/client-server-api/#ignoring-users
[other existing MSCs]: #alternatives
