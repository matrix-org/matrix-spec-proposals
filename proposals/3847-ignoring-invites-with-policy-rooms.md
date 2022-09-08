# MSC3847: Ignoring invites using individual policy rooms

Receiving unwanted invites is something that users currently need to live
with on the Matrix network. To alleviate this, Matrix needs a mechanism to
let users specify that they are not interested in invites from specific
users or towards specific rooms.

In this proposal, we introduce the necessary extensions to let users do
this and to let clients perform filtering of unwanted invites.

We proceed as follows:

1. We build upon the mechanism of policy rooms, introduced in [MSC2313](https://github.com/matrix-org/matrix-doc/pull/2313), and define
a user's individual policy room, which may be created on behalf of the user by
a Matrix client, and which is shared across all devices and clients of the user.
2. We build upon the mechanism of recommendations, also introduced in [MSC2313](https://github.com/matrix-org/matrix-doc/pull/2313),
and create a new recommendation for ignoring invites from a specific user, from
a specific server or towards a specific room.


## Proposal

### Background

[Matrix specs define policy rooms](https://spec.matrix.org/v1.3/client-server-api/#moderation-policy-lists).
A policy room is a room in which rules such as the following may be published:

```jsonc
{
    "type": "m.policy.rule.user", // Or `m.policy.rule.server` or `m.policy.rule.room`.
    "state_key": "rule_1",        // Arbitrary.
    "content": {
        "entity": "@alice:example.org",
        "recommendation": "m.ban",
        "reason": "undesirable behaviour"
    }
}
```

Policy rooms are designed to be associated with entire servers, communities,
individual rooms or individual users, but there is no specification
clarifying how to associate an issuer with a policy room.

### Associating policy rooms to a user

For individual users, we introduce a new event `m.policies`, designed
to be used as part of account data. This event has content:

| Content | Type | Description |
|---------|------|-------------|
| `m.ignore.invites` | `Policies` | A list of rooms in which policies should be understood as "ignore invite" lists. |

We expect that future MSCs will expand upon this event `m.policies` and
add further fields with other lists of rooms in which policies should be
understood differently. This is, however, beyond the scope of the current
MSC.

We also expect that future MSCs will expand upon this event `m.policies`
to add semantics in other positions than account data, e.g. community rooms.
This is also beyond the scope of the current MSC.

Where `Policies` is defined as:

| Content     | Type | Description |
|-------------|------|-------------|
| `target`    | Room ID            | A room in which to issue new policies. |
| `sources`   | Room ID []         | A list of rooms from which to apply new policies. Should generally include `target`. |

The expected behavior is that:

- if a user Alice has a `m.policies` with key `m.ignore.invites` and `target` R,
    then whenever Alice issues a new policy to ignore invites from their client
    or another trusted agent, this policy will be stored in room R.

- if a user Alice has a `m.policies` with key `m.ignore.invites` and `sources`
    containing room R, any client or trusted agent acting on behalf of Alice will
    monitor room R for new policies and apply the recommendations on behalf of Alice,
    interpreting such policies as "ignore invites".

### Expanding recommendations to individual events

Policy lists define three scopes `m.policy.rule.user` for rules that deal with users,
`m.policy.rule.room` for rules that deals with rooms and `m.policy.rule.server` for
rules that deal with servers.

We expand these lists with a fourth scope `m.policy.rule.event` for rules that deal
with individual events, in this case ignoring a specific invite.

### Suggested client behaviour

If a user Alice has a `m.policies` with key `m.ignore.invites` and `sources` containing
room R *and* if a new policy `m.ban` appears in R:

- any pending invite currently displayed that matches the `entity` is removed from display;
- any incoming invite that matches the `entity` is not displayed among invites.

However, clients are expected to offer the ability to look at any ignored invite,
in a manner similar to a trashcan/recycle bin/undelete mechanism for desktop file
systems.

Similarly, if a policy `m.ban` in a `m.ignore.invites` room is redacted/amended,
clients should show any invite that doesn't match any `m.ignore.invites` & `m.ban`
entities anymore.

If the client detects that one of the rooms has been upgraded, it should follow
the tombstone to the new room.

### Server behavior

None at this stage. While implementation details may differ, key `m.ignore.invites` is
designed *a priori* to be executed entirely client-side.

## Potential issues

### Number of events

There is a risk that the list of ignored invites of some users may grow a lot, which might have
performance impact, both during initial sync and during filtering. We believe that this risk is
limited. If necessary, clients may decide to cleanup ignored invites after some time.

### Sync size

With this proposal, any invite ignored with `m.ignore.invites` will still show up at each `/sync`.
In time, this can grow expensive. This is, however, necessary to be able to un-ignore invites
from the client.

We plan to file a followup MSC to introduce a `m.policies` key `m.drop.invites`, which will
ask the server to simply not send the invites during the next `/sync` operations.

## Alternatives

### Rejecting invites

A client could of course reject invites instead of ignoring them. However, experience shows that
spam/bullying tools monitor invite rejections to send invite spam. This entire MSC is meant to
offer an alternative mechanism that would close this gap and let users ignore invites without
notifying the sender.

### Server-side filtering

Just as `m.ignored_users_list` is handled mostly on the server, we could handle `m.invites.ignore`
largely on the server. However, this would make it much harder to undo erroneous ignores (i.e.
implementing some sort of recovery from trashcan) on the client.

Consequently, we prefer handling things on the client, even if this may require more traffic.

## Security considerations

### Room aliases
We have decided to specify room IDs rather than room aliases as room aliases can, in some circumstances,
be forged by malicious users/administrators.

### Trust
If the administrator of a policy room R is malicious, they can use this room to specify that all invites,
or some specific good invites, should be ignored. A user who uses R as a `source` will therefore not see
some invites that they would otherwise see.

In other words, using a room as source requires trusting the administrator of that room.

## Unstable prefix

During testing:

- `m.ignore.invites` should be prefixed `org.matrix.msc3847.ignore.invites`;
- `m.policies` should be prefixed `org.matrix.msc3847.policies`;
- `m.policy.rule.event` should be prefixed `org.matrix.msc3847.policy.rule.event`.

