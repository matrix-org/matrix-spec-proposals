# MSC4284: Policy Servers

**Note**: The concepts and architecture proposed by this MSC are rapidly iterating and will change.
Review is appreciated with the understanding that absolutely nothing is set in stone. Where security
issues are present, please use the [Security Disclosure Policy](https://matrix.org/security-disclosure-policy/)
rather than leaving inline comments. This is to ensure application integrity for those opting to use
highly experimental and changing implementations of this proposal.

Communities on Matrix are typically formed through [Spaces](https://spec.matrix.org/v1.14/client-server-api/#spaces),
but can be made up of singular rooms or loose collections of rooms. These communities often have a
desire to push unwelcome content out of their chats, and rely on bots like [Mjolnir](https://github.com/matrix-org/mjolnir),
[Draupnir](https://github.com/the-draupnir-project/Draupnir), and [Meowlnir](https://github.com/maunium/meowlnir)
to help manage their community. Many of these communities have additionally seen a large increase in
abusive content being sent to their rooms recently (as of originally writing). While these existing tools allow for reactive
moderation (redactions after the fact), some impacted communities may benefit from having an option
to use a server of their choice to automatically filter events at a server level, reducing the spread
of abusive content. This proposal experiments with this idea, calling the concept *Policy Servers*.

This proposal does not seek to replace community management provided by the existing moderation bots,
but does intend to supplement a large part of the "protections" concept present in many of these bots
to the room's designated policy server. It is expected that protections will continue to be developed
and maintained within moderation bots as an additional layer of safety.

At a high level, policy servers are *optional* recommendation systems which help proactively moderate
communities on Matrix. Communities which elect to use a policy server advertise their choice through
state events in individual rooms, and homeservers in the room may reach out to the chosen server for
opinions on how to handle local and remote events *before* those events are delivered to their users.
The functional role of being a policy server may be implemented by a dedicated server, typically
optimized for moderation, or integrated within a homeserver implementation.

In the general case, a homeserver which honours a policy server's recommendation to flag an event as
spam would [soft fail](https://spec.matrix.org/v1.14/server-server-api/#soft-failure) remote events
and reject local events to avoid delivering them to users. Servers which don't honour those recommendations
may see redactions issued by a server/user in the room to help protect those users too, much as the
moderation bots listed above already do today.

This tooling is entirely optional, and decided upon by the room/community itself, similar to moderation
bots. The specific filtering behaviour is left as an implementation detail, and is expected to be
configurable by the community using the policy server. Some examples may include preventing images
from being sent to their rooms, disallowing lots of messages from being sent in a row, and limiting
the number of mentions a user can make.

While there isn't anything which prevents policy servers from operating in private or encrypted rooms,
the intended audience is public (or near-public) rooms and communities. Most communities may not need
a policy server and can instead rely on moderation bots or other forms of moderation. Those which do
decide to use a policy server may find that they have it disabled or in a low power state most of the
time.

## Proposal

**This is a work in progress.**

A *Policy Server* (PS) is a server which implements the newly-defined `/check` API described below.
This may be an existing logical server, such as matrix.org, or a dedicated host which implements the
minimum surface of the [Federation API](https://spec.matrix.org/v1.15/server-server-api/) to operate
the API and exist in the room. In practice, this means:

* Supporting [normal server name resolution](https://spec.matrix.org/v1.15/server-server-api/#resolving-server-names).
* [Publishing a signing key](https://spec.matrix.org/v1.15/server-server-api/#publishing-keys).
* [Understanding authentication](https://spec.matrix.org/v1.15/server-server-api/#authentication).
* Being able to [make and send join requests](https://spec.matrix.org/v1.15/server-server-api/#joining-rooms).

Some implementations may also wish to support:

* [Invites](https://spec.matrix.org/v1.15/server-server-api/#inviting-to-a-room) to be added to rooms.
* [Receiving transactions](https://spec.matrix.org/v1.15/server-server-api/#transactions) (possibly
  routing to `/dev/null`) to minimize risk of remote servers flagging them as "down".
* Supporting [device lookups](https://spec.matrix.org/v1.15/server-server-api/#get_matrixfederationv1userdevicesuserid)
  to again minimize risk of remote servers flagging the policy server as down.

Rooms which elect to use a policy server would do so via the new `m.room.policy` state
event (empty state key). The `content` would be something like:

```json5
{
    "via": "policy.example.org"
}
```

**TODO**: Array for multiple policy servers?

Provided `policy.example.org` is in the room, that server receives events as any other homeserver
in the room would, *plus* becomes a Policy Server. If `policy.example.org` is not in the room, the
assignment acts as though it was undefined: the room does not use a policy server. This check is to
ensure the policy server has agency to decide which rooms it actually generates recommendations for,
as otherwise any random (potentially malicious) community could drag the policy server into rooms and
overwhelm it.

If a policy server is in use by the room, homeservers SHOULD call the `/check` API defined below on
all locally-generated events before fanning them out, and on all remote events before delivering them
to local users. If the policy server recommends treating the event as spam, the event SHOULD be soft
failed if remote and rejected if local. This means local users should encounter an error if they
attempt to send "spam" (by the policy server's definition), and events sent by remote users will
never make it to a local user's client. If the policy server recommends allowing the event, the event
should pass unimpeded.

For Synapse homeservers, the above paragraph's consequences are natural behaviour of the spam checker
module feature. A server could, with some performance penalty, deploy a module which calls the `/check`
API to enact the consequences described above.

The new `/check` is described as follows:

```
POST /_matrix/policy/v1/event/:eventId/check
Authorization: X-Matrix ...
Content-Type: application/json

{PDU-formatted event}
```

The request body is *optional* but *strongly recommended* for efficient processing, as the policy
server may not make efforts to locate the event over federation, especially during `/check`.

Authentication is achieved using normal [Federation API request authentication](https://spec.matrix.org/v1.14/server-server-api/#request-authentication).

Requests may be rate limited, but SHOULD have relatively high limits given event traffic.

The endpoint always returns `200 OK`, unless rate limited or a server-side unexpected error occurred.
If the request shape is invalid, the policy server SHOULD respond with a `spam` recommendation, as
shown below. If the event (or room) is not known to the policy server, it is left as an implementation
detail for whether to consider that event as `spam` or `ok`.

```
200 OK
Content-Type: application/json

{"recommendation": "spam"}
```

```
200 OK
Content-Type: application/json

{"recommendation": "ok"}
```

```
429 Rate Limited
Content-Type: application/json

{"error":"Too many requests","errcode":"M_RATE_LIMITED"}
```

```
500 Internal Server Error
Content-Type: application/json

{"error":"It broke","errcode":"M_UNKNOWN"}
```

**TODO**: Figure out a way to expose which filters (if any) caused an event to be flagged as spam, to
allow for more nuanced decision making by servers/bots. Also, if exposed, figure out a way to do so
which doesn't expose that detail to potential attackers. Consider exposing with score metrics per filter.

As shown, `recommendation` may either be `spam` or `ok`. (**TODO**: Consider different keywords)

**TODO**: Support namespaced identifiers in an array for more recommendations? ie: `[ok, org.example.warn_user]`

Homeserver implementations SHOULD fail safely and assume events are *not* spam when they cannot reach
the policy server. However, they SHOULD also attempt to retry the request for a reasonable amount of
time.

In some implementations, a homeserver may cooperate further with the policy server to issue redactions
for spammy events, helping to keep the room clear for users on servers which didn't check with the
policy server ahead of sending their event(s). For example, `matrix.example.org` may have a user in
the room with permission to send redactions and `/check`s all events.

## Potential issues

**TODO**: This section.

Broadly:
* Lack of batching is unfortunate (**TODO**: Fix this)

## Safety considerations

**TODO**: This section.

## Security considerations

**TODO**: This section.

## Alternatives

**TODO**: This section. Many of the inline TODOs describe some alternatives.

An alternative was considered where, in a future room version, all events must be signed by the policy
server before they're able to be added to the DAG. However, this results in compulsory centralization
and usage, removing the room's agency to choose which moderation tools they utilize and that room's
ability to survive network partitions. This alternative does have an advantage of reducing bandwidth
spend across the federation (as there's no point in sending a spammy event if the policy server won't
sign it), but would require that communities upgrade their rooms to a compatible room version, which
typically take significant time to specify and deploy.

## Unstable prefix

While this proposal is not considered stable, implementations should use the following unstable identifiers:

| Stable | Unstable |
|-|-|
| `/_matrix/policy/v1/event/:eventId/check` | `/_matrix/policy/unstable/org.matrix.msc4284/event/:eventId/check` |
| `m.room.policy` | `org.matrix.msc4284.policy` |

## Dependencies

This proposal has no direct dependencies.
