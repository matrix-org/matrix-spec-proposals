# MSC4267: Automatically forgetting rooms on leave

Matrix discriminates between "leaving" and "forgetting" a room.
[`/_matrix/client/v3/rooms/{roomId}/leave`] stops a user participating in a room
but still allows them to retrieve history. A subsequent call to
[`/_matrix/client/v3/rooms/{roomId}/forget`] then stops the user from being able
to retrieve history.

Clients don't always differentiate these two operations in their UI and may only
offer leaving without forgetting a room. Thus, some servers automatically forget
rooms when a user leaves them in order to more aggressively free up their
resources. One example of this is the [`forget_rooms_on_leave`] config option in
Synapse.

The present proposal seeks to standaradize this proprietary behaviour.

## Proposal

When a user leaves a room, either through
[`/_matrix/client/v3/rooms/{roomId}/leave`] or by being kicked or banned,
Servers MAY automatically forget the room – as if the user had called
[`/_matrix/client/v3/rooms/{roomId}/forget`] themselves.

This can limit clients' options to maintain an archive of historic rooms (such
that they have left *without* forgetting them). Therefore, servers that
auto-forget rooms MUST advertise that they do so via an `m.forget_forced_upon_leave`
capability.

``` json5
{
  "capabilities": {
    "m.forget_forced_upon_leave": {
      "enabled": true
    }
  }
}
```

A value of `true` means that the server performs auto-forget so that the client
cannot leave rooms without also forgetting them. A value of `false` means that
rooms will only be forgotten when the clients calls
[`/_matrix/client/v3/rooms/{roomId}/forget`].

When the capability is missing, clients SHOULD assume that the server does not
auto-forget.

## Potential issues

None.

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

While this proposal is unstable, clients should refer to
`m.forget_forced_upon_leave` as `org.matrix.msc4267.forget_forced_upon_leave`.

## Dependencies

None.

  [`/_matrix/client/v3/rooms/{roomId}/leave`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3roomsroomidleave
  [`/_matrix/client/v3/rooms/{roomId}/forget`]: https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3roomsroomidforget
  [`forget_rooms_on_leave`]: https://github.com/element-hq/synapse/blob/12dc6b102f071eb2eb84f2cff4cf92903276ffbb/synapse/config/room.py#L88
