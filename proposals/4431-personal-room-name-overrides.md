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

A new room account data type `m.room.name.override` is introduced. The schema is identical to the
schema of `content` in [`m.room.name`].

    GET /_matrix/client/v3/user/@john:example.com/account_data/m.room.name.override
    {
      "name": "Charlie Meyers (the Hotspurs guy)"
    }

A new first step is inserted at the very beginning of the [room name computation
RECOMMENDATIONs][recommendations]: If `m.room.name.override` exists in the room's account data and
is not the empty object (`{}`), use the name given by that item.

Clients MAY additionally display the room name implied by [`m.room.name`] and
[`m.room.canonical_alias`] as an indicator for how the room may be displayed for other users.

Since account data cannot be deleted, clients MAY set the value to the empty object (`{}`) to remove
the override. Contrarily, to force an empty room name, clients MAY use a value of `""` for `name` in
the override.

Finally, clients MAY encrypt `m.room.name.override` using the [Secrets module].

## Potential issues

Confusion may arise when people refer to the same room under different names due to their personal
overrides. Clients can display both the personal and the official name to mitigate this problem.

Users may miss changes of a room's purpose due to their personal name override. Again, clients can
display both names to help alleviate this issue.

## Alternatives

This proposal largely follows [MSC3015] which appears to have been abandoned.

An actual alternative would be to store personal overrides in `m.room.name` state events by using
the MXID as `state_key`. This doesn't provide confidentiality for overrides and may pollute the room
state, slowing down state resolution, though. Additionally users may not have sufficient power level
to send state events in all rooms.

## Security considerations

Personalised room name overrides may leak metadata to the home server. Clients MAY use the [Secrets
module] to prevent this.

## Unstable prefix

| Stable identifier      | Purpose           | Unstable identifier                     |
|------------------------|-------------------|-----------------------------------------|
| `m.room.name.override` | Account data type | `de.gematik.msc4431.room.name.override` |

## Dependencies

None.

  [recommendations]: https://spec.matrix.org/v1.17/client-server-api/#calculating-the-display-name-for-a-room
  [`m.room.name`]: https://spec.matrix.org/v1.17/client-server-api/#mroomname
  [`m.room.canonical_alias`]: https://spec.matrix.org/v1.17/client-server-api/#mroomcanonical_alias
  [Secrets module]: https://spec.matrix.org/v1.17/client-server-api/#secrets
  [MSC3015]: https://github.com/matrix-org/matrix-spec-proposals/pull/3015
