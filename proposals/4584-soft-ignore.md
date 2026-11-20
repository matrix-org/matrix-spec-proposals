# MSC4584: Soft-ignoring

Language used is per [MSC4283](https://github.com/matrix-org/matrix-spec-proposals/pull/4283).

Currently, ignoring a user is done on the server, as per 10.26.3 of the Client-Server API. This
means that a client gets no say in how to present an ignore: it just happens, and the client can't
really do much about it other than sync. Servers may even reject invites (making this behavior
closer to what a user might think of as a block), which leaves the user with little agency.

 Other platforms present a feature where the client can _optionally_ hide
messages from a user, perhaps temporarily. A user can then optionally
show certain messages, behind a disclosure, to reveal them. For example,
[Discord](https://support.discord.com/hc/en-us/articles/28084948873623-How-to-Ignore-Users-on-Discord)
has this feature.

## Proposal

A new account data event `m.soft_ignore_config` is introduced.

```jsonc
{
  // Global on/off toggle
  "enabled": true,
  "users": {
    "@alice:example.com": "allow",
    "@mallory:example.com": "ignore",
  },
  "rooms": { "!family-group-chat": "allow" },
  "servers": { "matrix.org": "ignore" }
}
```

`enabled` is a boolean property and defaults to `true` if omitted. It provides clients with a
convenience on/off toggle that lets them deactivate the configuration without purging it.

`users` is optional, and maps [User
IDs](https://spec.matrix.org/v1.18/appendices/#user-identifiers). `rooms` is optional, and maps
[Room IDs](https://spec.matrix.org/v1.18/appendices/#room-ids). `servers` is optional, and maps
[Server Names](https://spec.matrix.org/v1.18/appendices/#server-name). All of these properties
default to `{}` if not defined.

These properties map to the values:

- `"ignore"`: Soft-ignore this entity
  Server names MUST only map to `"ignore"`
- `"allow"`: Do not soft-ignore this entity

Resolving the set of soft-blocked users MUST be determined as follows:

1. Exclude any user IDs with a server name corresponding to any server listed as `"ignore"`.
2. Include all users listed as `"allow"`
3. Exclude any users listed as `"deny"`.

Resolving the set of soft-blocked rooms MUST be determined as follows:

2. Include all rooms listed as `"allow"`
3. Exclude any rooms listed as `"deny"`.

### Client behavior

'Hiding' is client-specific behavior, and MAY look like one of these following behaviors. Behavior
may be different depending on which kind of entity is being soft-ignored.

1. Choosing not to display a message, user or room.
2. Replacing a message or room with a disclosure that the entity has been soft-ignored, with an
optional button to view the entity anyway.
3. Moving hidden rooms or users to a separate section, similar to how 'low priority' rooms, or
'rooms without spaces' are presented in clients today.

A client SHOULD find soft-ignored users and SHOULD hide messages authored by soft-ignored users.

A client SHOULD hide rooms specified in `m.direct` which correspond to a soft-ignored user.

A client SHOULD hide rooms that have been soft-ignored.

### Naming

Soft-ignoring is a name used to clarify the specific behaviors of this
feature. Clients MAY choose to use different language, but SHOULD consult
[MSC4283](https://github.com/matrix-org/matrix-spec-proposals/pull/4283) when doing so. Clients
SHOULD avoid using 'block', and MUST avoid using 'ignore' if a client also uses it to describe
[Ignoring Users](https://spec.matrix.org/v1.15/client-server-api/#ignoring-users).

## Potential issues

This could further confuse users, where use of the terms 'ignoring' and 'blocking' are not
used as consistently as they should be. To avoid these issues, this proposal is dependent on
[MSC4283](https://github.com/matrix-org/matrix-spec-proposals/pull/4283).

Making a distinction between a server-enforced ignore and a client-enforced ignore is considered by
this proposal to be much more important for users than a distinction between blocking and ignoring.
It is possible that further efforts in ignoring users move towards client-side enforcement, which
would obsolete this proposal.

However, there would likely be a concurrent effort to propose server-enforced user blocking, as
server-side enforcement is still a useful feature. It is the view of this proposal that 'client-side
ignoring' and 'server-side blocking' should become the two commonly-used actions for user hiding
behaviors in Matrix, and this proposal is designed to fit into the former.

## Alternatives

None have been found so far by this proposal's author.

## Security and safety considerations

Using soft-ignores guarantees that an ignored user can't know if they have been ignored, so this
prevents leaks. An ignored user may be able to intuit that they have been ignored through attempted
communication, but it is likely deniable.

Being able to quickly ignore and unignore users and rooms will be a benefit for user safety. For
example, if a room is encountering harmful spam, a user could soft-ignore that room, and then later
find it in their soft-ignored rooms list, and unignore it. If someone needs to 'cool down' from a
heated conversation, they could soft-ignore the other user temporarily, and then come back when they
are more level-headed. Unlike other methods of ignoring, this is instant and instantly reversible,
with no potential losses of messages or invites.

## Unstable Prefix

Until this MSC is merged, clients shall replace the following namespaces accordingly:

- `m.soft_ignore_config` => `net.f0rest.msc4584.soft_ignore_config`

## Dependencies

This MSC relies on [MSC4283](https://github.com/matrix-org/matrix-spec-proposals/pull/4283) for
clarification, but does not technically require it to be added to the specification to be useful.
