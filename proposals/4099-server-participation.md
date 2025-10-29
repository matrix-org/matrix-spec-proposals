# MSC4099: Participation based authorization for servers in the Matrix DAG

This is a proposal for the representation of servers and their basic responsibilities in the Matrix
DAG. This MSC does not define or amend a state resolution algorithm, since there are several possible
routes that can be explored with other MSCs. We make considerations to  allow this proposal to be
implemented on top of the existing `m.room.member`/`m.room.power_levels` centric authorization and
state resolution algorithms.

The key merits of this proposal are:
- Authorization rules are changed so that there is no way for a server to append an event to the DAG
until they have been explicitly named in a new authorization event, `m.room.server.participation`. 
- All events have to be authorized with a corresponding `m.room.server.participation` event for their
origin server.
- Room admins and their tools now have the ability to examine joining servers before making a decision
to permit them to participate in the room. This can be thought of as the equivalent of "knocking for servers"[^knocking].
- We envisage that for most rooms, permitting servers to participate will happen quickly and automatically,
probably before the server even attempts to join the room if they already well known and trusted within
the community[^tooling-for-accepting].

Additional merits that can be explored as an indirect result of this proposal:
- A way for servers to preemptively load and cache rooms that their users are likely to join.
- A way for servers to advertise to other servers about rooms that their users are likely to join,
so that these rooms can be optionally pre-loaded and cached.

This is a more specific component and redesign of the general idea of [MSC3953: Server capability DAG](https://github.com/Gnuxie/matrix-doc/blob/gnuxie/capability-dag/proposals/3953-capability-dag.md).

## Context

### The role of the existing `m.room.member` for a user

In order to develop ideas about how to represent server membership in the room DAG,
which is NOT what this proposal does, we need to understand the responsibilities that `m.room.member`
already has:

- A representation of the desire for the user's server to be informed of new events.
- The capability for the server to participate in the room on behalf of the user,
being used to authorize the user's events.
- The capability for the user to backfill in relation to visibility.
  + it is unclear to me whether `m.room.history_visibility` restricts a server's ability to backfill or not.
- A representation of the user's profile and participation information, who they are, why they are in the room, avatar, and displayname.

## Proposal

### Considerations for amending the `make_join` handshake

When a joining server is instructed by a client to join a room, the joining server sends an
EDU, `m.server.knock`, to any available resident server that the joining server is aware of. 

The server then waits until it receives an `m.server.participation` event, which will contain the
joining server's name within the `state_key`. 
The `m.server.participation` event can be received from any resident server that is participating
in the room. However, the `m.server.participation` event should only be sent by the room admins.

When `m.server.participation`'s `participation` field has the value `permitted`, then
the joining server can begin to use `make_join` and `send_join`. However, `send_join` could be amended
in another MSC so that a server is able to produce an `m.server.subscription` configuration event,
rather than an `m.room.member` event for a specific user. This is so that a server can begin the
process of joining the room in advance of a user accepting or joining the room via a client,
in order to improve the response time. 

### The: `m.server.knock` EDU

`m.server.knock` is an EDU to make a client in a resident server aware of the joining server's intent
to join the room. This client will usually be a room admin. A client can then arbitrarily research
the reputation of the joining server before deciding whether resident servers of the room should
accept any PDU whatsoever from the joining server. Currently in room V11 and below, it is not
possible for room operators to stop a new server from sending multiple PDUs to a room without first
knowing of, and anticipating a malicious server's existence. This is a fact which has already
presented major problems in Matrix's history.

This proposal does not just aim to remove the risk of spam joins for members from the same server,
but also spam joins from many servers at the same time. While it is seen as technically difficult
to acquire user accounts from a large number of Matrix homeservers, it is still possible and
has happened before. For example, servers could become compromised with a common exploit in a server
implementation. Existing servers that have weak registration requirements could also be exploited,
and this has happened already in Matrix's past.

Having an EDU allows us to accept a knock arbitrarily with clients, and more accurately automated bots
like Draupnir. We can then arbitrarily research the reputation of the server before deciding
to accept. This also conveniently keeps auth_rules around restricted join rules clean and simple,
because all logic can be deferred to clients.

The `m.server.knock` EDU can be treated as idempotent by the receiver, although the effect should
expire after a duration that is subjective to the receiver.

```
{
  "content": {
    "room_id": "!example:example.com",
  },
  "edu_type": "m.server.knock"
}
```

### The `m.server.participation` event, `state_key: ${serverName}`

This is a capability that allows the server named in the `state_key` to send `m.server.subscription`,
it is sent to accept the `m.server.knock` EDU. The event can also be used to make a server aware of
a room's existence, so that it can be optionally preload and cache a room before the server's users
discover it.

`participation` can be one of `permitted` or `deny`. When `participation` is `permitted`, the server
is able to join the room. When `participation` is `denied`, then the server is not allowed to send
any PDU's into the room. The denied server must not be sent a `m.server.participation` event unless
the targeted is already present within the room, or it has attempted to knock.
This is to prevent malicious servers being made aware of rooms that they have not yet discovered.

A `reason` field can be present alongside `participation` in order to explain the reason why
a server has been `denied`. This reason is to be shown to the knocking, or previously present
server, so that they can understand what has happened.

### The `m.server.subscription` event, `state_key: ${serverName}`

This is a configuration event that uses the `m.server.participation` capability to manage
the server's subscription to the event stream. This is NOT an authorization event.

This is distinct from `m.server.participation` because this event is exclusively controlled
by the participating server, and other servers cannot modify this event[^spec-discussion].
This allows the server to have exclusive control over whether it is to be sent events (where
its participation is still `permitted`). We specifically do not want to merge this with
`participation` to avoid having to specialise state resolution for write conflicts,
or "force joining" servers back into rooms. This allows a server to remain permitted to participate,
but opt out of receiving further events from this room, and can then optionally stop replicating the
room and delete all persistent data relating to it (should all clients have also forgotten the room). 

### Considerations for event authorization

All events that a server can send need to be authorized by an `m.server.participation` event
with the field `participation` with a value of `permitted`.

## Potential issues

### Permitting, then denying a malicious server.

The feature in principle that a malicious server can never send a PDU into the room can be worked
around if the server manages to have their `participation` `permitted` at some point in the room's
history. Since now they can create PDU's that reference this stale state, and all the other
participating servers have no option but to soft fail these events
(ignoring that we don't block them at the network level).
While this is still a huge improvement over the existing situation, we need suggestions for how
to stop this at the event authorization level. I'm begging for advice.

### Unclear if a joining server can receive a PDU from a room that it is not joined to

The amendments to the join handshake described in this MSC mean that a server has to wait
for a PDU, `m.server.participation` before it has attempted to join the room beyond sending an EDU.
It's not clear to me whether this is currently possible or changes are required to federation send.

### Surely the joining server needs to send the EDU via resident servers, so `make_join` has to be modified

The EDU `m.server.knock` surely has to be sent via a resident server so that it can be received
by all servers within the room.

## Alternatives

## Security considerations

## Unstable prefix

## Dependencies

None.

[^spec-discussion]: This was derived from the following spec discussion: https://matrix.to/#/!NasysSDfxKxZBzJJoE:matrix.org/$0pv9JVVKzuRE6mVBUGQMq44vNTZ1-l19yFcKgqt8Zl8?via=matrix.org&via=envs.net&via=element.io

[^knocking]: Although, knocking is implemented with the auth event `m.room.member` we don't want joining
servers to be able to send any event to the room at all (other than the `m.server.knock` EDU).

[^tooling-for-accepting]: Though now I say this, we probably need to be able to demonstrate that
this will be the case. A lot of this is now looking obvious, why weren't we thinking about this
years ago? Well, there's a lot of context. There always is buddy, you've got the easy view of hindsight.
Someone had to both conceive and write this and get us out of the dark ages. Ths MSC looks poorer
in my eyes by the minute.
