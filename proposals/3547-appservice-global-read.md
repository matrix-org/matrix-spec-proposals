# MSC3547: Allow appservice bot user to read any rooms the appserice is part of

Currently if an appservice wants to read information about a room (say, request an event via `/_matrix/client/r0/rooms/$room/event/$foo`),
it needs to know which of it's users are present in that room in order to request it. In most cases, the
`sender_localpart` user is joined to the room and so most requests do not require masquerading in order
to read the event.

It's desirable to sometimes have only ghost users in a room though, such as in the case of handling DMs.
In these cases, the service must know the membership of the room in advance to masquerade as the right user,
in order to fetch the event. This requires the appservice to hold state about who is in the room, either caching
locally or fetching via an endpoint like `/_matrix/client/r0/joined_members`.

Given that appservices are designed for a single actor/application to control multiple users, there is very
little point in requiring masquerading in order to read information from rooms. This MSC therefore asserts
that the `sender_localpart` user identity (or the lack of a `?user_id` query parameter) should imply that
the request is on behalf of the whole appservice. Any request made on behalf of the appservice should be
allowed if *any* of it's users are present in the room.
## Proposal

The rules should be changed for the following endpoints:

- `GET /rooms/:room_id/state`
- `GET /rooms/:room_id/context/:event_id`
- `GET /rooms/:room_id/event/:event_id`
- `GET /rooms/:room_id/state/:event_type/:state_key`
- `GET /rooms/:room_id/messages`
- `GET /rooms/:room_id/members`
- `GET /rooms/:room_id/joined_members`

If a request is made (that does **NOT** include a `user_id` query parameter) by an application service,
it should be granted if any users in it's `namespaces.user` registration match any users joined to the room.


## Potential issues

Any appliation services that currently use the failure of a event lookup to determine if the bot is part of the room
will now see a success rather than a failure, leading to false positives. However this is a considerable
mis-use of the API and application developers should be using other endpoints, such as the membership APIs to
determine this.


## Alternatives

One alternative is simply that an application service must always store at least one member that it knows
of in the room, in order to always know which user to masquerade as. While this is a practical solution to
the problem, it does pose a problem for library development.

For example, a piece of middleware that automatically fetches the original message when a reply is encountered
will now need to hold the state of who is joined to the room in advance, rather than simply requesting via the
appservice user. It's advantageous to bridge developers to seperate state in certain areas of their application in
these instances.

## Security considerations

While this proposal means that the appservice user can effectively read events from any rooms any namespaced
user is part of, it doesn't change the security impact. It is already possible to read these events by determining
the membership in the target room, and masquerading as a user that has access.

## Unstable prefix

Not required, this proposal proposes to change the authorization rules of existing endpoints but does not change
the overall behaviour.
## Dependencies

No dependencies.
