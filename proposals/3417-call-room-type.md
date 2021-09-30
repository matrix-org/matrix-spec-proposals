# MSC3417 Call room room type

[MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401) defines how native
Matrix group calls can work. It allows for immersive voice/video/call rooms.
[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) proposes a way of
giving rooms types.

We should use `m.room.type` to inform clients about the fact a room is a
call room, so that we consistently specify the room type.

## Proposal

This MSC proposes that when a room admin wishes a room to be used as a call
room, they should set an `m.room.type` state event where the `type` is set to
`m.call`.

### Example

```json
{
    "content": {
        "type": "m.call"
    },
    "event_id": "$143273582443PhrSn:example.com",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.com",
    "sender": "@user:example.com",
    "state_key": "",
    "type": "m.room.type",
    "unsigned": {
        "age": 1234
    }
}
```

## Potential issues

The `m.intent` field in the `m.call` state event could get out of sync with the
room type.

## Alternatives

Clients could look for the `m.call` state event and its `m.intent` field though
this feels weird as the room type feels like the place where we should put this.

## Unstable prefix

|Stable  |Unstable                 |
|--------|-------------------------|
|`m.call`|`org.matrix.msc3417.call`|
