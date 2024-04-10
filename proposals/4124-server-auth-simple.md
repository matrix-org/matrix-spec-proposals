# MSC4124: Simple server authorization

This MSC proposes simple authorization rules that consider the origin
server of a given event, with the aim of replacing `m.room.server_acl`.

This is a compromising MSC based on [MSC4099](https://github.com/matrix-org/matrix-spec-proposals/pull/4099)
that tries to use concepts even more inline current authorization events
This MSC was also created in reaction to [MSC2870](https://github.com/matrix-org/matrix-spec-proposals/pull/2870),
that describes itself as stop gap to cover what the MSC has described
short comings of `m.room.server_acl`. We also agree that MSC2870 is
a stop gap and that the `m.room.server_acl` has severe shortcomings,
but we take the view that after 4 years of proposed stop-gaping,
there is enough time to introduce a more complete solution.

Related issues:
- https://github.com/matrix-org/matrix-spec/issues/928

## Proposal

### The `m.server.knock` authorization rule

This rule is be inserted after rule 3 in [version 11](https://spec.matrix.org/v1.10/rooms/v11/#authorization-rules),
the check for `m.room.create`'s content field `m.federate`.

1. If the type is `m.server.knock`:
   1. If the `state_key` does not contain the server name for the
      origin server, reject.
   2. If there is any current state for the origin server's `m.server.knock`, reject.
   3. If the origin server's current participation is `permitted`, allow.
   4. If the `m.server.knock_rule` is `deny`, reject.
   5. If the origin server's current participation is `deny`, reject.
   6. Otherwise allow.

The purpose of this rule is to allow a server to send a knock
event, even if the `sender` has no membership event.

The purpose of rule 1.2 is to prevent denied servers from ever being
given the ability to craft any event whatsoever in a room that has always
had the `active` `m.server.knock_rule`.
This is because an `m.server.participation` event set to `deny` will
usually be topologically older than an `m.server.knock` due to the
`m.server.participation` usually referencing a recent
`m.room.power_levels` event. And so `m.server.knock` events could
be crafted by malicious servers without restriction without
rule 1.2.

### The `m.server.participation` authorization rule

This rule is to be inserted before rule 4 in [version 11](https://spec.matrix.org/v1.10/rooms/v11/#authorization-rules),
the check for `m.room.member`, and after the `m.server.knock` rule
described in this proposal.

1. If the origin server's current `participation` state is not `permitted`:
   1. If the `participation` state is `deny`, reject.
   2. If the type is `m.server.participation` and the sender's origin
      server matches the state_key of the considered event:
      1. If the `participation` field of the considered event is not
         `permitted`, reject.
	  2. If the sender is the same sender of m.room.create, then allow.
   3. If the `m.server.knock_rule` is `deny`, reject.
   4. If the `m.server.knock_rule` is anything other than `passive`, reject.

We allow the room creator to set their own participation and bypass
the `m.server.knock_rule` provided their server has not been explicitly
denied. This is because we want them to be able to set their
participation at room creation without being unable to do when the
`m.server.knock_rule` is `active`.

We allow senders to add the `participation` of their own server,
provided that they only do so to `permit` their own server (and not
deny themselves as a footgun). This is useful in cases where a
room has a `passive` `m.server.knock_rule` and the room admins need
to explicitly permit their own servers before changing the knock
rule to `active`.

### The `m.server.participation` authorization event, `state_key: ${origin_server_name}`

This is an [authorization event](https://spec.matrix.org/v1.10/server-server-api/#auth-events-selection)
that is used to authorize events originating from the server named in
the `state_key`.

`participation` can be one of `permitted` or `deny`.
`participation` is protected from redaction.

A denied server must not be sent a `m.server.participation` event unless
the targeted server is already present within the room, or it has
an existing `m.server.knock` event.
This is to prevent malicious servers being made aware of rooms that
they have not yet discovered.

A `reason` field can be present alongside `participation` in order to
explain the reason why a server has been `denied`.
This reason is to be shown to a joining, or previously present
server, so that the server's users can understand why they are not
being allowed to participate.

### The `m.server.knock_rule` event, `state_key: ''`

This event has one field, `rule` which can be one of the following:

- `deny`: Users are unable to send the `m.server.knock` event
  unless there is an existing `m.server.participation` event for the
  server.
- `passive`: Users can send the `m.server.knock` event without
  corresponding membership or server participation.
- `active`: Users can send the `m.server.knock` event but
  cannot send any other event without a corresponding
  participation of `permitted`.

`rule` is protected from redaction.

The `passive` state allows for rooms to operate as they do today,
new servers can freely join a room and start sending events without
prior approval from the administrators

The `active` state allows for a much safer way to run public Matrix rooms,
new servers can join a room, send the `m.server.knock` event
but cannot do more until a room administrator permits the new joiner with
an `m.server.participation` event. We expect that in practice automated
tooling will perform a simple reputation check and immediately permit
a new server to participate. This is an essential part of the proposal
as the `active` mechanism eliminates a current shortfall that
`m.room.server_acl` is a purely reactive tool in a join wave attack.

### The `m.server.knock` event, `state_key: ${origin_server_name}`

This event has no fields, because it can only be sent once, and
therefore cannot be edited if the wrong or malicious information
is provided.

The intent of the event is to only let the room administrators
explicitly aware of the server's existence.

### The `make_server_knock` handshake

This MSC requires a very simple clone of the `make_knock` handshake
for the purpose of signing and creating the `m.server.knock` event.

The details of this handshake are left outside the scope of the MSC,
as it may be decided that an API providing an agnostic unification of
`make_knock` and `make_join` should be used instead that signs
both the membership event and the `m.server.knock` event templates.

We believe that the open choice here should not alone be a reason
to block this MSC from consideration. But we will follow up
with a clone of the `make_knock` handshake if requested.

## Potential issues

### Racing with `m.server.knock_rule`?

We will embed `m.server.knock_rule` in `m.room.create` if it
someone raises concerns about a potential race condition or other issue
about this conflicting with `m.server.participation`. However, stating
that there might be without elaboration is not helpful, I'd need to
know how the race works. If there is insistence, then we will embed
within the `m.room.create` event.

### Changing the `m.server.knock_rule` from `passive` to `active` or `deny`

Server admins can unintentionally lock themselves out of their room
unless they are the room creator under the current proposal.

### Soft failure of messages

Servers that had `participation` of `permitted` that are later
denied via `deny`, can have some of their messages soft failed
while the forks synchronise similar to https://github.com/matrix-org/synapse/issues/9329.

This could be addressed with [MSC4104](https://github.com/matrix-org/matrix-spec-proposals/pull/4104).

### Mismatch with `m.room.power_levels`

There is an argument to be made that the ability to manage
`m.server.participation` should not be flat in the way that
`m.room.server_acl` is. Consider Alice being the room creator
and Bob being an admin. Bob could create an `m.server.participation`
event that denies Alice's server from participating, even if Alice
is the same or a higher power level.

## Alternatives

- [MSC4099](https://github.com/matrix-org/matrix-spec-proposals/pull/4099) Participation based authorization for servers in the Matrix DAG
- [MSC3953](https://github.com/matrix-org/matrix-spec-proposals/pull/3953) Server capability DAG

## Security considerations

None considered.

## Unstable prefix

`me.marewolf.msc4124.*`

## Dependencies

No direct dependencies
See `make_server_knock` handshake.
