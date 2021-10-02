# MSC3417 Call room room type

[MSC3401](https://github.com/matrix-org/matrix-doc/pull/3401) defines how native
Matrix group calls can work. It allows for immersive voice/video/call rooms.
[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772) is a proposal for
Matrix spaces. A part of this proposal is a way to specify a room type.

We should use the `type` field in the `m.room.create` state event to inform
clients about the fact a room is a call room.

## Proposal

This MSC proposes that when creating a call room the `type` field in the
`m.room.create` state event should be set to `m.call`. This way clients can
clearly distinguish between regular chat rooms and call rooms.

In the case of the `m.intent` field in the `m.call` state event getting out of
sync with the the `type` field in the `m.room.create` state event, the
information from the `m.room.create` state event should be preferred.

### Example

```json
POST /_matrix/client/r0/createRoom HTTP/1.1
Content-Type: application/json

{
    "preset": "private_chat",
    "name": "The Grand Duke Pub",
    "topic": "All about happy hour",
    "creation_content": {
        "m.federate": false,
        "type": "m.call",
    }
}
```

## Potential issues

The `m.intent` field in the `m.call` state event could get out of sync with the
value of `type` in the `m.room.create` state event.

## Alternatives

### Using the `m.call` state event

Clients could look for the `m.call` state event and its `m.intent` field though
this feels weird as the room type feels like the place where we should put this.
It also is mutable which isn't ideal (see next section).

### Using the `m.room.type` state event

[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) proposes a
different way to give rooms types. While we could use the `m.room.type` state
event, it is mutable which we'd like to avoid in the case of call rooms. Clients
supporting call rooms will present the chat in those rooms as secondary or not
present it at all, so it is beneficial for this to be immutable so that the chat
history isn't "lost" when changing the room type.

## Additional notes

[MSC3088](https://github.com/matrix-org/matrix-doc/pull/3088) proposes a way for
room subtyping, this could be used in the future for things such as stage rooms,
though that isn't the focus of this MSC.

## Unstable prefix

|Stable  |Unstable                 |
|--------|-------------------------|
|`m.call`|`org.matrix.msc3417.call`|
