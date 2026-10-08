# MSC4534: Simple room rules

In public communities, there is often a desire to present the community's rules to new members in an obvious
fashion. Currently, many communities list or link to their rules in the topic of each of their rooms, but client
UX for room topics varies from "understated" to "nonexistent", causing users to frequently miss rule information
entirely. This MSC proposes an explicit method for specifying a room's rules, and optionally requiring users to
explicitly accept them.

## Proposal

A new state event `m.room.rules` is defined, with an empty state key and these top-level keys in `content`:

| Key                  | Type                      | Required? | Purpose                                                                                                 |
| -------------------- | ------------------------- | --------- | ------------------------------------------------------------------------------------------------------- |
| `rules`              | object (extensible event) | no        | The room's rules, formatted as an [extensible event].                                                   |
| `require_acceptance` | bool                      | no        | If true, clients MUST show the user the rules when they first join the room, as outlined below.         |
| `version`            | number                    | yes       | A monotonically increasing integer, used in the `m.room.rules.accepted` account data as outlined below. |
| `delegate_to`        | object                    | no        | An object with one required key, `room`, specifying a room ID to delegate rules to.                     |

[extensible event]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767

If `rules` is not present, the room has no rules. Clients should behave as if no `m.room.rules` event exists.

If `require_acceptance` is not present, clients should assume it to be `false`.

If `delegate_to` is not present, delegation is disabled. `delegate_to` MUST have a `room` subkey if it is present.

Clients SHOULD show `m.room.rules` events in the timeline, with a message along the lines of "Alice updated the
room's rules (_view_)."

A new room-scoped account data event `m.room.rules.accepted` is defined, with these top-level keys:

| Key                     | Type   | Required? | Purpose                                 |
| ----------------------- | ------ | --------- | --------------------------------------- |
| `last_accepted_version` | number | yes       | The last accepted version of the rules. |

### Accepting rules

When clients recieve a new `m.room.rules` state event, including upon joining a room, they MUST check if its
`require_acceptance` field is true. If so, they MUST check the `last_accepted_version` field of the room's `m
.room.rules.accepted` account data event. If the account data event is not set, or if its `last_accepted_version`
field is is less than the `version` field of the newly recieved `m.room.rules` state event, the client MUST show
the `rules` content of the newly received state event in an appropriate UI element such as a modal dialog. To
dismiss this dialog, the user MUST either indicate to the client that they have read and understood the rules,
or leave the room entirely. Clients MAY allow the user to switch to another room without accepting the rules and
return later, but in all cases clients MUST NOT allow the user to interact meaningfully with the room, with the
exception of leaving the room, until the user indicates that they have read and understood the rules, or until
an updated `m.room.rules.accepted` account data event is received over sync, or until the `m.room.rules` event is
changed to delegate to a room where they have already accepted the rules, as outlined below.

Once the user indicates that they have read and understood the rules, the client MUST set the `last_accepted_version`
field of the `m.room.rules.accepted` room account data to the `version` of the newly received state event, and
allow the user to begin participating in the room normally. The user's other clients will receive this change over
sync and unlock the room in their UIs accordingly.

Clients SHOULD increment the `version` field when saving changes to the rules, even if `require_acceptance` is
false. Clients MAY offer an option to skip incrementing `version`, to keep users from being notified about minor edits.

Clients MUST retain the `version` field when deleting the rules by removing the `rules` key, to ensure users are
notified if the rules are reinstated in the future. Clients do not need to increment the `version` field when
removing the rules, but MUST do so when reinstating them.

To avoid requiring a new room version, this MSC does not modify the redaction algorithm to protect the `version`
field from redaction. Clients SHOULD NOT redact `m.room.rules` state events.

### Delegating rules

If the `delegate_to.room` field is set to a room ID, and the user is joined to that room, clients MUST use that room's
`m.room.rules` state event and `m.room.rules.accepted` account data event instead of the current room's. Otherwise,
if the field is unset, or the user is not joined to the room, the current room's data should be used as normal.

This feature is intended to allow users to only need to accept rules once for a space, instead of individually
for each room in the space. Clients that provide a UI for editing rules SHOULD clearly indicate, for rooms with
delegation enabled, that the delegated room's rules may be shown to users instead of the room's own rules, and
SHOULD automatically copy a room's rules to all known rooms that delegate to it when its rules are updated, to
avoid them from diverging undesirably.

Clients SHOULD use a room's parent spaces as suggested/autofill options when choosing a room to delegate to.

Clients MAY automatically send a `m.room.rules` state event delegating to the parent room when a user creates a
new room in a space.

For simplicity, and to confine changes to clients only, no mechanism is specified by this MSC for clients to directly
query the delegated room's rules instead of falling back to a local copy. The `delegate_to` field is made an object
to allow for a future MSC to extend it with this capability.

## Alternatives

[MSC4060](https://github.com/matrix-org/matrix-spec-proposals/pull/4060) (a draft at the time of writing) describes
a similar system that includes a server-side enforcement mechanism and requires clients to directly reference
the rules event as proof that they accepted it. This approach is believed to be undesirable by the author of this
proposal; see the "Potential issues" section for an explanation of why this MSC does not take this approach.

## Potential issues

This MSC does not propose a mechanism to prevent users from interacting with a room without accepting its
rules. Malicious, buggy, or outdated clients may ignore the rule state event and allow users to send messages
anyway. This is deemed to be an acceptable compromise, both to avoid requiring server-side changes (and possibly
a new room version) and to avoid bad UX in outdated clients that may be blocked from sending events without any
way to accept the rules.

Outdated clients will not display the room rules to users. It is anticipated that, while this MSC is being adopted,
communities will include their rules in both the `m.room.rules` state event and the room topic for redundancy.

Rooms that delegate their rules to another room may show either their own rules _or_ that room's rules depending
on if the user is joined to the delegated room. This issue is partially mitigated by having clients copy rule
changes to all known delegating rooms, but cannot be avoided entirely without server-side changes, which this
proposal seeks to avoid. The anticipated use case for delegation is for rooms that delegate their rules to a space
controlled by the same administrators, in which case users who join a room first and the parent space second should
not be surprised by being prompted to agree to the room and the space's rules independently.

## Security considerations

Malicious room administrators could put abusive content in the rules, which could be automatically presented to
users when joining. Since malicious room administrators already have the ability to do things like fill the room's
timeline with abusive content, this is deemed to be an acceptable risk.

Rooms that delegate their rules to other rooms are additionally at the mercy of the delegated room's administrators to
set appropriate rules. It is anticipated that administrators will only delegate rules to rooms that they themselves
control, which mitigates this risk.

## Unstable prefix

While this MSC is unstable, implementations should use the following identifiers:

| Stable                  | Unstable                                       |
| ----------------------- | ---------------------------------------------- |
| `m.room.rules`          | `computer.gingershaped.msc4534.rules`          |
| `m.room.rules.accepted` | `computer.gingershaped.msc4534.rules.accepted` |

## Dependencies

This MSC depends on [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767) (extensible events).