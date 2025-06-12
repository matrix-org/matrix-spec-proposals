# MS4299: Trusted Users

Currently, Matrix has a way to assign specific users as "ignored", declaring to both your client and server that you
would not like to interact with a given user, and in some situations would not like them to interact with you.
However, there is no mechanism to do the inverse - assign specific users as "trusted", even more so define what
"trusted" even means. This proposal will aim to tackle both of these issues, while allowing for plenty of
expansion in the future as needs of the protocol change.

## Proposal

For clarity's sake, the following words are used with the associated context throughout this proposal:

- Ignored: (users that are ignored OR blocked)[2]
- Non-trusted: users who are neither trusted nor ignored (the default state)
- Trusted: users who are explicitly added to the trusted users account data object

While this proposal does not aim to tackle what to *do* with user trust (that's for followup MSCs to define), it lays
the foundations for defining that a user can be "trusted" at all.

Currently, we already have [the ignored users list][1], which allows you to define which users you never want to see.
This proposal introduces a "trusted users list", which behaves semantically similarly to the ignored users list,
but the inverse. Clients and servers may wish to give "trusted" users special treatment, like they currently do
with ignored users. Examples include (but are not limited to) servers filtering invites to only allow trusted users to
send them, clients disabling media previews and only enabling them by default for trusted users, only allowing
users to initiate calls if the recipient trusts them, and preventing profile fields
(display name, avatar, custom fields) being sent to non-trusted users.

Clients can create an account data entry with the type `m.trusted_users`, with the following format:

```json
{
    "trusted_users": {
        "@user1:example.com": {},
        "@user2:example.com": {}
    }
}
```

This event's content should be an object, whose keys are fully qualified user IDs.
Note that here, the objects following the trusted user IDs (hereon referenced as the "trust configuration") are
empty objects - this is to allow for namespaced fields to be added by later MSCs to further extend the capabilities
of trust.

An **example** of an extended trust configuration could be:

```json
{
    "trusted_users": {
        "@user1:example.com": {
            "com.example.allow_custom_colours": true
        },
        "@user2:example.com": {}
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

- [MSC4155](4155) implements invite filtering by defining allowed/ignored/blocked users & servers. The allow function
  of that proposal has potentially overlapping functionality and semantics with this one, although lacks the future
  extensibility that this one aims to provide. Contrarily, 4155 could be used to build on top of this one.
- Doing away with ignores, and instead only using trusts, and adding the ability to mark a trust as an ignore/untrust,
  or some other semantically similar meaning. This would be complicated and just generally expensive


## Unstable prefix

Until this proposal is accepted, implementations should make use of the account data event type
`uk.timedout.msc4299.trusted_users`, instead of `m.trusted_users`.

