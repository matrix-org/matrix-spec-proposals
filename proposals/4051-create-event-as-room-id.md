# MSC4051: Using the create event as the room ID

Matrix has a dedicated [room ID grammar](https://spec.matrix.org/v1.8/appendices/#room-ids) which
aims to ensure there is a single identifier representing the room. This is done by using the origin
server's name in the ID, which often leads to confusion among users and admins that the listed server
"owns" the room.

**TODO(TR): Insert security context.**

This proposal uses the create event's event ID as the room ID instead, ensuring there is a fully
unique value that can be used.

## Proposal

A new room version is established to accommodate the event format, redaction, and identifier changes
from this proposal.

The `room_id` field is removed from events, and no longer protected from redaction. The create event's
reference hash is used and prefixed with `!` when a room ID is needed (such as in API endpoints).

The create event is already selected as an auth event for all events in the room, allowing servers to
easily determine which room ID the sent event belongs.

Events served over the client-server API MUST still include a `room_id`. Clients should already be
treating the value as opaque, and therefore should not break when encountering the serverless value.

**TODO(TR): Maybe go into *a bit* more detail...**

## Potential issues

**TODO(TR): This**

## Alternatives

**TODO(TR): This**

## Security considerations

**TODO(TR): This**

## Unstable prefix

**TODO(TR): This**

## Dependencies

As of writing, this MSC is being evaluated as a potential feature for use in the MIMI working group at
the IETF through the Spec Core Team's efforts.
