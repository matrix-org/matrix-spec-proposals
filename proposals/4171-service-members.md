# MSC4171: Service members
Matrix has lots of bots for different use cases: simple chat bots, bridge bots,
administration bots, etc. Currently, such bots can't be added to DMs without
messing up the automatic room name and avatar calculation. [Canonical DMs] may
solve the issue eventually, but implementing those will likely take quite a
while due to the complexity of the system. This proposal is an intermediate
solution for bots before canonical DMs are fully implemented.

[Canonical DMs]: https://github.com/matrix-org/matrix-spec-proposals/pull/2199

## Proposal
The proposed solution is a new state event: `m.member_hints`. The state event
contains a field called `service_members` which is a list of user IDs.

Any users (service members) listed there should not be considered when
computing the room name or avatar based on the member list. If the room only
has two non-service members, then any additional DM-specific treatment should
be applied as well (for example, using 1:1 semantics for VoIP calls).

To prevent hiding encrypted message recipients, service members MUST still be
visible in the member list and membership events they send MUST be rendered if
other users' membership events are rendered.

Clients may include some special label for service members in the member list
to make it clearer why they're not included in the room name.

Any listed users who are not room members can be safely ignored. Simply being
on the list without actually being a room member has no special behavior.

## Potential issues
Clients that don't support this MSC would still include the service members in
the room name calculation. It may be possible to work around this by excluding
service members from `m.heroes` on the server side, but that may also cause
other issues.

## Alternatives
### Inverted user list
The state event could be inverted to list real members instead of service
members. This approach was not chosen for backwards-compatibility reasons: if
a user is invited with a client that doesn't know about this MSC, it's better
for bots to show up in the name than it is for real users to be hidden from the
name.

## Security considerations
This MSC hides encrypted message recipients to some extent. However, as long as
the requirement to still show the members in the member list is followed, the
situation is no different than "hiding" members by injecting room name/avatar
events.

## Unstable prefix
Due to existing implementations, `io.element.functional_members` should be used
as the event type until this MSC is accepted.
