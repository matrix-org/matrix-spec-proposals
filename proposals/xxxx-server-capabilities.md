# MSC0000: Participation based authorization for servers in the Matrix DAG

This is a proposal for the representation of servers and their basic responsibilities in the Matrix
DAG. This MSC does not define or ammend a state resolution algorithm, since there are serveral possible
routes that can be explored with other MSCs.

The key merits of this proposal are:
- The ability to deny servers from adding events to the DAG.
- The ability for clients and bots to examine joining servers before accepting any PDU from them into the room.
- Arbritrary knock logic for servers.

Additional merits that can be explored as an indirect result of this proposal:
- A way for servers to preemptively load and cache rooms that their users are likely to join.
- A way for servers to advertise to other servers about rooms that their users are likely to join,
so that these rooms can be optionally preloaded and cached.

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
- A reperesentation of the user's profile and participation information, who they are, why they are in the room, avatar, and displayname.

## Proposal

### Considerations for ammending the make_join handshake

When a joining server is instructed to join a room, the joining server sends an EDU `m.server.knock`
to any available resident servers that the joining is aware of. 

The server then waits until it receives an `m.server.participation` event with the state_key
containing the joining server's name from any resident server that is participating in the room.

When `m.server.participation`'s `participation` field has the value `permitted`, then
the joining server can use `make_join` and `send_join`. However, `send_join` could be ammended
in another MSC so that a server is able to produce an `m.server.subscription` configuration event,
rather than an `m.room.member` event for a specific user. This is so that a server can begin the
process of joining the room in advance of a user accepting or joining the room via a client,
in order to improve the response time. 

### The: `m.server.knock` EDU

`m.server.knock` is an EDU to make a client in a resident server aware of the joining server's intent to join
the room. A client can then arbritrarily research the reputation of the joining server before deciding
whether resident servers of the room should accept any PDU whatsoever from the joining server.
Currently in room V11 and below, it is not possible for room operators to stop a new server from
sending multiple PDUs to a room without first knowing of, and anticipating a malicious server's existence.
This is a fact which has already presented major problems in Matrix's history.

This propsal does not just aim to remove the risk of spam joins for members from the same server,
but also spam joins from many servers at the same time. While it is seen as technically difficult
to acquire user accounts from a large number of Matrix homeservers, it is still possible and
has happened before. For example, servers can be compromised via a common exploit in server
imlementations or existing servers that have weak registration requirements can be exploited,
and this has happened already in Matrix's history.

Having an EDU allows us to accept a knock arbritrarily with clients, and more accurately automated bots
like Draupnir. We can then arbitrarily research the reputation of the server before deciding
to accept. This also conveniently keeps auth_rules around retricted join rules clean and simple,
because all logic can be deferred to clients.

The `m.server.knock` EDU can be treated as idempotent by the receiver, although the effect should probably
expire after some subjective (to the receiver) duration.

```
{
  "content": {
    "room_id": "!example:example.com",
  },
  "edu_type": "m.server.knock"
}
```

### The `m.server.participation` event, `state_key: ${serverName}`

This is a capbility that allows the state_key'd server to send `m.server.subscription`, it is sent
to accept the `m.server.knock` EDU. The event can also be used to make a server aware of a room's
existance, so that it can be optionally preload and cache a room before the server's users discover it.

`participation` can be one of `permitted` or `deny`.
When `participation` is `permitted`, the server is able to join the room.
When `participation` is `denied`, then the server is not allowed to send any PDU's into the room.
The denied server must not be sent the denied event unless it is already present within the room,
or it has attempted to knock. This is to prevent malicious servers being made aware of rooms
that they have not yet discovered.

A `reason` field can be present alongside `participation` in order to explain the reason why
a server has been `denied`. This reason is to be shown to the knocking or previously present
server, so that they can understand what has happened.

### The `m.server.subscription` event, `state_key: ${serverName}`

This is a configuration event that uses the `m.server.participation` capability to manage
the server's subscription to the event stream. This is NOT an authorization event.

This is distinct from `m.server.participation` because this event is exclusively controlled
by the participating server, and other server's cannot modify this event[^spec-discussion].
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

The property that a malicious server can never send a PDU into the room can be worked around if
the server manages to have their `participation` `permitted`. Since now they can create PDU's
that reference this stale state, and all the other participating servers have no option but to
soft fail these events (ignoring that we don't block them at the network level).
While this is still a huge improvement over the exisitng situation but we need suggesstions for how
to stop this at the event authoirzation level. I'm begging for advice.

## Alternatives

## Security considerations

## Unstable prefix

## Dependencies

None.

[^spec-discussion]: This was derived from the following spec discussion: https://matrix.to/#/!NasysSDfxKxZBzJJoE:matrix.org/$0pv9JVVKzuRE6mVBUGQMq44vNTZ1-l19yFcKgqt8Zl8?via=matrix.org&via=envs.net&via=element.io
