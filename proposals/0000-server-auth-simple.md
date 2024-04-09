# MSC0000: Simple server authorization

This MSC proposes simple authorization rules that consider the origin
server of a given event, with the aim of replacing `m.room.server_acl`.

This is a compromising MSC based on [MSC4099](https://github.com/matrix-org/matrix-spec-proposals/pull/4099)
that tries to use concepts even more inline current authorization events,
and without changing the `/make_join` handshake.
This MSC was also created in reaction to [MSC2870](https://github.com/matrix-org/matrix-spec-proposals/pull/2870),
that describes itself as stop gap to cover what the MSC has described
short comings of `m.room.server_acl`. We also agree that MSC2870 is
a stop gap and that the `m.room.server_acl` has severe shortcomings,
but we take the view that after 4 years of proposed stop-gaping,
there is enough time to introduce a more complete solution.

Related issues:
- https://github.com/matrix-org/matrix-spec/issues/928

## Proposal

### The subscription authorization rule

This rule is be inserted after rule 3 in version 11, the check
for `m.room.create`'s content field `m.federate`.

1. If the type is `m.server.subscription`:
   1. If the `state_key` does not contain the server name for the
      origin server, reject.
   2. If the origin server's current participation is `permitted`, allow.
   2. If the `m.server.subscription_rule` is `deny`, reject.
   3. If the origin server's current participation is `deny`, reject.
   4. Otherwise allow.

The purpose of this rule is to allow a server to send a subscription
event, even if the `sender` has no membership event.

### The participation authorization rule

This rule is to be inserted before rule 4 in version 11,
the check for `m.room.member`, and after the subscription rule
described in this proposal.

1. If the origin server's current `participation` state is not `permitted`:
   1. If the `participation` state is `deny`, reject.
   2. If the `m.server.subscription_rule` is `deny`, reject.
   3. If the `m.server.subscription_rule` is anything other than `passive`, reject.

### The `m.server.participation` authorization event, `state_key: ${origin_server_name}`

This is an authorization event that is used to authorize events
originating from the server named in the `state_key`.

`participation` can be one of `permitted` or `deny`.
`participation` is protected from redaction.

A denied server must not be sent a `m.server.participation` event unless
the targeted server is already present within the room, or it has
an existing `m.server.subscription` event.
This is to prevent malicious servers being made aware of rooms that
they have not yet discovered.

A `reason` field can be present alongside `participation` in order to
explain the reason why a server has been `denied`.
This reason is to be shown to a joining, or previously present
server, so that the server's users can understand why they are not
being allowed to participate.

### The `m.server.subscription_rule` event, `state_key: ''`

This event has one field, `rule` which can be one of the following:

- `deny`: Users are unable to send the `m.server.subscription` event
  unless there is an existing `m.server.participation` event for the
  server.
- `passive`: Users can send the `m.server.subscription` event without
  corresponding membership or server participation.
- `active`: Users can send the `m.server.subscription` event but
  cannot send any other event without a corresponding
  participation of `permitted`.

`rule` is protected from redaction.

The `passive` state allows for rooms to operate as they do today,
new servers can freely join a room and start sending events without
prior approval from the administrators

The `active` state allows for a much safer way to run public Matrix rooms,
new servers can join a room, send the `m.srever.subscription` event
but cannot do more until a room administrator permits the new joiner with
an `m.server.participation` event. We expect that in practice automated
tooling will perform a simple reputation check and immediately permit
a new server to participate. This is an essential part of the proposal
as the `active` mechanism eliminates a current shortfall that
`m.room.server_acl` is a purely reactive tool in a join wave attack.

### The `m.server.subscription` event, `state_key: ${origin_server_name}`

This event has one field, `reason` which is optional. This field
is redactable. The intent is for the reason field to be redactable
by room admins.

Servers MUST check the `membership` of the `sender` before sending
to confirm that the `membership` of the sender is not `ban`.
This is to prevent users changing the reason to be malicious without
being joined to the room, without forcing room admins to `deny` the
entire server from participating. Room admins should `deny`
the server if they continue to modify the reason maliciously or
fail to perform the aforementioned check. This will prevent the server
from sending further `m.server.subscription` events.

## Potential issues

### Racing with `m.server.subcription_rule`?

We will embed `m.server.subscription_rule` in `m.room.create` if it
someone raises concerns about a potential race condition or other issue
about this conflicting with `m.server.participation`. However, stating
that there might be without elaboration is not helpful, I'd need to
know how the race works. If there is insistence, then we will embed
within the `m.room.create` event.

### `subscription` might not be an ideal term

`subscription` might not be an ideal term.

### Soft failure of backfilled messages

Servers that had `participation` of `permitted` that are later
denied via `deny`, will have their historical messages soft failed by
servers which later join.

This should be addressed with [MSC4104](https://github.com/matrix-org/matrix-spec-proposals/pull/4104).

## Alternatives

- [MSC4099](https://github.com/matrix-org/matrix-spec-proposals/pull/4099) Participation based authorization for servers in the Matrix DAG
- [MSC3953](https://github.com/matrix-org/matrix-spec-proposals/pull/3953) Server capability DAG

## Security considerations

None considered.

## Unstable prefix

`me.marewolf.msc0000.*`

## Dependencies

No dependencies
