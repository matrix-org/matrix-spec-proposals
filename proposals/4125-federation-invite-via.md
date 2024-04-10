# MSC4125: Specify servers to join via when inviting over federation

## Introduction

Currently when a user is invited over federation, the receiver of the invite does not know what servers
are in the room, so when attempting to join over federation, servers typically have to guess what server
to join via, typically with the `sender`'s server.

However, the server of the user who sent the invite may not be online, meaning that the user is unable to
join the room they are invited to until the `sender`'s server comes online, if it ever does. If they do not
know anyone else in the room, they cannot even ask out-of-bounds for someone else to invite them to the room.

In the case of rejecting invites, it can lead to users of the room believing that the invited user has neither
accepted nor rejected the invite, while it might have been locally rejected by the invited user's homeserver due
to it being unable to reach the sender's homeserver.

## Proposal

The proposed fix is to add an additional `via` field in the request body of `PUT /_matrix/federation/v2/invite`
to inform the server it is inviting of possible servers it can join via. The same is **not** done for `v1` of this
endpoint as `v2` should be used by default, and a server that only implements `v1` is unlikely to update to support
this new field. Here is an example of this new body:

```json
{
  "event": {
    "content": {
      "membership": "invite"
    },
    "origin": "matrix.org",
    "origin_server_ts": 1234567890,
    "sender": "@alice:matrix.org",
    "state_key": "@bob:example.org",
    "type": "m.room.member",
  },
  "invite_room_state": [
    {
      "content": {
        "name": "Example Room"
      },
      "sender": "@alice:matrix.org",
      "state_key": "",
      "type": "m.room.name"
    },
    {
      "content": {
        "join_rule": "invite"
      },
      "sender": "@alice:matrix.org",
      "state_key": "",
      "type": "m.room.join_rules"
    }
  ],
  "via": [
    "matrix.org",
    "elsewhere.chat",
    "another-server.net"
  ],
  "room_version": "10"
}
```

This field would be similar to the `via` field of the `m.space.child` and `m.space.content` event content,
where there is simply an array of server names which are likely to be online and be in the room in the distant
future. Similarly with the `m.space` events, the `via` field must have at least one server listed. If it does not,
the server the request is being sent to should respond with `400 M_INVALID_PARAM`.

This field should be optional for backwards compatibility. When the key is not present, servers should attempt
to join or leave via the `sender`'s server, and if that fails with an error other than `403 M_FORBIDDEN`, it can
optionally retry with the servers mentioned in the `invite_room_state` array. Future versions of this endpoint
(if any) should make this field mandatory.

When accepting an invite, the server should attempt to use the `/make_join` and `/send_join` endpoints on each
of the specified servers until either it is able to join or gets a `403 M_FORBIDDEN` response.

When rejecting an invite, the server should also do the same as above but for the `/make_leave` and `/send_leave`
endpoints, iterating over the servers until it either is able to leave or gets a `403 M_FORBIDDEN` response.

In the case where multiple users on the same server have received invites to the same room over federation, servers
in the most recent invite should be attempted first, and should work through invities in reverse chronological order,
attempting the servers specified in each as explained above. Servers should only be attempted on their most recent
appearance.

## Potential issues

None foreseen.

## Alternatives

Servers could potentially try to join via other servers it knows, but it may take a while to find a server that
is actually in the room.

## Security considerations

The invited server now knows some of the servers that are in the room without having to join, which could be
undesirable if the room is private.

## Unstable prefix

While this MSC is not considered stable, implementations should still use
`/_matrix/federation/v2/invite` as the endpoint, but use `org.matrix.msc4125.via` instead of `via` in the body.

## Dependencies

None relevant.
