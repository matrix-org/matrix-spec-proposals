# MSC4049: Sending events as a server or room

Matrix rooms operate off a principle where only users can send events, and thus only users can change
settings (state events) or send messages as themselves. When a server wants to make changes in a room
on behalf of users, that server needs to "impersonate" or otherwise puppet a user account it controls
in the room. While technically feasible, the approach is often disagreeable from (at minimum) a privacy
perspective.

A server might want to send an event without associated user when a user is not semantically responsible
for the event. For example:

* Keeping the `via` list for an [`m.space.child`](https://spec.matrix.org/v1.7/client-server-api/#mspacechild)
  event updated.
* Replacing the functionality of a [system alerts](https://spec.matrix.org/v1.7/client-server-api/#server-notices)
  room. ie: not occupying a [phishy user ID](https://github.com/vector-im/element-meta/issues/1759).
* Populating a [policy room](https://spec.matrix.org/v1.7/client-server-api/#moderation-policy-lists)
  with rules as the entity, avoiding occupying/puppeting a user ID. ie: when matrix.org publishes changes
  to its code of conduct or terms of service policy rooms, it intends to do so as matrix.org, but due to
  limitations with how events work it sends as `@abuse:matrix.org` instead.
* Other abuse-related notifications, such as a message to a room that they are potentially breaking
  the terms of service.

Sending as a server might be relatively rare, but a more common feature would be to send events as
a room or space. For example, in announcement rooms where the sender might not want to take personal
credit for the message, as they might be sending it on behalf of a company or community. Doing so
protects the identity of the sender, preventing bombardment of DMs/questions being sent to an individual.

Being able to send as a room is popular in announcement-only channels/rooms on other messaging platforms
such as Telegram. In Matrix, we can already have read-only rooms, but cannot hide the sender's identity.
A related feature is being able to hide the membership list of the room from other users - this is
specifically out of scope for this MSC, though possible with MSCs like [MSC4047](https://github.com/matrix-org/matrix-spec-proposals/pull/4047).

This proposal adapts the `sender` field of an event through a future room version, permitting non-user
ID values to be used, provided that entity has appropriate permissions.

Dependencies:
* [MSC4047](https://github.com/matrix-org/matrix-spec-proposals/pull/4047)
  * Depends on [MSC4046](https://github.com/matrix-org/matrix-spec-proposals/pull/4046)

## Proposal

*This MSC is done entirely in context of a future room version, due to event format, event auth,
and redaction algorithm changes.*

There are two conditions which describe a legal `sender` for an event:

1. Membership in the room.
2. Power level in the room.

For user-based senders this should hopefully be very familiar. A user which is joined to the room and
has enough power level can typically send events. With this MSC we extend `sender` to additionally be
a server name or room ID though, making these conditions slightly harder to reason about.

### Membership

Servers already have a notion of "participation" within a room: if they have at least 1 user which is
joined to the room, the server is participating in that room. We use this same definition to satisfy
the membership condition for servers-as-`sender`.

Rooms being members of a room is difficult to think about, but luckily we have a parent/child relationship
structure we can base our work off of: [spaces](https://spec.matrix.org/v1.7/client-server-api/#spaces).
In essence, spaces allow for rooms to be listed as children (read: members) of a room. Such a structure
is ideal when the message is intended to be visually sent by a parent space. For example, the "AliceChat"
space contains an "AliceChat Desktop News" announcement room - not only will users want to send as the
Desktop News room, but they'll want to send as the parent AliceChat space from time to time too.

Using the `m.space.child` relationship doesn't work as a way to determine "membership" for rooms though.
Event authorization operates exclusively within the target room, meaning it can't easily branch out to
another room (the parent space) to see if the room is listed as a child. That also assumes the server
evaluating the event even has visibility on the parent space room to begin with. Instead, we require
the largely-unused [`m.space.parent`](https://spec.matrix.org/v1.7/client-server-api/#mspaceparent) state
event to be specified within the target room. When a legal space parent is specified, the referenced room
ID is considered "joined" to the room for purposes of the membership condition on `sender`. We also declare
that a room is always "joined" to itself, allowing events to be sent as that room.

To ban a server from sending further events, all of its users can be removed or it can be
[ACL'd](https://spec.matrix.org/v1.8/server-server-api/#server-access-control-lists-acls) out of the room.

To ban a room from sending further events, it's `m.space.parent` event is removed/made invalid in the room.
Banning sending using the current room ID is done by revoking the "send key" (discussed later in this proposal).

### Power levels

#### Sending as server power levels

With membership solved, the remaining condition is power levels. The protocol already supports a `users`
and `users_default` structure in [`m.room.power_levels`](https://spec.matrix.org/v1.7/client-server-api/#mroompower_levels)
for user ID senders, but `m.room.power_levels` obviously doesn't consider servers (or rooms) as senders.

Sending as a server can be replicated by using the same `users` and `users_default` structure:

* `servers` are the power levels for specific servers. It is an object keyed by server name with value
  of power level for that server.
* `servers_default` is the default power level for any server not listed in `servers`, defaulting to
  zero itself. Unlike `users_default`, the room creator does *not* get any special treatment on this
  field.

Both fields use the same integer requirements as the other power level fields, and are protected from
redaction. See the "Security Considerations" section for why we don't inherit a server's permissions
from its users' power levels.

#### Sending as room power levels

Sending as a room is more complicated, at least for power levels. We can't simply copy the structure
we use for servers because that would allow anyone (literally anyone) to send an event as the room.
Narrowing it down to using the origin server's power level doesn't work for 2 reasons: first, the
protocol doesn't have a way to identify an origin when the `sender` is a room ID (a problem this MSC
needs to solve anyways, and does later on), and second it doesn't actually prevent much. For example,
if an announcement room for matrix.org were to be set up, it would be natural to allow matrix.org to
post as its own room. However, seeing as how matrix.org is also a large public server, any random user
could create official-looking news in the room.

We can keep trying to narrow it down by saying there's a `sender_user_id` field next to `sender`, but
then we're violating one of the principles covered in this MSC's introduction: we deliberately do not
want to know which user sent an event when it is sent as another entity.

*Author's note: this area of the MSC in particular could do with input/ideas. It's more WIP than proposal.*

##### Option 1: Send keys

To solve the issue of not being able to find a sender we can authenticate against, we use a simple
public/private key pair, as described by [MSC4047](https://github.com/matrix-org/matrix-spec-proposals/pull/4047).

We can then mirror `servers` and `servers_default` for send keys as `send_keys` and `send_keys_default`
in `m.room.power_levels`. Events which have a room ID as their `sender` must use a send key, and the
power levels associated with that send key determine what events it can send. The highest privileged
send key is used for auth rules, if multiple send keys were used to send the event.

##### Option 2: ???

*This is where more ideas are welcome.*

### `/send` API changes

The remaining ability is for an entity, usually a client, to send an event with a server or room ID
`sender`. This proposal expects that servers-as-senders will be more common with internal tooling and
so expects that vendor-specific APIs will be used in that case. For sending as a room though, the client
or entity with the send key can use [MSC4047](https://github.com/matrix-org/matrix-spec-proposals/pull/4047)'s
`/send_pdu` client-server API endpoint to modify the `sender`.

### Full diff: Event authorization

**TODO**: This section. Need a rule to describe how the power level semantics work, and `m.space.parent` becomes
an auth event.

### Full diff: Redaction algorithm

**TODO**: This section. Ensure new power level properties are not redacted. `m.space.parent` might also need
protecting in some way as it becomes an auth event.

### Examples and test vectors

**TODO**: This section.

## Potential issues

**TODO**: This section. Cover whether `m.room.member` can have non-user ID senders/state keys. Cover that only
PDUs are affected by this proposal (not to-device messages or other ephemeral events).

## Alternatives

Alternatives are described inline where relevant. Structural alternatives are not currently identified.

## Security considerations

**TODO** This section. Primary questions to answer:

1. Why not use the existing `users` power levels to determine a server name's power level? => Power escalation.
2. Why not provide a CS API endpoint for sending as a server? => Power level defaults to zero, is easily abused.

## Unstable prefix

While this proposal is not incorporated into a stable room version, implementations should use `org.matrix.msc4049`
as an unstable room version, using [MSC4047](https://github.com/matrix-org/matrix-spec-proposals/pull/4047) as a
base. `sender` is not prefixed in this room version.

## Dependencies

As of writing, this MSC is being evaluated as a potential feature for use in the MIMI working group at the IETF
through the Spec Core Team's efforts.
