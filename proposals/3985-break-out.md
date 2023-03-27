# MSC3985: Break-out rooms

VoIP applications such as Zoom or MS Teams support break-out rooms - a mechanism
for splitting users into multiple calls. This proposal suggests a mechanism for
break-out rooms in Matrix which would not be limited to VoIP use-cases.

## Proposal

When a user wants to break-out the "parent" room's users into multiple "child"
rooms, their client should first create those rooms and then send an
`m.breakout` event:

```json5
{
    "type": "m.breakout",
    "state_key": "cvsiu2813",
    "content": {
        "m.breakout": {
            "!roomId1": {
                "via": ["example.org", "other.example.org"],
                "users": ["userId1", "userId2"]
            },
            "!roomId2": {
                "via": ["example.org", "other.example.org"]
            }
        }
    }
}
```

This event contains a map of the "child" rooms along with their `via`s. The
event may also include information about the users who are suggested to join a
given "child" room.

When the event is received by the other clients in the room, they should give
their users the option to join the given rooms. If the user is suggested to join
a specific room, the UI should reflect that.

If a user is participating in a call when the event is sent, they should either
start a call or join an existing call in the "child" room, if there is one.

The "child" rooms may have `join_rules` of the user's, which has initiated the
break-out, or their client's choosing.

## Potential issues

None that I can think of.

## Alternatives

An alternative for the VoIP use-case would be having multiple calls in one room
along with multiple threads for chat. While this works alright for some
use-cases, it has its limitations.

## Security considerations

None that I can think of.

## Unstable prefix

While this MSC is unstable, `org.matrix.msc3985.breakout` should be used instead
of `m.breakout`.

## Dependencies

None that I can think of.
