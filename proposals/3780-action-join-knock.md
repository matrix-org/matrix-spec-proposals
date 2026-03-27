# MSC3780: Knock on `action=join`

[Matrix URIs][matrix-uri] have an `action` query component,
of which `=join` is taken as a hint that the user joins a particular room as described within the URI.

Knocking was introduced in [room version 7](https://spec.matrix.org/v1.2/rooms/v7/#authorization-rules),
which makes it possible to "knock" (i.e. notify) a room, announcing an intention to join.

However, the [current specification for `=join`][matrix-uri] does not detail knocks as an action a client should present,
when join rules prohibit public joining.

## Proposal

The specification should be updated to state that `=join` will prompt a user with a knocking prompt,
if it cannot join the room via an invite, or a normal public join.

## Potential issues

As the spec currently stands, this would have to be done on a "fallback" basis; The client has to try
joining via a public join, and then try to infer if its a knockable-only room, and present the user a
knock prompt.

As far as this author knows, there exists no specced error code/string that tells the client (when
failing to join) that a room is only knockable.

[MSC3266] - Room Summaries - maybe be
required to allow the client to easily and deterministically infer if a room is (only) knockable.

## Alternatives

`action=knock`, this would allow the client to instantly know which action (out of joining or knocking)
to take when it is given this URI. However, once/if a room join rules change, it might not be possible
to "blindly knock" a room, and this author believes that encoding "current states" of the room into the
URI is not a good practice because of this.

In comparison, `action=join` encompassing knocks would allow for more generic, unified and resilient logic when it
comes to joining rooms.

## Security considerations

None identified.

## Unstable prefix

None required.

## Dependencies

For optimal performance, this MSC heavily leans on [MSC3266].

[matrix-uri]: https://spec.matrix.org/v1.2/appendices/#matrix-uri-scheme
[MSC3266]: https://github.com/matrix-org/matrix-spec-proposals/pull/3266