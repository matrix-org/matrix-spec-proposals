# MSC3901: Deleting State

Matrix rooms have an ever-growing list of state, caused by real-world events
like someone joining a room or sharing their live location.

Even when this state is potentially of little interest (e.g a person left the
room a long time ago, or they stopped sharing their location), servers and
clients must continue processing and passing around the state: once a
`state_key` has been created it will always exist in a room.

TODO: refer to live location sharing MSC

This ever-increasing list of state causes load on servers and clients in terms
of CPU, memory, disk and bandwidth. Since some of this state is of little
interest to users, it would be good to reduce this load.

Further, some more recent spec proposals attempt to increase the number of state
events in use, and give permission by default for less-privileged users to
create state events. If these proposals are accepted, it will be easier for
malicious or spammy users to flood a room with undeletable state, potentially
mounting a denial of service attack against involved homeservers. So, some
solution to "clean" an affected room is desirable.

TODO: refer to relevant MSCs: live location, and also the owned state ones.

Over several months in 2022 some interested people got together and discussed
how to address this situation. There was much discussion of how to structure
the room graph to allow "forgetting" old state, and not all ideas were fully
explored, but all added complexity, and most ended up with some idea of a new
root node, similar in character to a `m.room.create` event.

We already have a mechanism to start a new room based on an old one: room
upgrades. So, we agreed to explore ideas about how to make room upgrades more
seamless, in the hope that they will become good enough to allow "cleaning"
rooms of unimportant state.

TODO: link to room upgrades in spec.

We propose improving room upgrades in various ways, and offering an "Optimise
Room" function in clients that allows room administators to "upgrade" a room
(manually) to a new one with the same version.

With enough improvements to upgrades, we believe this will materially improve
the current situation, since there will be a viable plan for rooms that become
difficult to use due to heavy activity or abuse.

We accept that an automatic process that was fully seamless would be better,
but we were unable to design one, and we hope that:

a) improvements to room upgrades may eventually lead to a process that is so
   smooth it can be automatic, or at least very easy, and

b) improvements to room upgrades will bring benefits Matrix even if they don't
   turn out to be the right way to solve the deleting state problem.

## Proposal

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix

## Dependencies
