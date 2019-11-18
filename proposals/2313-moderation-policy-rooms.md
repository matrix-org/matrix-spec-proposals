# MSC2313: Moderation policies as rooms (ban lists)

Matrix is an open network and anyone can participate in it. As a result, a
very wide range of content exists, and it is important to empower users to be
able to select which content they wish to see, and which they wish to block. By
extension, room moderators and server admins should also be able to select
which content they do not wish to host in their rooms and servers.

The protocol's position in this solution should be one of neutrality: it
should not be deciding what content is undesirable for any particular entity and
should instead be empowering those entities to make their own decisions. This
proposal introduces "moderation policy rooms" as a basic mechanism to help users
manage this process, by providing a way of modelling sets of servers, rooms and users
which can then be used to make filtering decisions. This proposal makes no
attempt at interpreting the model and actually making those decisions however.

To reaffirm: where this proposal says that some content is undesirable it does not intend to
bias the reader into what that could entail. Undesirability is purely in the hands of the
entity perceiving the content. For example, someone who believes birthday cake is undesirable
is perfectly valid in taking that position and is encouraged by this proposal to set up or
use a policy room which prevents birthday cake from coming across their field of view.

## Proposal

Moderation policy lists, also known as ban lists in this proposal, are stored as room state events,
allowing for structures and concepts to be reused without defining a new room version. This
proposal does not make any restrictions on how the rooms are configured, just that the state
events described here are represented in a room. For example, a room which is invite only is
just as valid as a room that is not: the important details are specific state events and not
the accessibility, retention, or other aspects of the room.

Ban lists are stored as `m.moderation.rule.<kind>` state events, with state keys being arbitrary IDs
assigned by the sender. The `<kind>` is currently one of `user`, `room`, and `server`. Three
fields are defined in `content`:

* `entity` (`string`) - **Required.** The entity/entities the recommendation applies to. Simple globs are supported
  for defining entities (`*` and `?` as wildcards, just like `m.room.server_acl`).
* `recommendation` (`enum`) - **Required.** The action subscribed entities should take against
  the described entity. Currently only `m.ban` is defined (see below).
* `reason` (`string`) - **Required.** The human-readable description for the recommendation.

Invalid or missing fields are to be treated as though the rule doesn't exist. This is to
allow for rules to be deleted while state events cannot be deleted in Matrix.

An example set of minimal state events for banning `@alice:example.org`, `!matrix:example.org`,
`evil.example.org`, and `*.evil.example.org` would be:

```json
[
    {
        "type": "m.moderation.rule.user",
        "state_key": "rule_1",
        "content": {
            "entity": "@alice:example.org",
            "recommendation": "m.ban",
            "reason": "undesirable behaviour"
        }
    },
    {
        "type": "m.moderation.rule.room",
        "state_key": "rule_2",
        "content": {
            "entity": "!matrix:example.org",
            "recommendation": "m.ban",
            "reason": "undesirable content"
        }
    },
    {
        "type": "m.moderation.rule.server",
        "state_key": "rule_3",
        "content": {
            "entity": "evil.example.org",
            "recommendation": "m.ban",
            "reason": "undesirable engagement"
        }
    },
    {
        "type": "m.moderation.rule.server",
        "state_key": "rule_4",
        "content": {
            "entity": "*.evil.example.org",
            "recommendation": "m.ban",
            "reason": "undesirable engagement"
        }
    }
]
```

When the entity is a room, it can be a room alias or ID - the subscriber is responsible for
resolving it to a room ID (if it wants to).

Non-standard recommendations are permitted using the Java package naming convention for
namespacing. A `recommendation` is just a recommendation: how implementations apply the rules
is left as a concern for those implementations. The only standard `recommendation` currently
defined is `m.ban`: The `entity` should be banned from participation where possible.

The enforcement mechanism of `m.ban` is deliberately left as an implementation detail to avoid the
protocol imposing its opinion on how the lists are interpreted. However, a suggestion for
a simple implementation is as follows:

* Is a user...
  * Applied to a user: The user should be added to the subscriber's ignore list.
  * Applied to a room: The user should be banned from the room (either on sight or immediately).
  * Applied to a server: The user should not be allowed to send invites to users on the server.
* Is a room...
  * Applied to a user: The user should leave the room and not join it
    ([MSC2270](https://github.com/matrix-org/matrix-doc/pull/2270)-style ignore).
  * Applied to a room: No-op because a room cannot ban itself.
  * Applied to a server: The server should prevent users from joining the room and from receiving
    invites to it (similar to the `shutdown_room` API in Synapse).
* Is a server...
  * Applied to a user: The user should not receive events or invites from the server.
  * Applied to a room: The server is added as a denied server in the ACLs.
  * Applied to a server: The subscriber should avoid federating with the server as much as
    possible by blocking invites from the server and not sending traffic unless strictly
    required (no outbound invites).

Other entities could be represented by this recommendation as well, however as per the
introduction to this proposal they are strictly out of scope. An example would be an integration
manager which doesn't want to offer integrations to banned entities - this is an implementation
detail for the integration manager to solve.

A new event type is introduced here instead of reusing existing events (membership, ACLs, etc)
because the implication of a recommendation/rule is less clear when using the more narrow-scoped
events. For example, a philosophical question arises over what a `membership` of `ban` means to a server
subscribed to the list. More questions get raised when the `membership` of a user isn't `ban`,
but is `join` or similar instead - if the subscriber was mirroring events, it would be inclined
to try and sync membership lists, which this proposal attempts to avoid by using a more generic
and neutral event type.

How subscriptions to ban lists are handled is also left as an implementation
detail (to avoid unnecessarily blocking progress on this MSC). The subscriber
could be anything that speaks Matrix, therefore this proposal makes no attempt
to describe how this should work for everything. Some ideas for how this could
be implemented include joining the ban list room to watch for updates and
applying them automatically, however there is no requirement that the
subscriber needs to join the room: they could peek or poll at an interval
instead, which is just as valid.

To ease sharing of these ban list rooms, a system very similar to [MSC1951's sharable URLs](
https://github.com/matrix-org/matrix-doc/pull/1951/files#diff-4ee6ed0ee1f2df73efac5fa9a9835642R50-R70)
is defined. There are two ways to share the ban list: a link to the room as one would when
sharing any reference to any other room ("please add `#bans:example.org` to your block list"),
or by using plain `http` or `https` URLs. Just like in MSC1951, the URL when approached with
a `Accept: application/json` header or has `.json` appended to the end of the URL should return
a `room_uri` which is a reference to the ban list room. Currently, the reference would be a
`matrix.to` URI, however in the future this could be a `mx://` or similar URL. When not approached
with the intent of JSON, the service could return a user-friendly page describing what is included
in the ban list.

## Future considerations

This proposal notably does not define specific behaviour for AI or machine learning applications.
Implementations are currently able to apply AI/ML to their systems if they see fit (for example,
spam detection or undesirable content being uploaded), however no specification is proposed
here to make the interaction standardized.

This proposal additionally does not describe how a server could subscribe to a ban list: this
is left for the server to figure out (possibly by using a utility user account?) potentially
with the support of other proposals, such as [MSC1777](https://github.com/matrix-org/matrix-doc/pull/1777).

Further work on reputation systems could enhance ban lists by adding additional metrics to
assert their validity. This proposal assumes social trust ("don't use it if you
don't trust the creator") over verifiable/provable trust - a future proposal can easily add
such systems to these ban lists.

This proposal intentionally does not handle how a server could assist the user in preventing
undesirable content or subscribing to ban lists. Users already have some tools at their disposal,
such as being able to ignore other users, and are encouraged to make use of those first. Other
proposals are encouraged to specify what additional tools might look like to better handle
ban lists.

Media (uploaded content) is not handled by this proposal either. This is a concern left for
other proposals like [MSC2278](https://github.com/matrix-org/matrix-doc/pull/2278) and
[MSC701](https://github.com/matrix-org/matrix-doc/issues/701).

## Security considerations

Using this solution one can build a social system of shared blacklists, which
may create a divide within established communities if not carefully deployed.
This may well not be a suitable answer for all communities.

Depending on how the implementations handle subscriptions, user IDs may be linked to ban
lists and therefore expose the views of that user. Using the example from the introduction,
if a user who does not like birthday cake were to join the ban list room for blocking
birthday cake, that user's preference would be exposed to any other observers of that ban
list. Proposals like [MSC1228](https://github.com/matrix-org/matrix-doc/issues/1228) and
[MSC1777](https://github.com/matrix-org/matrix-doc/pull/1777) could help solve this.

## Implementation notes

This proposal is partially implemented by [mjolnir](https://github.com/matrix-org/mjolnir)
using the `org.matrix.mjolnir.*` namespace until this becomes stable. This results in
the following mappings:

* `m.moderation.rule.user` => `org.matrix.mjolnir.rule.user`
* `m.moderation.rule.room` => `org.matrix.mjolnir.rule.room`
* `m.moderation.rule.server` => `org.matrix.mjolnir.rule.server`
* `m.ban` => `org.matrix.mjolnir.ban`
