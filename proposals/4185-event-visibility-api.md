# MSC4185: Event visibility API

Matrix events will often relate to other events.
A user can send an event A with a relation to event B while not having access to event B in the first place.
While it is harmless in regular Matrix usage, integrations -- such as bridges
-- may then find it hard or impossible to figure out how to handle such a situation.

Consider an event that replies to another event.
An integration may want to process it into a form with an excerpt from the original event, followed by the reply.
While sensible in the general case, this does open an opportunity for an information leak,
if the user sending a reply does not in fact have access to the original event.

Integrations have a limited capacity for figuring out whether or not user does have access to a given event.
As mentioned in [the issue that provoked this proposal](https://github.com/matrix-org/matrix-spec/issues/1747),
while this information can be derived from the room state, it's not very practical.
Matrix servers do have that information, and it'd be nice of them to share it.

## Proposal

This MSC proposes a new API endpoint that'd expose the information that the server already has:
can user X access the event Y.

It could take form of a endpoint such as

    GET /_matrix/client/v1/can_user_see_event/<room_id>/<user_id>/<event_id>

That responds with a boolean, revealing if `<user_id>` has access to `<event_id>` in `<room_id>`.
The endpoint is only accessible to users that do have access to the given event themselves.

## Potential issues

While the homeserver is likely to have event visibility information cached for its local users,
the operation could be end up costly when performed for remote users.
Still, even for that case, the homeserver is probably in the best position to calculate this.

## Alternatives

Integrations could figure out event visibility on their own, with enough state tracking and a bit of logic.
In addition to putting more load on the integration (duplicating the functionality that the homeserver already has),
this could also become source of bugs, were the event visibility logic diverge between the server and the integration.
The performance hit is also likely going to be smaller if visibility is calculated on the server
that has all the information available in its database than in an integration that will need to query the server for it.

## Security considerations

With this MSC trying to solve a problem of information leaks, the new API poses a risk of leaking information by itself
-- for example allowing users to see if a target user is a member of a given room using a known recent event ID.

In order to not expose information that the API user wouldn't otherwise know,
the usage of the endpoint is limited to users who, themselves, have access to the given event in the given room.
If we have access to an event, it can be assumed that we also know who was in the room at the time of the event being sent,
so the new endpoint won't expose anything that clients don't already know.

With the intended usecase in mind it would be tempting to make the endpoint accessible only to appservices.
There are however other integration types (such as bots) that could also make use of the proposed event visibility API,
and either way appservices should not be treated as all-powerful entities,
and it makes sense for them to follow the same rules as everyone else does, in this case.

## Unstable prefix

The initial implementation for synapse at [github.com/tadzik/synapse](https://github.com/tadzik/synapse/tree/tadzik/appservice-event-visibility)
uses a `/unstable/net.tadzik` prefix.
