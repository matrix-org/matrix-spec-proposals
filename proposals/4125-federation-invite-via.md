# MSC4125: Specify servers to join via when inviting over federation

## Introduction

Currently when a user is invited over federation, the receiver of the invite does not know what servers
are in the room, so when attempting to join over federation, servers typically have to guess what server
to join via, typically with the `sender`'s server.

However, the server of the user who sent the invite may not be online, meaning that the user is unable to
join the room they are invited to until the `sender`'s server comes online, if it ever does. If they do not
know anyone else in the room, they cannot even ask out-of-bounds for someone else to invite them to the room.

## Proposal

The proposed fix is to create a new version of the `PUT /_matrix/federation/*/invite` endpoint based on
`PUT /_matrix/federation/v2/invite`, with the only change being an additional unsigned `via` field in the request
body to inform the server it is inviting of possible servers it can join via. This endpoint would be denoted as
`PUT /_matrix/federation/v3/invite`. Here is an example of this new body:

```json
{
  "content": {
    "membership": "invite"
  },
  "origin": "matrix.org",
  "origin_server_ts": 1234567890,
  "sender": "@alice:matrix.org",
  "state_key": "@bob:example.org",
  "type": "m.room.member",
  "unsigned": {
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
    ]
  }
}
```

This field would be similar to the `via` field of the `m.space.child` and `m.space.content` event content,
where there is simply an array of server names which are likely to be online and be in the room in the distant
future.

When accepting an invite, the server should attempt to use the `/make_join` and `/send_join` endpoints on each
of the specified servers until either it is able to join or gets a `403 M_FORBIDDEN` response.

## Potential issues

None foreseen.

## Alternatives

Servers could potentially try to join via other servers it knows, but it may take a while to find a server that
is actually in the room.

## Security considerations

The invited server now knows some of the servers that are in the room without having to join, which could be
undesireable if the room is private.

## Unstable prefix

While this MSC is not considered stable, implementations should use
`/_matrix/federation/unstable/org.matrix.msc4125/invite` as the endpoint. The body stays as proposed.

## Dependencies

None relevant.
