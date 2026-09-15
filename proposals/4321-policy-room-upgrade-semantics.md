# MSC4321: Policy Room Upgrade Semantics

In the wake of the predisclosure of [project
hydra](https://matrix.org/blog/2025/07/security-predisclosure/), it is
clear that there will need to be a coordinated system for upgrading
policy rooms and ensuring moderation tools have consistent semantics
for upgrading policy rooms.

We have identified at least two ways in which policy list curators
intend to upgrade their rooms and for how they should be followed by
moderation bots. The following descriptions are non-normative and
illustrative only:

- A community may wish to upgrade the policy room, but not move any policy over to the new room.
  Moderation tools will be expected to keep following the old room as well as the new room. This is
  the option that will be taken by large policy rooms such as the Community Moderation Effort's
  #community-moderation-effort-bl:neko.dev.

- A community may wish to _move_ the policies from the old list into
  the new room and preserve information such as the creator, and the
  time of creation. Moderation bots will be expected to stop watching
  the old list as it is now considered unstable.

## Proposal

### Annotation of `m.room.tombstone` with the policy room upgrade semantic

A new property is added to the `m.room.tombstone` event `org.matrix.msc4321.policy_room_upgrade_type`

This property is expected to have a value of the string type. Move modes specified in this MSC are:

- `move`

- `transition`

### Annotation of `m.policy.rule.*` events for moved policies

Please note that policies are represented by the current state for a
state_key and type combination. They are not the events themselves.
The metadata here is purely representing the current state of the
original room at the time the policy was moved.

#### The `org.matrix.msc4321.original_sender` property

This is the top level `sender` property of the original policy event
that is being moved to the replacement room.

#### The `org.matrix.msc4321.original_timestamp` property

This is the top level `origin_server_ts` of the original policy event that is
being moved to the replacement room.

#### The `org.matrix.msc4321.original_event_id` property

This is the `event_id` of the original policy event that is being
moved to the replacement room.

### The `move` policy room upgrade type

When a policy room has been marked as moved as a result of the
`org.matrix.msc4321.policy_room_upgrade_type` property being present
with the value `"moved"`, moderation tools should at their convenience
watch the replacement room and stop watching the old one.

#### Moving policies

When policies are moved, all of their content properties should be
preserved. Additionally, the `state_key` should be preserved as this
often represents an identifier for the policy.

#### Handling legacy and unstable recommendations

When a policy with an unstable recommendation is being moved,
implementations may change the recommendation to the stable version.
Implementations should not change the `state_key` in this situation
unless it is determined that the `state_key` was derived from the
recommendation and other properties in the policy. Caution should be
exercised here as the `state_key` may intentionally be unique.

An example of an unstable recommendation change could be
`org.matrix.mjolnir.ban` to `m.ban`.

#### Handling legacy and unstable policy types

When a policy with an unstable type is being moved, implementations
may change the type to the stable version. Implementations should not
change the type unless it is determined that the transformed policy
will not conflict with any other policy (share the `state_key` and
`type`).

An example of an unstable policy type change could be
`org.matrix.mjolnir.rule.user` to `m.policy.rule.user`.

### The `transition` policy room upgrade type

When a policy room has been marked as `transition`, moderation tools
should at their convenience watch the replacement room. The old room is still
watched as a policy room, and policies may still be removed by policy
curators from the old policy room. New policies SHOULD only be added to the
replacement room. No policies are expected to be moved from the old policy room to
the replacement policy room, but they could be if the mode is later changed to `move`.

Moderation tools may show in UX that the old room is a legacy room
containing valid policies, and that any new policy will be added to
the replacement room.

## Potential issues

### The `replacement_room` in tombstone events can be changed

In this situation, moderation tools should treat the
`replacement_room` the same way they would if the room was being
upgraded without an existing `replacement_room`. Tools may warn that
the property has changed from an existing value, and make it clear in
the UX that this is a distinct scenario from an upgrade.

Any existing watched policy room should remain watched.

### Noting `/upgrade`

We expect that most clients to avoid `/upgrade` and perform moving
manually. It is left as an implementation detail whether servers will
choose to move policies on behalf of clients. Currently `/upgrade`'s
behaviour is underspecified and more options need to be presented to
clients about what state events the server should copy and how.

## Security considerations

### Replicated properties in moved policies are loosely trusted

The tool that _moves_ policies from the old policy room to the
replacement room has the liberty to fake the `original_sender`,
`original_timestamp` properties.

### Policy rooms using the `transition` type with old room versions may be unstable

Maybe there should be a recommendation about when it is appropriate to
use `transition` and whether these rooms should be encouraged to
eventually consider using `move` instead. As the tombstone event can
be superseded, it is possible for the upgrade type to change from
`transition` to `move`.

### The tombstone annotation in old rooms may be unreliable in state resets

It is possible that the annotation of the upgrade type in the old room
may be state reset.

### Hijacking of policy rooms

It may be possible for policy rooms to be hijacked by malicious parties via the tombstone event.

There are a few considerations that implementations must take:

- Moderation tools SHOULD NOT automatically follow tombstone events. A manual step
  SHOULD be taken by a moderator before the tool follows to the replacement room and
  watches the list.
- Moderation tools SHOULD attempt to provide enough information about
  the replacement room so that a moderator can make a decision as to
  whether the replacement room should be watched.

## Alternatives

### Ad-hoc upgrades

#### Loss of policy context

With ad-hoc upgrades there is a loss of data when the upgrade happens
and policies are naively cloned. The original creator and timestamp
are lost.

#### Confusion about whether to unwatch the old room

There will also be confusion and differences in communities about
whether the old policy room should remain watched, or be left.

As policy rooms are essential infrastructure on Matrix, and formal
communication channels typically do not exist for policy rooms, it is
very likely that policy room consumers will not know whether to keep
watching the old policy room. Which will lead to stale policies being
applied within these communities.
