# MSC4431: Personalised room name overrides

Matrix includes [recommendations] for how to compute a room's display name in clients. The logic
starts with the [`m.room.name`] state event, falls back to the [`m.room.canonical_alias`] state
event and finally defaults to concatenating member display names. None of these branches allows one
party in the room to *set* a room name that only they can see. This would, however, be desirable in
certain cases:

- You may want to file a DM under something else than the other user's display name because their
  display name is ambiguous (you may know more than one person called "Charlie") or otherwise
  confusing (you don't interact with Charlie often enough to remember "SpursLover86").
- The logic of concatenating member names doesn't work well in DMs where one party is joined with
  multiple accounts (e.g. a work and a personal account or a regular and a backup account).
- You want to use a personalised naming scheme such as "Lastname, Firstname" for DMs or "External:
  ..." for chats outside your organisation.

The present proposal addresses these use cases by introducing a way to create personalised overrides
for room names via account data.

## Proposal

A new room account data type `m.room.name.private` is introduced. The schema is identical to the
schema of `content` in the [`m.room.name`] state event.

    GET /_matrix/client/v3/user/${userId}/rooms/${roomId}/account_data/m.room.name.private
    {
      "name": "Charlie Meyers (the Hotspurs guy)"
    }

The suffix `.private` enables future extensibility and helps distinguish personalised overrides from
other kinds of overrides such as the server-wide overrides introduced in [MSC4432]. The naming
matches the [`m.read.private`] read receipt type which is used for personal receipts that are not
shared with other users.

To apply the override, a new first step is inserted at the very beginning of the [room name
computation RECOMMENDATIONs][recommendations]: If `m.room.name.private` exists in the room's account
data and is not the empty object (`{}`), use the name given by that item.

Clients MAY additionally display the room name implied by the state events [`m.room.name`] and
[`m.room.canonical_alias`] as an indicator for how the room may be displayed for other users.

Since account data cannot be deleted, clients MAY set the value to the empty object (`{}`) to remove
the override. Contrarily, to force an empty room name, clients MAY use a value of `""` for `name` in
the override.

## Potential issues

Confusion may arise when people refer to the same room under different names due to their personal
overrides. Clients can display both the personal and the official name to mitigate this problem.

Users may miss changes of a room's purpose due to their personal name override. Again, clients can
display both names to help alleviate this issue.

## Alternatives

This proposal largely follows [MSC3015] which appears to have been abandoned. One key difference is
the usage of `private` rather than `override` in the account data type. The fact that
`m.room.name.private` in account data overrides `m.room.name` in the room state seems sufficiently
clear even without an explicit `override` suffix. This is because the room state is shared by all
room members whereas room account data is storage specifically meant for a single user. In contrast,
the semantics of an `m.room.name` account data type would not be clear if another kind of override
is introduced in an `m.room.name.whatever` account data type in future.

An actual alternative would be to store personal overrides in `m.room.name` state events by using
the MXID as `state_key`. This doesn't provide confidentiality for overrides and may pollute the room
state, slowing down state resolution, though. Additionally users may not have sufficient power level
to send state events in all rooms.

## Security considerations

Just like the `m.room.name` state event, personalised room name overrides may leak metadata to the
home server. A future MSC may introduce a practical encryption mechanism for account data events,
for instance, by building upon the [Secrets module] to prevent this.

## Unstable prefix

| Stable identifier     | Purpose           | Unstable identifier                    |
|-----------------------|-------------------|----------------------------------------|
| `m.room.name.private` | Account data type | `de.gematik.msc4431.room.name.private` |

## Dependencies

None.

  [recommendations]: https://spec.matrix.org/v1.17/client-server-api/#calculating-the-display-name-for-a-room
  [`m.room.name`]: https://spec.matrix.org/v1.17/client-server-api/#mroomname
  [`m.room.canonical_alias`]: https://spec.matrix.org/v1.17/client-server-api/#mroomcanonical_alias
  [MSC4432]: https://github.com/matrix-org/matrix-spec-proposals/pull/4432
  [`m.read.private`]: https://spec.matrix.org/v1.17/client-server-api/#private-read-receipts
  [MSC3015]: https://github.com/matrix-org/matrix-spec-proposals/pull/3015
  [Secrets module]: https://spec.matrix.org/v1.17/client-server-api/#secrets
