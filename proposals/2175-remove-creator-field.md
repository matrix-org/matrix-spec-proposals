# MSC2175: Remove the `creator` field from `m.room.create` events

[`m.room.create`](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-create)
events have a mandatory `creator` property giving the ID of the user who
created the room. This field is redundant as it is always identical to the
`sender` of the create event.

This MSC proposes that, in a future room version, this field should be removed
and that the `sender` field be used instead.

Note that `creator` is mentioned in the [auth
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules). It can
safely be removed.

`creator` is also mentioned as a key to be preserved during [Event
redaction](https://matrix.org/docs/spec/client_server/r0.5.0#redactions). It
should be removed from that list.
