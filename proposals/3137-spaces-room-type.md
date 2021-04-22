# Proposal for Matrix Spaces room type

This MSC is a subset of 
[MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772).

https://github.com/matrix-org/matrix-doc/pull/1840#issuecomment-460070485

## Background and objectives

As part of progressing [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772)
we have identified that we can obtain the greatest flexibility with the lowest risk by
separating out the space room type definition into its own MSC and get it stabilised
before the rest of the proposals.

That way any migrations therein do not need to burn and create new rooms, can just
migrate state events within the otherwise stable space rooms, this helps avoid yet
another room upgrade cycle, which is a very degraded experience, in the process of
getting Spaces out of the door.

## Proposal

Each space is represented by its own room, known as a "space-room". 

Space-rooms are distinguished from regular messaging rooms by the presence of a
`type: m.space` property in the content of the `m.room.create` event. This allows clients to
offer slightly customised user experience depending on the purpose of the
room. Currently, no server-side behaviour is expected to depend on this property.

All other behaviours, additional functionality, endpoints, state events are to be
defined by other MSCs to allow the greatest flexibility.

### Membership of spaces

Users can be members of spaces (represented by `m.room.member` state events as
normal). The existing [`m.room.history_visibility`
mechanism](https://matrix.org/docs/spec/client_server/r0.6.1#room-history-visibility)
controls whether membership of the space is required to view the room list,
membership list, etc.

"Public" or "community" spaces would be set to `world_readable` to allow clients
to see the directory of rooms within the space by peeking into the space-room
(thus avoiding the need to add `m.room.member` events to the event graph within
the room).

Join rules, invites and 3PID invites work as for a normal room, with the
exception that `invite_state` sent along with invites should be amended to
include the `m.room.create` event, to allow clients to discern whether an
invite is to a space-room or not.

## Related MSCs

 * [MSC1772](https://github.com/matrix-org/matrix-doc/issues/1772): Matrix
   spaces.

 * [MSC2946](https://github.com/matrix-org/matrix-doc/issues/2946): Spaces
   Summary API.
   
 * [MSC3088](https://github.com/matrix-org/matrix-doc/issues/3088): Room
   subtyping.
   
 * [MSC1840](https://github.com/matrix-org/matrix-doc/issues/1840): Typed
   rooms.

## Security considerations

None at present.

## Potential issues

None at present.

## Rejected alternatives

### Use a separate state event for type of room

[MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) proposes the use
of a separate `m.room.type` state event to distinguish different room
types. This implies that rooms can dynamically switch between being a Space,
and being a regular non-Space room. That is not a usecase we consider useful,
and allowing it would impose significant complexity on client implementations.

## Unstable prefix

The following mapping will be used for identifiers in this MSC during
development, they are inherited from MSC1772 to prevent yet another
breaking change:

Proposed final identifier       | Purpose | Development identifier
------------------------------- | ------- | ----
`type` | property in `m.room.create` | `org.matrix.msc1772.type`
`m.space` | value of `type` in `m.room.create` | `org.matrix.msc1772.space`
