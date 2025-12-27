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

The existence of this server-side feature creates a problem. Without knowing
whether or not the homeserver will automatically forget rooms on leave, clients
are limited in their UX choices around forgetting rooms. For instance, a client
might want to:

-   simultaneously display buttons for "leave" (`/leave`) and "leave & forget"
    (`/leave` followed by `/forget`)
-   offer a setting to toggle what a single "leave" button does (`/leave`
    followed or not followed by `/forget`)
-   explain the finality or non-finality of a single "leave" button before
    issuing a `/leave` (e.g. in a tooltip or dialog)
-   display the empty "historical rooms" view or section alongside some
    documentation explaining what it is or how it'll be populated

On a server that automatically forgets rooms on leave, these would result in
confusing UX, however.

The present proposal seeks to standaradize the currently proprietary behaviour
of automatically forgetting rooms on leave in way that allows clients to discover
the server's configuration and adapt their UI accordingly.

Note that forgetting rooms as currently spec'ed has a separate problem in that
forgotten rooms are not communicated via incremental syncs. In a scenario where
users have multiple clients, this means that occasional initial syncs are
required to determine the correct set of historical rooms. This proposal does
not seek to address this issue.

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
