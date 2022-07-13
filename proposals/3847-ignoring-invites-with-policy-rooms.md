# MSC3847: Ignoring invites using individual policy rooms

Receiving unwanted invites is something that users currently need to live
with on the Matrix network. To alleviate this, Matrix needs a mechanism to
let users specify that they are not interested in invites from specific
users or towards specific rooms.

In this proposal, we introduce the necessary extensions to let users do
this and to let clients perform filtering of unwanted invites.

We proceed as follows:

1. We build upon the mechanism of policy rooms, defined in MSC2313, and define
a user's individual policy room, which may be created on behalf of the user by
a Matrix client, and which is shared across all devices and clients of the user.
2. We build upon the mechanism of recommendations, also defined in MSC2313,
and create a new recommendation for ignoring invites from a specific user, from
a specific server or towards a specific room.


## Proposal

### Background

MSC2313 defines policy rooms. A policy room is a room in which rules such
as the following may be published:

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
individual rooms or individual users, but there is no specification in MSC2313
clarifying how to associate an issuer with a policy room.

### Associating a policy room with a user

For individual users, we introduce a new event `m.policies`, designed
to be used as part of account data. This event has content:

| Content | Type | Description |
|---------|------|-------------|
| `room`  | Room ID or Alias | The main room in which a user may publish policies to be applied on their behalf. |

We expect that future MSCs will expand upon this event `m.policies` and add
other rooms where policies are published by other users or communities but
that the current user also wish to apply, e.g. for distributing trust. This
is, however, beyond the scope of the current proposal.

The expected behavior is that if a user Alice has a `m.policies` with `room` R,
then:

- whenever Alice issues a new policy from their client or another trusted agent,
    this policy will be stored in room R;
- any client or trusted agent acting on behalf of Alice will monitor room R for
    new policies and apply the recommendations on behalf of Alice.

### A recommendation for ignoring invites

We expand the **`enum`** `recommendation` with the following value

| Value | Description |
|---------|-------------|
| `m.invites.ignore`  | The user's client should not display any invite from/to the entity specified in `entity`. |

In particular, if Alice has a policy with `recommendation` `m.invites.ignore`:

- if `type` is `m.policy.rule.user` and `entity` is Bob's User ID, Alice's clients will not display any invite issued by Bob;
- if `type` is `m.policy.rule.room` and `entity` is the Room ID or alias of room Bobroom, Alice's clients will not display any invite issued to Bobroom;
- if `type` is `m.policy.rule.server` and `entity` is the server name of server Bobverse, Alice's clients will not display any invite issued from any account from Bobverse or towards a room alias on the Bobverse.

### Client behaviour

If a new policy `m.invites.ignore` appears in Alice's individual policy room:

- any pending invite currently displayed that matches the `entity` is removed from display;
- any incoming invite that matches the `entity` is not displayed among invites.

However, clients are expected to offer the ability to look at any ignored invite,
in a manner similar to a trashcan/recycle bin/undelete mechanism for desktop file
systems.

Similarly, if a policy `m.invites.ignore` is redacted/amended, clients should show any
invite that doesn't match any `m.invites.ignore` entity anymore.

### Server behavior

As recommended in MSC2313, if a policy `m.ban` appears in Alice's individual policy room:

- if `type` is `m.policy.rule.user`, ignore any message or invite from the user `entity`, as per `m.ignored_users`;
- if `type` is `m.policy.rule.room`, ignore any message in the room or invite from the room `entity`;
- if `type` is `m.policy.rule.server`, ignore any message in any room on server `entity`, any message from any user on server `entity`, any invite towards any room on server `entity`, any invite from any user on server `entity`.

## Potential issues

### Number of events

There is a risk that the list of ignored invites of some users may grow a lot, which might have
performance impact, both during initial sync and during filtering. We believe that this risk is
limited. If necessary, clients may decide to cleanup ignored invites after some time.

### Sync size

With this proposal, any invite ignored with `m.invites.ignore` will still show up at each `/sync`.
In time, this can grow expensive.

If necessary, clients may decide to convert ignored invites into rejected invites or `m.ban`
after a while.

## Alternatives

### Server-side filtering

Just as `m.ignored_users_list` is handled mostly on the server, we could handle `m.invites.ignore`
largely on the server. However, this would make it much harder to undo erroneous ignores (i.e.
implementing some sort of recovery from trashcan) on the client.

So we prefer handling things on the client, even if this may require more traffic.

## Security considerations

Can't think of any right now.

## Unstable prefix

During testing:

- `m.invites.ignore` should be prefixed `org.matrix.msc3847.invites.ignore`;
- `m.policies` should be prefixed `org.matrix.msc3847.policies`.
