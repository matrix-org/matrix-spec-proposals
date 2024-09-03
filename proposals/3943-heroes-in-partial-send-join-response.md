# MSC3943: Partial joins to nameless rooms should include heroes' memberships.

This is an addendum to [MSC3706](https://github.com/matrix-org/matrix-spec-proposals/pull/3706) which ensures that partial-joining a nameless room has a reasonable client UX.

## Background

[MSC3706](https://github.com/matrix-org/matrix-spec-proposals/pull/3706) extends the federation `/send_join` endpoint to optionally return a "partial state" response. In this mode of operation, the joining server is given only a _subset_ of the current state[^1] of the room to be joined; the full state is lazily loaded by the joining server.

[^1]: More precisely: the current state of the room to be joined _from the perspective of the resident server_.

MSC3706 specifies this subset

> `state`: if partial state is being returned, then state events with event
> type `m.room.member` are omitted from the response. All other room state is
> returned as normal.

because

> Currently, `m.room.member` events are by far the biggest problem.

but also notes that 

> In future, the list of event types to omit could be expanded. (Some rooms
  may have large numbers of other state events).

## Problem

_Originally noted in [synapse#12995](https://github.com/matrix-org/synapse/issues/12995)._

Clients need to present a display name for the room, using `m.room.name` or `m.room.canonical_alias` state events[^2] as described [in the spec](https://spec.matrix.org/v1.5/client-server-api/#calculating-the-display-name-for-a-room). If neither event exists, then the client falls back to a name calculated based on the membership events for the "heroes" of the room.

[^2]: More precisely: using state events with (type, state\_key) pair equal to `('m.room.name', '')` or `('m.room.canonical_alias', '')`.

The problem is that the partial-joining server does not have the heroes' membership events until it fetches the full state of the room; in this situation, the room has no defined display name. This results in a poor end-user experience.

## Proposal

When serving a partial join, if the room to be joined has no `m.room.name` or `m.room.canonical_alias` events in its current state, the resident server SHOULD

- determine the heroes for the room (as specced today),
- include the heroes' current membership events in the response `state` field, and
- include the heroes' current membership events' auth chains in the response `auth_chain` field.

## Potential issues

This enlarges the `state` and the `auth_chain` returned in a partial state response. The effect on `state` is limited as there are at most 5 heroes in any given room. The `auth_chain` for the heroes' membership events may be arbitrarily long.

## Alternatives

- Have the resident server compute a dummy room name and express this as a new field in the `/send\_join` response. This is hard to internationalise and complicates the data model for minimal gain.
- Require clients to use the room ID or alias which initiated the join as a room displayname.
  - What if the join was actioned by a different client device, or by the server directly?
- Change the spec's display name rules to fallback to the room ID if there are no membership events available.
  - Poor end-user experience: room IDs are opaque.
  - This would also gives rooms that contain only an `m.room.create` event a defined display name. But that's not especially useful.

## Security considerations

None at present. Or better put: this doesn't introduce any new concerns.

- The joining server is already privvy to these additional membership events. It will receive them when it receives the full state from the resident server.
- The joining server already trusts that the resident server is sending an accurate partial and full state.

## Unstable prefix

Not required.

## Dependencies

[MSC3706](https://github.com/matrix-org/matrix-spec-proposals/pull/3706).
