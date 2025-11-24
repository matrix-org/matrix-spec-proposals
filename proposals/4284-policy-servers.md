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

A *Policy Server* (PS) is a server which implements the newly-defined `/sign` API described below.
This may be an existing logical server, such as matrix.org, or a dedicated host which implements the
minimum surface of the [Federation API](https://spec.matrix.org/v1.15/server-server-api/) to operate
the `/sign` API and exist in the room. For a dedicated host, this means:

* Supporting [normal server name resolution](https://spec.matrix.org/v1.15/server-server-api/#resolving-server-names).
* [Publishing a signing key](https://spec.matrix.org/v1.15/server-server-api/#publishing-keys).
* Understanding [authentication](https://spec.matrix.org/v1.15/server-server-api/#authentication).
* Being able to [make and send join requests](https://spec.matrix.org/v1.15/server-server-api/#joining-rooms).

Some dedicated host implementations may also wish to support:

* [Invites](https://spec.matrix.org/v1.15/server-server-api/#inviting-to-a-room) to be added to rooms.
* [Receiving transactions](https://spec.matrix.org/v1.15/server-server-api/#transactions) (possibly
  routing to `/dev/null`) to minimize risk of remote servers flagging them as "down".
* Supporting [device lookups](https://spec.matrix.org/v1.15/server-server-api/#get_matrixfederationv1userdevicesuserid)
  to again minimize risk of remote servers flagging the policy server as down.

Logical servers may prefer to have dedicated software run their `/sign` API, but otherwise leave the
remaining Federation API endpoints to be served by their existing software.

Existing homeserver software, such as Synapse, may further benefit by supporting `/sign`, but deferring
the actual spam/neutral check to a module or appservice (via API not defined by this MSC). In this
setup, Synapse would take on the request authentication and signature requirements while the module
simply returns `spam: true/false`. This would support moderation bots being policy servers themselves
without needing to implement the same requirements as dedicated hosts above.

Rooms which elect to use a policy server would do so via the new `m.room.policy` state
event (empty state key). The `content` has the following implied schema:

```json5
{
    "via": "policy.example.org", // the server name of the policy server
    "public_key": "unpadded_base64_signing_key" // that server's *public* signing key used for `/sign`
}
```

**TODO**: Array for multiple policy servers?

Provided `policy.example.org` is in the room, that server receives events as any other homeserver
in the room would, *plus* becomes a Policy Server. If `policy.example.org` is not in the room, the
assignment acts as though it was undefined: the room does not use a policy server. This check is to
ensure the policy server has agency to decide which rooms it actually generates recommendations for,
as otherwise any random (potentially malicious) community could drag the policy server into rooms and
overwhelm it.

When creating an event locally, homeservers SHOULD call the `/sign` API defined below to acquire a
signature from the policy server, if one is configured for the room. The homeserver then appends the
signature to the event prior to delivering the event to other servers in the room.

Upon receipt of an event in a room with a policy server, the homeserver SHOULD verify that the policy
server's signature is present on the event *and* uses the key from the `m.room.policy` state event.
If the signature is missing, invalid, or for the wrong key, the homeserver SHOULD [soft fail](https://spec.matrix.org/v1.15/server-server-api/#soft-failure)
the event.

Servers MUST NOT validate that policy server signatures exist on `m.room.policy` state events with
empty state keys. This is to ensure that rooms have agency to remove/disable the policy server,
especially if the policy server they're using has become obstructive to the room's function.

**Note**: Policy servers are consulted on *all* other event types. This includes membership events,
power level changes, room name changes, room messages, reactions, redactions, etc.

For clarity, when a room doesn't use a policy server (either because the state event is unset, or
because the policy server isn't joined), events SHOULD NOT be impeded by lack of policy server signatures.
This also applies to events which are topologically ordered at a point in the DAG where a policy
server was not in effect, but were received late.

When implemented fully, users attempting to send "spammy" events according to the policy server will
not be sent to the room because the homeserver will have failed to acquire a signature. Users also
won't see events which lacked a valid signature from the policy server, for events which originate
from a homeserver that sent events without asking the policy server to sign them (or did ask and got
a refusal to sign, but sent the event anyway).

**Note**: A future MSC may make the signature required in a future room version, otherwise the event
is rejected. The centralization concerns of that architecture are best reserved for that future MSC.

The new `/sign` endpoint uses normal Federation API authentication, per above, and MAY be rate limited.
It has the following implied schema:

```
POST /_matrix/policy/v1/sign
Authorization: X-Matrix ...
Content-Type: application/json

{PDU-formatted event}
```

The request body is **required**.

If the policy server deems the event "neutral" (or "probably not spam"), the policy server returns
a signature for the event using the key implied by `public_key` in the state event and a Key ID of
`ed25519:policy_server`, like so:

```jsonc
{
    "policy.example.org": {
        "ed25519:policy_server": "zLFxllD0pbBuBpfHh8NuHNaICpReF/PAOpUQTsw+bFGKiGfDNAsnhcP7pbrmhhpfbOAxIdLraQLeeiXBryLmBw"
    }
}
```

If the policy server refuses to sign the event, it returns 200 OK with an empty JSON object instead
of a normal error response. This is to leave error codes open for problems with the request itself,
such as invalid events for the room version (`400 Bad Request`). **TODO**: define such error codes.

For improved security, policy servers SHOULD NOT publish the key they use inside the state event on
[`/_matrix/key/v2/server`](https://spec.matrix.org/v1.15/server-server-api/#get_matrixkeyv2server).
This is to prevent an attack surface where a signing key is compromised and thus allows the attacker
to impersonate the server itself (though, they'll still be able to spam events as much as they want
because they can self-sign).

In some implementations, a homeserver may cooperate further with the policy server to issue redactions
for spammy events, helping to keep the room clear for users on servers which don't validate the signature
on events. For example, `matrix.example.org` may have a user in the room with permission to send
redactions and redacts all events that aren't properly signed by the policy server.

### Implementation considerations

When determining whether to sign an event, policy servers might wish to consider the following cases
in addition to any implementation-specific checks/filters:

* Is the requesting server [ACL'd](https://spec.matrix.org/v1.15/server-server-api/#server-access-control-lists-acls)?
  The `/sign` endpoint is open to ACL'd servers, but that doesn't mean it needs to return a signature
  for such servers.
* **TODO**: Add more as they are encountered.

## Potential issues

**TODO**: This section.

Notes for TODO:
* Redacting the policy server event is 😬, especially because it causes the key to vanish
* Broadly: Lack of batching is unfortunate (**TODO**: Fix this(maybe??))
* "SHOULD soft fail when no signature is present" is problematic when operating a room with outdated
  servers which don't know they're supposed to get a signature. **TODO**: figure out migration plan
  and/or advice for how to handle that case (allow anyway but (somehow) flag as "possible spam"?).
* If the policy server can't be reached, servers are forced to assume that the event is spammy. Those
  servers probably should retry the request. As of writing, it's believed to be a feature that *no*
  events can be sent when the policy server is down (aside from removing the policy server, so rooms
  have an escape hatch during extended outages).

## Safety considerations

**TODO**: This section.

## Security considerations

**TODO**: This section.

Notes for TODO:
* Policy servers are natural targets for DDoS attempts, especially because when they can't be reached,
  the room is unusable.

## Alternatives

**TODO**: More alternatives.

One possible alternative is to have servers `/check` events at time of receipt rather than `/sign` at
send time, though this has a few issues:

1. It's non-deterministic. If the policy server forgets what it replied for a given event, it may
   cause one server to soft fail it while another doesn't. This has proven to be the case in practice,
   especially when the policy server cannot be reached right away.

2. It's `O(n)` rather than `O(1)` scale, where `n` is the number of servers in the room. This can lead
   to traffic patterns in the single-digit kHz range in practice.

3. It requires the policy server to have near-100% uptime as a `/check` request could come in late
   when a receiving server has fallen behind on federation traffic. By putting the signing key into
   the room state itself, we ensure that servers can validate the signatures without needing the
   policy server to be online. Outages on the policy server will still affect net-new event sending,
   but events already signed and working their way through federation don't need 100% SLA uptime to
   work.

   The approach of putting the key into the room itself is similarly used in [MSC4243](https://github.com/matrix-org/matrix-spec-proposals/pull/4243)
   to ensure that user-sent events have less dependency on their server being online and reachable to
   accept into the DAG. Readers are encouraged to review MSC4243 for additional context on why it's
   important to remove the network dependency from signature verification (where possible).

## Unstable prefix

While this proposal is not considered stable, implementations should use the following unstable identifiers:

| Stable | Unstable |
|-|-|
| `/_matrix/policy/v1/sign` | `/_matrix/policy/unstable/org.matrix.msc4284/sign` |
| `m.room.policy` | `org.matrix.msc4284.policy` |

**Note**: Due to iteration within this proposal, implementations SHOULD fall back to `/check` (described
below) when `/sign` is unavailable or when `public_key` is not present in the `org.matrix.msc4284.policy`
state event.

## Dependencies

This proposal has no direct dependencies.

## Prior iteration

This proposal has iterated since it was originally written. This section exists to capture a summarized
form of the prior experiments, but is not intended to enter the spec - this exists for reference only.

### `/check` API

A new `/check` is described as follows:

```
POST /_matrix/policy/unstable/org.matrix.msc4284/event/:eventId/check
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

As shown, `recommendation` may either be `spam` or `ok`. (**TODO**: Consider different keywords)

Homeserver implementations SHOULD fail safely and assume events are *not* spam when they cannot reach
the policy server. However, they SHOULD also attempt to retry the request for a reasonable amount of
time.

Comments not incorporated into text:
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2107839742 - Why optional body?
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2051075167 - Require signature check on body?
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2254883244 - Error for when the policy server
  knows it's not protecting that room?
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2089903103 - Warnings system.
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2254826194 - Check ACLs?
