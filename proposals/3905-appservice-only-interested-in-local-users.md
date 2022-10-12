# MSC3905: Application services should only be interested in local users

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
behavior mismatch between remote and local users.


## Proposal

Therefore the proposal is that the `users` namespace regex should only be applied
against local users of the homeserver.

A basic implementation of this would look like:

```js
const isLocalUser = sender.endsWith(":" + homeserver.domain);
const isInterestingUser = isLocalUser && sender.matches(regex);
```

```js
const localRoomMembers = getLocalRoomMembers(roomId);
const interestingUsers = localRoomMembers.filter((localRoomMember) => localRoomMember.matches(regex));
```

---

To avoid confusion, please note that the `rooms` and `aliases` namesapces are not
affected. You can still match whatever rooms and aliases to listen to all events
that occur in them.


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


## Historical context

According to @turt2live (SCT member), "the spec intended to [originally] say the
namespace can make an appservice interested in remote users, though there's obviously no
ability for the server to call `/user` on remote users (it's not like the appservice can
create them)." (https://github.com/matrix-org/synapse/pull/13958#discussion_r988369446)

This intention goes back further than `r0` (or `v1.0` in marketing versions speak) but
this history is lost to time since there isn't really anything concrete to point to
beyond the original spec
[issue](https://github.com/matrix-org/matrix-spec-proposals/issues/1307) and
[PR](https://github.com/matrix-org/matrix-spec-proposals/pull/1533) which don't mention
these details.

Since we're unable to come up with any valid use cases nowadays, it's unclear to
outsiders from that time whether the original intention is actually true. In any case,
we're clarifying it here and making an MSC to change it explicitly.


## Unstable prefix

If a homeserver wants to implement this functionality before this MSC merges, since it
only affects application services local to the server, it can be implemented although it
will be technically unspecced behavior until this MSC is merged. Also consider a config
option for maximal compatibility with existing application services people may be using.
