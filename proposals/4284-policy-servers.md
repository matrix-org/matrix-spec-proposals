# MSC4284: Policy Servers

Communities on Matrix are formed through collections of rooms. These communities often have a
desire to push unwelcome content out of their chats, and rely on bots like [Mjolnir](https://github.com/matrix-org/mjolnir),
[Draupnir](https://github.com/the-draupnir-project/Draupnir), and [Meowlnir](https://github.com/maunium/meowlnir)
to help manage their community. Many public communities additionally see abusive content sent to their
rooms. While these existing tools allow for reactive moderation (redactions after the fact), some
impacted communities may benefit from having an option to use a server of their choice to automatically
filter events at a server level, reducing the spread of abusive content. This proposal explores this
idea, calling the concept *Policy Servers*.

This proposal does not seek to replace community management provided by the existing moderation bots,
but does intend to supplement a large part of the "protections" concept present in many of these bots
to the room's designated policy server. It is expected that protections will continue to be developed
and maintained within moderation bots as an additional layer of safety, especially for content which
makes it through the policy server.

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
the number of mentions a user can make. More filter ideas can be found in the Foundation's
[policyserv](https://github.com/matrix-org/policyserv) implementation of this proposal.

While there isn't anything which prevents policy servers from operating in private or encrypted rooms,
the intended audience is public (or near-public) rooms and communities. Most communities may not need
a policy server and can instead rely on moderation bots or other forms of moderation. Those which do
decide to use a policy server may find that they have it disabled or in a low power state most of the
time.

## Proposal

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
  routing to `/dev/null`) to minimize risk of remote servers flagging them as "offline".
* Supporting [device lookups](https://spec.matrix.org/v1.15/server-server-api/#get_matrixfederationv1userdevicesuserid)
  to again minimize risk of remote servers flagging the policy server as offline.

Logical servers might prefer to route `/sign` to dedicated software at their reverse proxy.

Existing homeserver software, such as Synapse, may further benefit by supporting `/sign`, but deferring
the actual spam/neutral check to a module or appservice (via API not defined by this MSC). In this
setup, Synapse would take on the request authentication and signature requirements while the module
simply returns `spam: true/false`. This would support moderation bots being policy servers themselves
without needing to implement the same requirements as dedicated hosts above.

Rooms which elect to use a policy server would do so via the new `m.room.policy` state
event (empty state key). The `content` has the following implied schema:

```json5
{
  "via": "policy.example.org", // the server name providing room policy (the "policy server")
  "public_keys": {
    // MUST contain at least `ed25519` for event signing. The key version will be "policy_server",
    // defined later.
    "ed25519": "unpadded_base64_signing_key" // that server's *public* signing key used for `/sign`
  }
}
```

**Note**: Only a single server can be listed. See the Alternatives section for details on what a
multi-server setup might require.

The sender of the `m.room.policy` state event will need to know the server's `public_keys` in order
to populate the event. To help clients convert a server name to a public key, policy servers SHOULD implement the following
`/.well-known/matrix/policy_server` endpoint. If the endpoint is not supported by the policy server,
the `public_keys` will need to be sourced out of band to populate the state event.

**Note**: Servers MUST only use the `m.room.policy` state event as a source of truth for the policy
server's public key. The well-known endpoint exists exclusively for clients to use to populate the
state event. The endpoint does *not* exist to make `public_keys` optional or act as a secondary lookup
for the key.

`GET /.well-known/matrix/policy_server` is a Client-Server API endpoint similar to the existing
[`/support`](https://spec.matrix.org/v1.17/client-server-api/#getwell-knownmatrixsupport) well-known
endpoint. Policy servers SHOULD support it, where feasible/applicable. It MAY be rate limited, and
MUST NOT require authentication. Like other well-known endpoints,
the request is made to the server's [`server_name`](https://spec.matrix.org/v1.17/appendices/#server-name)
rather than the base URL of the client-server API. Also like other well-known endpoints, it
[supports CORS](https://spec.matrix.org/v1.17/client-server-api/#web-browser-clients).

The `GET /.well-known/matrix/policy_server` endpoint returns a response body as shown below. It SHOULD
have a `Content-Type: application/json` response header.

```jsonc
{
  "public_keys": { // required; the same thing that appears in the state event
    "ed25519": "unpadded_base64_signing_key" // also required, and the same as in the state event
  }
}
```

The state event's `via` is the same as the domain name used to get the JSON document. Callers MUST
use `https://` when calling the endpoint.

The server name in `via` MUST additionally have at least one *joined* user in the room. That user does
not need any special power levels - they just need to be joined. This is to ensure the policy server
itself has agency to decide which rooms it actually generates recommendations for. Otherwise, any
random (potentially malicious) community could drag the policy server into rooms and overwhelm it.

If the room's *current state* has a valid policy server configured for the room (joined + valid
`m.room.policy` event), all homeservers wanting to send an event in the room MUST call the `/sign`
API defined below. If that endpoint returns a signature, the homeserver appends that signature to the
event before sending it to other servers in the room. The endpoint may also refuse to sign the event,
effectively marking it spammy. When this happens, the homeserver SHOULD cease trying to send the event
to other servers and reject/fail any applicable Client-Server API requests that were creating the event.
Those Client-Server API request failures SHOULD use the same error returned by the policy server on
the `/sign` request, if any.

**Note**: The above applies to Federation API requests as well as Client-Server API requests. For
example, during `/send_[join|leave|knock]`, the policy server might decline to sign the membership
event, which leads to the federation request failing.

"Current state" is the same state used to evaluate an event for [soft failure](https://spec.matrix.org/v1.17/server-server-api/#soft-failure).
That state might be different on different servers, though the `m.room.policy` state event is not
expected to change frequently enough for this to be a major concern: at the time of trying to send
any given event, the policy server has likely been set for a long while already.

The `/sign` API uses normal Federation API authentication, per above, and MAY be rate limited.
It has the following implied schema:

```
POST /_matrix/policy/v1/sign
Authorization: X-Matrix ...
Content-Type: application/json

{PDU-formatted event}
```

The request body is **required**.

If the policy server deems the event "neutral" (or "probably not spam"), the policy server returns
a signature using *all* of the keys in `m.room.policy`'s `public_keys`. The key version is *always*
`policy_server` for these keys.

Example:

```jsonc
{
  "policy.example.org": {
    // This uses `public_keys.ed25519` from the `m.room.policy` state event
    "ed25519:policy_server": "zLFxllD0pbBuBpfHh8NuHNaICpReF/PAOpUQTsw+bFGKiGfDNAsnhcP7pbrmhhpfbOAxIdLraQLeeiXBryLmBw"
  }
}
```

If the request was invalid or the policy server refuses to sign the event, it returns any of the
following errors. The error codes are reused from the Client-Server API's [Common Error Codes](https://spec.matrix.org/v1.17/client-server-api/#common-error-codes).

* `400 M_BAD_JSON` - The supplied PDU-formatted event was improperly formatted (ie: missing required
  keys for the room version).
* `400 M_NOT_JSON` - The request body wasn't JSON.
* `404 M_NOT_FOUND` - The room ID is not known or not protected by the policy server.
* `403 M_FORBIDDEN` - The caller is ACL'd (see below).
* `400 M_FORBIDDEN` - The policy server refuses to sign the event. In future, this may be extended
  with more detail, like in [MSC4387: `M_SAFETY` error code](https://github.com/matrix-org/matrix-spec-proposals/pull/4387).

**Note**: Policy servers MAY return *any* of the above errors to indicate failure. For example, if a
policy server wishes to hide whether it knows about a room, it MAY return `400 M_FORBIDDEN` instead
(or, it MAY sign the event anyway).

The 403 `M_FORBIDDEN` error MAY be returned by the policy server if the caller is
[ACL'd](https://spec.matrix.org/v1.17/server-server-api/#server-access-control-lists-acls). This is
not a "MUST" because policy servers may not always have full room state context when optimized for
content moderation over Matrix moderation.

The following errors are returned per normal specification requirements:

* `404 M_UNRECOGNIZED` - The server is not a policy server (the endpoint isn't implemented).
* `405 M_UNRECOGNIZED` - The server is a policy server, but the caller used the wrong HTTP method.
* `429 M_LIMIT_EXCEEDED` - The server is rate limiting the caller.

Upon receipt of an event in a room with a policy server, the homeserver SHOULD verify that the policy
server's signature is present on the event *and* is valid when using the key from the current `m.room.policy` state event.
If the signature is invalid or for the wrong key, the homeserver SHOULD [soft fail](https://spec.matrix.org/v1.15/server-server-api/#soft-failure)
the event. If the signature is plainly missing, the homeserver SHOULD call `/sign` on the policy
server and use that result to determine whether to pass the event through unimpeded or soft fail it.
The homeserver SHOULD persist the policy server's signature with the event so the signature is passed
transitively to other servers which request the event from the homeserver.

**Note**: Signatures might be present but invalid/wrong due to the policy server's key rotating (the
`public_keys` changing between the `m.room.policy` state event *at* the event and the current state's
`m.room.policy` event). In these cases, it's appropriate for a homeserver to request another signature from the policy server
to confirm whether the event is spammy. See the Security Considerations section for details.

**Note**: Advanced tooling, likely built into moderation bots, may further send redactions for events
which are soft failed due to the policy server's recommendation. This helps remove content from the
room for users which are stuck on an older/uncooperative homeserver.

**Note**: Events can be missing signatures either maliciously or accidentally. Outdated servers which
don't support this proposal wouldn't know that they need to get the signature, and servers which
intentionally don't request a signature would be trying to send unwanted content to the room.

**Note**: Because servers will check events against the current policy server for the room, a policy
server might get asked to sign events from "before" it was enabled in the room. This could be because
a server has discovered old history in the room that the policy server hasn't seen before, or due to
the event's sending server experiencing clock drift (potentially maliciously). This would typically
manifest as `origin_server_ts` being "wrong" from the policy server's view. This proposal leaves
handling such events as an implementation detail for policy servers. The Implementation Considerations
section has some suggestions.

Servers MUST NOT validate that policy server signatures exist on `m.room.policy` state events with
empty state keys. This is to ensure that rooms have agency to remove/disable the policy server,
especially if the policy server they're using has become obstructive to the room's function.

**Note**: Policy servers are consulted on *all* other event types. This includes membership events,
power level changes, room name changes, room messages, reactions, redactions, `m.room.policy` events
with non-empty state keys, etc.

For clarity, when a room doesn't use a policy server (either because the state event is unset, or
because the policy server isn't joined), events SHOULD NOT be impeded by lack of policy server signatures.

When implemented fully, a user will see an error message when attempting to send "spammy" events. The
policy server gets to decide what "spammy" means. If the user's homeserver sends the event without
the signature from the policy server (either because it never requested one or because it decided to
send the event despite being refused a signature), other servers will hide the event from users by
soft failing it for lacking that signature.

**Note**: A future MSC is expected to make the signature required in a future room version when a
policy server is in use by the room. Centralization concerns related to that architecture are best
reserved for that future MSC.

### Implementation considerations

* For improved security, policy servers SHOULD NOT publish the key they use inside the `m.room.policy`
  state event on [`/_matrix/key/v2/server`](https://spec.matrix.org/v1.15/server-server-api/#get_matrixkeyv2server).
  This keeps the concerns of "can send federation traffic" and "can mark events as neutral (not spammy)"
  separate, and further means that a room can revoke the key without cooperation from the policy
  server.

* Homeservers or moderation bots MAY cooperate with policy servers to issue redactions for spammy
  events, helping to keep the room clear for users on servers which don't involve the policy server
  in their checks. For example, a room with `policy.example.org` and `matrix.example.org` might have
  redactions sent by `@mod:matrix.example.org` rather than anyone from `policy.example.org`. How this
  cooperation happens is left as an implementation detail.

* If a policy server implements rate limiting, those rate limits *SHOULD* be relatively high. Clients
  often retry events potentially dozens of times before giving up, which can quickly exhaust a server's
  burst limit. Some servers may also be more chatty than others depending on how many active users
  they have. Servers are encouraged to cache results to avoid being overly chatty as well.

* Policy servers SHOULD cache and deduplicate requests to `/sign` based on the event ID. When a server
  sends an event not signed by the policy server in a popular room, all of the other servers in that
  room may request that signature from the policy server right away. This can be a lot of requests.

  Caching and persistent storage is also important for consistency. There is no mechanism to inform servers that an event's
  spam or neutral designation has changed. If the policy server does change designation of an event,
  it can lead to user-visible split brains as one server soft fails the spam and another doesn't.

  A room's policies may also change over time, which may affect an event's designation (if the
  designation were allowed to change).

* Policy servers are *not* required to track the full DAG of the room. Logical servers which implement
  endpoints like [`GET /event`](https://spec.matrix.org/v1.17/server-server-api/#get_matrixfederationv1eventeventid)
  might need to track the DAG in order to reply appropriately, but dedicated policy servers which
  implement the minimal API surface described earlier in this proposal might not have any need to.

  This can be useful for implementations which are primarily concerned about what is about to be seen
  by users rather than what could have been seen by users a long time ago (for example). Such policy
  server implementations might track some definition of "current state", but might not be able to
  evaluate whether a given event is actually authorized in the room.

  This is expected: policy servers do *not* replace authorization rules. They do however add behaviour
  for legal-but-spammy events. Events which are neutral by a policy server's standards might still
  be illegal under the room's authorization rules, and are rejected accordingly.

* DAG-aware policy servers MAY check events sent before the policy server was involved (according to
  the DAG, not according to timestamps) differently from those after the policy server became involved.

  This might include:

  * Allowing the event because it was (presumably) legal at the time in the DAG.
  * Running "critical" checks, but skipping others. For example, scanning media for unwanted content
    but not applying message length limits.
  * Treating the event no different than any other event and running the full suite of checks against
    it.

* Policy servers SHOULD be aware of clock drift, both malicious and accidental. In some cases it may
  be possible to detect events that are being sent before the room was even created, though any
  definition of `time.now()` will need a fairly forgiving range of values to handle slow or out of
  sync servers.

  Policy servers SHOULD NOT use `origin_server_ts` to determine if an event was sent "before" the
  policy server was involved in the room.

## Potential issues

* Already noted in the proposal, existing rooms might have servers in them which don't know about
  policy servers. This can lead to events which aren't signed by the policy server, and thus could
  be considered spam automatically. This proposal aims to minimize this by suggesting that servers
  should ask for a signature from the policy server if the event is missing one, though this can
  lead to a lot of traffic for the policy server.

  In a future MSC and room version, it's expected that the auth rules will be adapted to require a
  signature from the policy server in order to accept an event (if a policy server is configured for
  the room). This will limit the number of excess calls the policy server receives.

  In the meantime, policy servers SHOULD be designed, built, and deployed with the assumption that they will
  receive an extremely high volume of requests, especially during spam waves.

* The `m.room.policy` event is *not* protected from redaction in this proposal. Doing so would require
  a new room version, which delays availability of this tooling to communities. A future MSC (probably
  the same one which fixes the DoS issue above) is expected to alter the redaction algorithm to protect
  critical portions of the `m.room.policy` state event.

  In the meantime, it's advised to never redact `m.room.policy` state events with empty state keys.
  If the intention is to "unset" or "remove" the policy server from the room, setting the content to
  an empty JSON object is sufficient. Alternatively, kicking all users belonging to the policy server
  from the room would also work.

* The `/sign` endpoint as proposed does not support batching. This limits a server's ability to send
  consecutive events quickly, which is currently considered a feature rather than a bug. A future
  MSC may explore a `/sign_many` or similar endpoint which handles checking a small number of events
  for spam. If such a future MSC is written, that MSC should consider what an appropriate value should
  be for "a small number" of events, and whether a single spammy event in the batch causes the whole
  batch to fail. Some use cases include bots which need to send consecutive events, but only want to
  do so if *all* of those events would be sent.

* When the policy server is offline or unreachable, the room is effectively unable to send events.
  Though events not signed by the policy server can be sent to the room, tooling such as moderation
  bots or natural homeserver behaviour might prevent those events from being readable by humans. For
  example, a homeserver might hold the event in purgatory until it can get a response from the policy
  server, or a moderation bot might immediately redact the event for missing a signature.

  Rooms can restore regular communication while a policy server is offline by unsetting the `m.room.policy`
  state event. Such events are explicitly not checked by the policy server to enable this exact
  escape hatch during an outage/problem.

* Homeservers might be confused if the policy server is ACL'd from the room. The `/sign` endpoint is
  not protected by the ACL, but the policy server can't participate in the room itself. In this
  scenario, tooling (possibly including the policy server itself) is encouraged to make the room's
  moderators aware of the situation so they can fix it. This is otherwise "don't do that" territory.

* Communities which don't have access to server hosting infrastructure may not be able to self-host
  a policy server. An example of this is a community which has deployed a moderation bot, but is not
  confident enough or financially able to run a proper Matrix homeserver (or policy server, by extension).

  In such cases, communities are likely also depending on publicly available homeservers for the bulk
  of their moderation and administration. Those communities can aim to find an easy-to-setup policy
  server implementation, or rely on a third party to host it for them. More considerations around
  third party instances are explored in the Safety Considerations below.

* The `m.room.policy` event type is named generically, and conflicts with the existing concept of
  [Moderation Policy Lists](https://spec.matrix.org/v1.17/client-server-api/#moderation-policy-lists).
  This is intentional: policy servers provide a function near to what would be described as "additional
  authorization rules" currently, and are expected to expand into features beyond event authorization
  in the future. For example, a policy server might be responsible for checking all media uploads on
  a homeserver against a media policy. Or, a policy server might provide enhanced requirements on who
  can join a room.

* There is no mechanism for a policy server to change an event's designation reliably. Once an event
  is signed by the policy server, it's signed (effectively) forever. Policy servers might cooperate
  with other moderation tooling to ensure redactions are sent for events they want to change from
  neutral to spammy, but going from spammy to neutral is a challenge.

  A future MSC is best placed to consider a mechanism to communicate designation changes.

* Policy server deployments which do decide to offer the `/.well-known/matrix/policy_server` endpoint
  might find that those deployments are more complex. This can lead to reliability issues as the
  endpoint might get missed in regular website maintenance, for example. This endpoint is exclusively
  used by clients during setup however, so the endpoint can afford some reliability issues.

  [element-meta#3046](https://github.com/element-hq/element-meta/issues/3046) goes into more detail
  on these concerns on a related endpoint.

Further issues are discussed in the Safety Considerations, Security Considerations, and Alternatives
below.

## Safety considerations

* This proposal intentionally makes no attempt to define "unwelcome" or "harmful" content. The precise
  filters or checks performed by a policy server are left as implementation details because they may
  vary from community to community.

* Policy servers are proactive rather than reactive to reduce the chance or ability for a harmful
  event to reach users. Prior to policy servers, communities had extremely limited options for proactive
  tooling, which could result in a harmful event being visible to room members for a moment while the
  reactive tooling caught up. With policy servers, such events get rejected before reactive tooling
  needs to kick in (in the vast majority of cases - see Potential Issues).

* Rooms and communities are not forced to use a policy server, and they may opt to use one during
  particular spam incidents then disable them after. This is critical to the feature design to
  ensure that rooms retain ownership and control over themselves.

  This is especially important when a room decides to (maybe temporarily) use a policy server instance
  which is supplied by a third party. The room is not required to give up control to the third party,
  and can cease using the third party at any time.

* Related to room ownership, rooms intentionally do not need to give any users from the policy server
  a high power level in the room. The room just needs a user to be joined. Some policy server
  implementations may be capable of going a bit above and beyond this MSC's scope by auto-redacting
  spam and similar, which requires higher power levels in most cases, but using that functionality
  should be optional.

* Policy servers are also not forced to participate in a room. They can refuse to join or self-eject
  as they see fit, causing other homeservers to stop checking new events with them. Doing so also
  stops the policy server from being consulted on events sent "during" the policy server's time in
  the room because the other servers in the room will be looking at the current state only.

  Allowing the policy server to shut down cleanly and not be responsible for chunks of the DAG/room
  forever is a feature.

* Further because the current policy server applies to all events regardless of when they were sent,
  policy servers are able to be responsive to shifting regulatory or other environments. For example,
  a community might not have a rule against long messages, but then one day does and wants to apply
  it to past messages too. While the policy server shouldn't be re-checking events it's already
  checked, it's possible that another server in the room has just found a section of DAG that the
  policy server hasn't checked before. The "no long messages" rule could then be applied to those
  events.

  It's left as an implementation detail whether communities can change this behaviour within their
  chosen policy server. Servers will still always ask for an opinion from the policy server, but
  whether the policy server returns a spammy or neutral response is entirely up to it.

## Security considerations

As is the case with most safety tooling, attempts to work around the tooling are often considered
security issues. Policy servers are new tech for Matrix and might have unforeseen or undisclosed
issues/concerns. Readers are encouraged to review the [Security Disclosure Policy](https://matrix.org/security-disclosure-policy/)
ahead of reading this section, as it also applies to MSCs.

This proposal's security considerations are:

* Though rooms are given an escape hatch to unresponsive policy servers, a room's policy server is a
  natural Denial of Service (DoS) target. As already mentioned, policy servers MUST be tolerant to
  DoS attacks. To what scale they need to tolerate is left as a deployment detail. A policy server
  dedicated to a small community may not have the same requirements as a policy server available for
  many communities to use.

* Spammy events can still become visible in the room due to outdated servers or maliciously not checking
  the events against the policy server. This proposal has a number of mechanisms to minimize this
  risk as much as possible, but it's still possible. Those mechanisms include secondary `/sign` requests,
  moderation bot/advanced tooling redactions, and eventually considering those events as spammy.

  As already mentioned, a future MSC is expected to de-risk this completely through a new room version
  which requires relevant signatures on events.

* A homeserver might deliberately ask for signatures from the policy server, but never actually send
  the event to other homeservers. There are not many great options for avoiding this. One of the more
  successful approaches is to monitor clock drift (both positive and negative) on `origin_server_ts`
  and take action against extreme cases.

  This could be implemented by policy servers, moderation bots, and other moderation tooling, though
  is likely best placed in a moderation bot. In short, when the clock drift exceeds a threshold, take
  action against the event/sender. This might be a redaction + kick, or could be a warning to the user
  followed by increased action if it happens again in a short period of time.

  Policy servers which aren't tracking the DAG might find difficulty in doing the same. A call to
  `/sign` might have a sane `origin_server_ts` value, but the event isn't "sent" yet. The server would
  have to wait for the event to be echoed [`/send`](https://spec.matrix.org/v1.17/server-server-api/#put_matrixfederationv1sendtxnid)
  before being able to determine if it was actually sent. A server could refuse to deliver the echo
  though, either maliciously or accidentally with something like Synapse's [`federation_domain_whitelist`](https://element-hq.github.io/synapse/v1.144/usage/configuration/config_documentation.html#federation_domain_whitelist).

  A policy server which does track (and ideally, expose) the DAG for a room can do a little bit more.
  Instead of waiting for an echo, the policy server can consider the call to `/sign` as "sending" the
  event. If there isn't an echo in a reasonable time frame, the policy server could emit its own event
  which references that event via `prev_events`. Other servers in the room will then attempt to pull
  in the sent-but-not-delivered event using normal eventual consistency measures.

  Whether DAG tracking or not, policy servers might also get a redaction sent out for events they
  signed but didn't see echoed back in some time frame. This may require cooperation with something
  that can send redactions, like a moderation bot, if the policy server cannot send events itself.

  In any case, functionality which monitors clock drift MUST be aware that some amount of drift is
  expected. Sometimes, servers legitimately go down and try to re-send all of their events upon network
  being restored, which will have incorrect timestamps.

* As mentioned in the Implementation Considerations section, policy servers SHOULD NOT publish the
  signing key they use in `m.room.policy` state events as "real" keys in `/_matrix/key/v2/server`.
  This keeps separation of concerns between signing keys, and enables rooms to force-rotate/disable
  a policy server on their own without needing to cooperate with the policy server itself.

  If the signing key used in `m.room.policy` is compromised, rooms SHOULD disable their use of a
  policy server by setting the event's `content` to an empty object. Later, when the policy server
  rotates its key, the event SHOULD be re-populated with the updated key instead.

  Events are evaluated against the current policy server rather than the one defined at an event's
  position in the DAG, meaning that spammy events might temporarily be allowed during this rotation.
  Already-signed events might become soft failed due to having the wrong key being used to sign the
  events, however. To limit this case, servers MAY request a new signature from the policy server to
  doubly confirm that the event is in fact meant to be spammy.

  **Note**: Policy servers might rotate their key without the room's knowledge. This will cause events
  to fail signature checks because the key in the room is different from the key used by the policy
  server - this is intentional, and can be an indication that the `m.room.policy` state event needs
  updating.

  **Note**: Keys in `m.room.policy` are rotated/updated in-place, always. The key version of `policy_server`
  is hardcoded for simplicity in checking signatures, and is not used to identify the key itself.

## Alternatives

Some alternatives are implied through the above sections and are excluded for brevity. For example,
"what if we didn't use policy servers?" is answered multiple times above.

* One possible alternative is to have servers `/check` events at time of receipt rather than `/sign` at
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

* The `m.room.policy` state event could support multiple servers being listed instead of exactly one.
  This would allow the room to (theoretically) continue chatting if one of the policy servers went
  offline for whatever reason, though carries some costs:

  1. One of the reasons to consider multiple servers is to ensure a room cannot experience a denial
     of service through DoSing the policy server itself. Listing multiple servers increases how many
     targets are known to an attacker rather than provide meaningful redundancy.

     Most communities would also be able to tolerate a brief interruption and likely would not have
     the resources available to run/deploy multiple servers anyway. Policy servers protecting multiple
     communities, like the Foundation's own instance, are encouraged to consider anti-DDoS measures
     to limit interruptions among their protected communities.

     Further, the `m.room.policy` state event is explicitly *not* checked by a policy server itself,
     allowing communities to remove or replace which server they're using in the event of an outage.

  2. Assuming the setup involves getting a signature from any one of the listed servers rather than
     all servers, the server with the weakest configuration would always win. Communities may find
     it difficult to keep configurations in sync, especially if using different providers or software
     to run those servers.

     Exposing server configuration in the room state so it can be shared across all listed servers
     is not considered a solution as communities would generally prefer to keep precise configuration
     a relative secret (for example, exactly how long of a message is too long). This is aside from
     compatibility issues where one server supports message length filtering but another doesn't.

  3. Assuming that signatures are required from *all* rather than any one listed server, the denial
     of service risk remains: an attacker is only required to bring down a single server rather than
     all of them.

     This setup would fix the weakest link issue though. Communities could use multiple providers to
     gain different capabilities. For example, one provider might do static analysis on events while
     another tries to determine how "on topic" messages are. With a single server setup, that single
     server needs to perform *all* capabilities required by the community. In practice, it's expected
     that policy servers will have the same set of "essential" capabilities, and some may support the
     effect of multiple servers by calling out to downstream servers to get an opinion on an event.

## Unstable prefix

While this proposal is not considered stable, implementations should use the following unstable identifiers:

| Stable | Unstable |
|-|-|
| `/_matrix/policy/v1/sign` | `/_matrix/policy/unstable/org.matrix.msc4284/sign` |
| `/.well-known/matrix/policy_server` | `/.well-known/matrix/org.matrix.msc4284.policy_server` |
| `m.room.policy` | `org.matrix.msc4284.policy` |

**Note**: Due to iteration within this proposal, implementations SHOULD fall back to `/check` (described
below) when `/sign` is unavailable or when `public_key(s)` is not present in the `org.matrix.msc4284.policy`
state event.

**Note**: Also due to iteration within this proposal, unstable implementations using unstable `/sign`
MUST interpret a 200 OK with empty JSON object response as refusal to sign. Errors might not be raised
by the policy server.

**Note**: `org.matrix.msc4284.policy` state events MAY have a `public_key` field rather than `public_keys`.
The `public_key` is a single string denoting the `ed25519:policy_server` key for the server.

## Dependencies

This proposal has a **soft dependency** on the following MSCs. They are not blocking for this MSC's
acceptance.

* [MSC4387: `M_SAFETY` error code](https://github.com/matrix-org/matrix-spec-proposals/pull/4387).

This proposal has no other dependencies.

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

Comments not incorporated into `/check` text:
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2107839742 - Why optional body?
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2051075167 - Require signature check on body?
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2254883244 - Error for when the policy server
  knows it's not protecting that room?
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2089903103 - Warnings system.
* https://github.com/matrix-org/matrix-spec-proposals/pull/4284/files#r2254826194 - Check ACLs?
