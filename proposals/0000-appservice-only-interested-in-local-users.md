# MSC0000: Application Service should only be interested in local users

Application services receive events that they are "interested" in.

The current language in the spec describes it like this:

> An application service is said to be "interested" in a given event if one of the IDs
> in the event match the regular expression provided by the application service
> [registration]. [...] the application service is said to be interested in a given
> event if one of the application service's namespaced users is the target of the event,
> or is a joined member of the room where the event occurred.

This language is ambiguous around which users it should match against though. Should it
be all members of the room including remote users from other homeservers or just the
local users where the application service lives? It could be assumed either way and
naively applied to all members of the room which is still valid with the current
language and even what Synapse does.

But matching against remote users is merely a footgun because an application service may
assume that it'll receive all events sent by that remote user, even though it will only
receive events in rooms that are shared with a local user. This leaves us with a
behaivor mismatch between remote and local users.




## Proposal

Therefore the proposal is that the `users` namespace regex should only be applied
against local users of the homeserver.



## Potential issues

There are use cases like moderation where an application service wants to hear all
messages from remote users in rooms but these are are also covered by the `rooms`
namespace where all events in a matched room are considered "interesting".



## Alternatives

The alternative is clarify that the `users` namespace should be matched against all
users (local and remote). This still leaves us with the behavior-difference footgun.



## Security considerations

Since we're reducing the surface area, there doesn't seem to be any additional security
considerations introduced.

With this MSC, an application service will be receiving less events than before.



## Unstable prefix

If a homeserver wants to implement this functionality before this MSC merges, since it
only affects application services local to the server, it can be implemented although it
will be technically unspecced behavior until this MSC is merged. Also consider a config
option for maximal compatibility with existing application services people may be using.
