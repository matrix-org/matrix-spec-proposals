# MSC4432: Server-wide room name overrides

Matrix tracks room names in the [`m.room.name`] state event. Once set, the value applies to all
members of the room. These global semantics can be undesirable in a corporate context when
organizations on different home servers communicate with each other. Examples include:

- Some organizations might want to prefix federated rooms with "External: ..." while others might
  not.
- When two organizations A and B share a room, A may want to refer to the room as "B" or "B \<\> A"
  whereas B may want to use "A" or "A \<\> B".
- Organizations may want to use internal project names, case references or IDs in the room name to
  help provide context.

Personalised per-user overrides of the room name as proposed by [MSC4431] are not sufficient in
these cases. Instead, organizations require the name to be shared across all users on their
homeserver without impacting the displayed room name for users on other servers.

This proposal addresses this problem by introducing a way to set server-wide overrides of the room
name via state events.

## Proposal

When sending [`m.room.name`] state events, Clients MAY set the `state_key` to a [server name] to
scope the name to users of that server.

The [recommendations] for computing room display names in clients are changed accordingly:

- A new first step is inserted: If the room has an `m.room.name` state event with a `state_key`
  matching the users homeserver and a non-empty `name` field, use the name given by that field.
- The previous first step is limited to `m.room.name` state events with an empty `state_key`.

Clients MAY additionally display the room name as computed without the server-targeted state event
to provide an indication of how the room might show up for other users.

Servers MUST include both state events in [stripped state], [server-side search categories] and when
transferring state events during [room upgrades].

## Potential issues

In rooms shared by a large number of different organisations, the targeted room name events may
pollute the room state.

Outside of DMs, regular room members usually don't have the power level needed to send state events.
As a result, rooms will have to be configured appropriately to let all members send server-targeted
`m.room.name` events.

## Alternatives

[MSC4431] enables personalised and confidential room name overrides via room account data. This is
not sufficient in cases where multiple local users need to share the same room name, however.

## Security considerations

Since state events are currently not encrypted, the server-targeted `m.room.name` event may leak
metadata. This problem already exists with the current state event though.

To prevent abuse, servers MUST reject `m.room.name` events with a non-empty state key that doesn't
match the sender's server name. This requires a new step in the event authorization rules and
thereby a new room version.

## Unstable prefix

None.

## Dependencies

None.

  [`m.room.name`]: https://spec.matrix.org/v1.17/client-server-api/#mroomname
  [MSC4431]: https://github.com/matrix-org/matrix-spec-proposals/pull/4431
  [server name]: https://spec.matrix.org/v1.17/appendices/#server-name
  [recommendations]: https://spec.matrix.org/v1.17/client-server-api/#calculating-the-display-name-for-a-room
  [stripped state]: https://spec.matrix.org/v1.17/client-server-api/#stripped-state
  [server-side search categories]: https://spec.matrix.org/v1.17/client-server-api/#search-categories
  [room upgrades]: https://spec.matrix.org/v1.17/client-server-api/#server-behaviour-19
