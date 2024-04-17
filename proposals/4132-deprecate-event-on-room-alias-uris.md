# MSC4132: Deprecate Linking to an Event Against a Room Alias.

## Introduction

The spec supports 2 types of URI, the [Matrix scheme](https://spec.matrix.org/v1.10/appendices/#matrix-uri-scheme)
and [matrix.to](https://spec.matrix.org/v1.10/appendices/#matrixto-navigation) links which allow deep linking to
Matrix users, rooms and events. Event URIs can be constructed against either a room ID or a room alias the latter of
which is fragile issue as a room's alias is mutable and so event links may be broken by changes to the alias. Users
expect deep links to continue working so that older links continue to show the correct content. Therefore it is proposed
to deprecate event links against a room alias.


## Proposal

As room IDs are immutable, event URIs built against these will continue to work for as long as the room is reachable by
the homeserver. In contrast, event URIs built against a room alias can break under the following circumstances:
- The room is upgraded, resulting in the alias pointing to the new room, which won't contain any events from the
  ancestor.
- The alias is removed/changed resulting in a dead link that can't be resolved.

The proposal would [deprecate](https://spec.matrix.org/v1.10/#deprecation-policy) the 2 following URIs:
- Link to `$event` in `#somewhere:example.org`: `matrix:r/somewhere:example.org/e/event`
- Link to `$event` in `#somewhere:example.org`: `https://matrix.to/#/%23somewhere:example.org/%24event%3Aexample.org`

Specifically this means it would be marked in the spec as not to be used in future and clients should:
1. Stop making new event URIs with room aliases.
2. Continue to accept them as it will take time for other clients to update and legacy events will continue to exist.


## Potential issues

Whilst most clients do take the sensible route and generate event URIs against a room ID (even when it has an alias), as
it is part of the spec these kinds of links likely exist somewhere in room history and on the World Wide Web. This would
mean that after deprecation clients may still want to handle these URIs when received.


## Alternatives

An alternative would be to leave things as they are, although this wouldn't be the best choice for the user.


## Security considerations

It is unlikely that accepting this change would introduce any security considerations.


## Dependencies

N/A
