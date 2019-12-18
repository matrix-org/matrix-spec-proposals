# MSC2389 - Typing (keyboard-input) EDU-as-a-PDU

### Background

Typing events are a feature in Matrix which indicate a user is in the process
of entering a message. Typing events are currently specified as ephemeral data
units. A server will transmit a typing EDU when a user strikes a key to every
other server in the room. When the user stops, deletes, or transmits their entry,
another typing EDU is broadcast for stoppage and the message PDU is also
broadcast.

### Problem

The typing indication intuitively appears to have a very ephemeral meaning. Their
specification as an EDU allows an order of magnitude more of them to exist than
PDU's and to be easily discarded afterward. In practice, typing events are a very
small part of the overall loads on implementations within Matrix. Consider in situ,
typing events repel each other because users actually avoid typing at the same
time. The result is that if typing indications were a part of the room timeline
they would not overload it by any means; we contend that the timeline would even
be enriched by their presence.

### Solution

We specify the Event type `m.typing`. An `m.typing` event with `content` containing a
`timeout` millisecond integer field can be transmitted to the room, providing and
replacing the existing functionality of the `m.typing` EDU. Furthermore, we specify
that within the content of this event, an `m.relates_to` with a `rel_type` of
`m.typing` indicates to the remote party which message will be the focus of the
typing user.

- Implementations should indicate a user is typing upon receipt of a valid `m.typing`
event, and remains for at most the duration of the `content.timeout`.

- When `content.timeout` is undefined, zero, or null, implementations should
indicate a user is not typing.

- Further messages of type `m.room.message` from the user also indicate a user is no
longer typing, and thus transmitting parties should not negate prior typing events when the
user sends a visible message.
