# MSC4056: Role-Based Access Control (mk II)

A common request in Matrix is the ability to assign a set of permissions to a set of users without
having to give inherited permissions. Power levels currently provide an ability to define roles,
though each higher power level inherits the permissions from under it. A more formal Role-Based
Access Control (RBAC) mechanism would allow a user to inherit permissions from another role while
having specifics be negated, unlike power levels.

This proposal aims to improve upon the learnings of [MSC2812](https://github.com/matrix-org/matrix-spec-proposals/pull/2812),
particularly around the decentralization and state resolution components. The specific permissions
supported by roles are left out of scope in this version of the proposal.

MSC2812 fails to operate when state resolution is considered due to how it is structured. In isolation,
the MSC offers a sturdy framework for RBAC, but when two changes utilizing a role are in conflict,
state resolution will fail to pick a "winning" change. This proposal addresses the problem by applying
a power level structure over top of roles, providing a deliberate hierarchy of roles.

**TODO: Insert text about why RBAC is cool/wanted, and why we've avoided it in the past (NTFS hell,
flight console UX, etc)**

## Potential issues

*Author's note: This section is up here to be clear about which problems are considered TODO items.*

This MSC does *not* have:

* Backwards compatibility with existing clients/tooling.
* Explicit permissions a role could have. It is assumed for now that the permissions implied by power
  levels are maintained at a minimum. For example, ability to send an event of a given type.
* A complete solution. It outlines a framework at the moment.

## Proposal

In a future room version, due to dramatic changes relating to how rooms work, we do the following.

`m.room.power_levels` is stripped of its usefulness. Clients MAY send it, but it will be treated as
any other random event. Servers MAY optionally decide to prevent clients from sending it by accident
in applicable room versions.

A new `m.role` state event is introduced, with `state_key` being an arbitrary opaque string. The
`state_key` becomes the "Role ID". The `content` for the role is as follows:

```jsonc
{
  "profile": {
    // display name, avatar, colour, etc? Use extensible events content blocks where reasonable.
  },
  "permissions": {
    // TODO: Replace example with actual permission (m.invite or whatever)
    "org.example.my_permission": true,
    "org.example.another": {
      "is_complicated_type": true
    }
  }
}
```

`m.profile` is inspired by [MSC3949](https://github.com/matrix-org/matrix-spec-proposals/pull/3949),
where allowing a user to define such characteristics is clearly desirable. `m.permissions` are the
permissions themselves (which may be non-boolean values).

The users "affected" by this role are described in a second new state event: `m.role_map` with an
empty string `state_key`. The `content` being:

```jsonc
{
  "role_id": {
    "users": ["@alice:example.org"],
    "order": 1
  },
  "another_role_id": {
    "users": ["@bob:example.org"],
    "order": 5
  }
}
```

Each role MUST have a distinct `order` number. Roles with higher `order` override conflicting permissions
from lower `order` roles. For example, given the following:

* "Role A" with `order: 1` and permission `first: true, second: true`.
* "Role B" with `order: 2` and permissions `first: false, third: true`.

... a user with both roles would have permissions `first: false, second: true, third: true`. `first` is
overridden by the `order: 2` role, but `second` and `third` are not conflicting.

When an event is sent by a user, it MUST reference the `m.role_map` and `m.role` events applicable
to the `sender` from that map as `auth_events`.

MSC2812 has a fundamental flaw in how it authorizes events, preventing it from working reliably in
a decentralized environment. When a user with Role A is trying to ban a user, and the target user
is removing that permission from Role A at the same time, the conflict becomes impossible to predict
because state resolution will ultimately tiebreak on event ID. This unexpected behaviour can be (at
best) confusing for users.

This MSC fixes that flaw by retaining a concept of "power level", but only applying it to the roles
themselves through `order`. When state resolution is attempting to resolve a power struggle, it would
first determine which role has higher `order`, then let that event "win" the conflict. In the cases
where the two involved users have the *same* role, timestamps and event IDs are used as tiebreaks,
like with any other event. In other words, a user's power level is effectively the highest `order`
role they possess with the required permission(s).

When the users involved in a conflict are at the same effective power level, it is less surprising
to those users that a conflict would be resolved by timestamp or "flip of a coin" (event ID ordering).
For other cases however, users will typically have an implied hierarchy in mind even if `order` didn't
exist, leading to an expectation that users with "Admin" have "more power" than those with "Moderator".
The `order` field formalizes the user preference (and therefore expectation).

For the above reasons relating to state resolution, we intentionally mix user assignment and ordering
into the same event type. Ideally, the `order` (and possibly even assignment) would be done on the
`m.role` events themselves, however in a conflicted set of state it becomes difficult or impossible
to enforce "one role per order number" during event authorization.

### Detailed authorization rule changes

**TODO**

### Detailed state resolution changes

**TODO**

### Detailed redaction algorithm changes

**TODO**

### Test vectors

**TODO**

## Potential issues

**TODO: Complete more of this section.**

* A limited number of roles can be used and assigned, as `m.role_map` will be subject to size restrictions.
* This MSC is intentionally does not support per-user role ordering. This is a complicated feature to
  represent (when considering state resolution), and is empirically not used by Discord. A future room
  version may introduce such a feature.

## Alternatives

[MSC2812](https://github.com/matrix-org/matrix-spec-proposals/pull/2812) is the primary alternative to
this MSC. [MSC3073](https://github.com/matrix-org/matrix-spec-proposals/pull/3073) inherits from MSC2812
and is subject to the same issues described by this proposal. MSC3073 does introduce per-user role
ordering, though not in a way compatible with state resolution/conflicts.

[MSC3949](https://github.com/matrix-org/matrix-spec-proposals/pull/3949) aims to introduce the "profile
information" for a role without introducing RBAC itself. This proposal inherits the ideas of MSC3949.

No other significant alternatives are considered. Some minor representation details are possible, however
clients like Discord are generally seen as the "gold standard" for user-facing RBAC implementation. Those
clients don't make use of many theorized alternatives.

## Security considerations

**TODO**

If `m.role_map` uses a role ID which doesn't exist and assigns users to it, those users will never be able
to send events because the `auth_events` will never be complete. This needs to be fixed before this MSC
enters FCP, at least for `m.room.member` and similar power events.

## Unstable prefix

While this proposal is not incorporated into a stable room version, implementations should use `org.matrix.msc4056`
as an unstable room version, using [room version 11](https://spec.matrix.org/v1.8/rooms/v11/) as a base. The
event types are also prefixed in this room version.

| Stable | Unstable |
|--------|----------|
| `m.role` | `org.matrix.msc4056.role` |
| `m.role_map` | `org.matrix.msc4056.role_map` |

## Dependencies

As of writing, this MSC is being evaluated as a potential feature for use in the MIMI working group at
the IETF through the Spec Core Team's efforts.
