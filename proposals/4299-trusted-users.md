# MS4299: Trusted Users

> TODO: *trusted* is misleading and conflicting

Currently, Matrix has a way to assign specific users as "ignored", declaring to both your client and server that you
would not like to interact with a given user, and in some situations would not like them to interact with you.
However, there is no mechanism to do the inverse - assign specific users as "trusted", even more so define what
"trusted" even means. This proposal will aim to tackle both of these issues, while allowing for plenty of
expansion in the future as needs of the protocol change.

## Proposal

For clarity's sake, the following words are used with the associated context throughout this proposal:

- Entity/Entities: something that matches an entity that can be trusted (i.e. user ID, room ID, server name, glob pattern)
- Ignored: [entities that are ignored OR blocked][4283]
- Non-trusted: entities who are neither trusted nor ignored (the default state)
- Trusted: entities who are explicitly added to the trusted users account data object

> TODO: users -> entities

While this proposal does not aim to tackle what to *do* with user trust (that's for followup MSCs to define), it lays
the foundations for defining that an entity can be "trusted" at all.

Currently, we already have [the ignored users list][1], which allows you to define which users you never want to see.
This proposal introduces a "trusted users list", which behaves semantically similarly to the ignored users list,
but the inverse. Clients and servers may wish to give "trusted" users special treatment, like they currently do
with ignored users. Examples include (but are not limited to) servers filtering invites to only allow trusted users to
send them, clients disabling media previews and only enabling them by default for trusted users, only allowing
users to initiate calls that reach the recipient if the recipient trusts them, and preventing profile fields
(display name, avatar, custom fields) being sent to non-trusted users. However, these capabilities are not defined in
this proposal itself.

Clients can create an account data entry with the type `m.trusted_users`, with the following format:

```json5
{
    "trusted_users": {
        "@user1:example.com": {}, // specific user
        "@*:example.com": {},  // all users matching the glob pattern
        "example.com": {},  // all users on the homeserver example.com
        "!roomid:example.com": {},  // all members of the specified room
    }
}
```

> TODO: restrict globs to server names (i.e. wildcard domains) and user IDs?

This event's content should be an object, whose keys are generic strings that are intended to represent an entity.
Note that here, the objects following the trusted entities (hereon referenced as the "trust configuration") are
empty objects - this is to allow for namespaced fields to be added by later MSCs to further extend the capabilities
of trust (such as aforementioned examples).

An **example** of an extended trust configuration could be:

```json
{
    "trusted_users": {
        "@user1:example.com": {
            "com.example.allow_custom_colours": true
        },
        "@*:example.com": {}
    }
}
```

If a user does not trust any users, their account data would look like `{"trusted_users": {}}`.

A user **must not** be ignored *and* trusted, they are  mutually exclusive states.
In the event that there is a desynchronisation between the ignored users account data, and the trusted users
account data, the ignored users should take priority over trusted users.
Servers *should not* automatically remove trust from users when the client asks to ignore them, nor vice versa.
Clients *should*, consequently, attempt to atomically remove trust before attempting to ignore

## Potential issues

As this MSC aims to target functionality both in clients and in servers, there are likely to be inconsistencies in
the implementations. Hopefully, by not defining any actual uses for trust in this MSC, and instead relying on them
being proposed in followup proposals, servers will be able to advertise support for their individual functionalities,
and clients will be able to feature-gate appropriately.

This proposal also has potentially overlapping behaviour with other proposals, see the alternatives section below.

Due to ignores and trusts being mutually exclusive, there is the risk that they will become desynchronised, and
have overlapping entries. As defined above, ignores should take priority over trusts.

## Alternatives

- [MSC4155][4155] implements invite filtering by defining allowed/ignored/blocked users & servers. The allow function
  of that proposal has potentially overlapping functionality and semantics with this one, although lacks the future
  extensibility that this one aims to provide. Contrarily, 4155 could be used to build on top of this one.
- Doing away with ignores, and instead only using trusts, and adding the ability to mark a trust as an ignore/untrust,
  or some other semantically similar meaning. This would be complicated and just generally expensive
  
## Security Considerations

- Server-side manipulation: a homeserver's administrators are able to modify account data without notice, which could
  be used to cause unexpected client/server behaviour. The aforementioned URL preview example
  [was already a CVE in matrix-react-sdk][CVE-2024-42347], so additional care must be taken when considering followup
  capabilities.

## Unstable prefix

Until this proposal is accepted, implementations should make use of the account data event type
`uk.timedout.msc4299.trusted_users`, instead of `m.trusted_users`.

[1]: https://spec.matrix.org/unstable/client-server-api/#mignored_user_list
[4283]: https://github.com/matrix-org/matrix-spec-proposals/pull/4283
[4155]: https://github.com/matrix-org/matrix-spec-proposals/pull/4155
[CVE-2024-42347]: https://github.com/matrix-org/matrix-react-sdk/security/advisories/GHSA-f83w-wqhc-cfp4

## Dependencies

None.
