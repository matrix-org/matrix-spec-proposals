# MSC4498: Holding messages pending moderation (via policy servers)

[Policy servers](https://spec.matrix.org/v1.18/client-server-api/#policy-servers) are optional safety
tooling that rooms can use to add additional protection. Because these servers operate at a lower
level in the Matrix stack than traditional bots, they can enable previously-unsupported (or difficult
to support) functionality. One example is holding messages pending moderation.

There are a number of different design considerations for holding messages pending moderation. This
proposal focuses on a model where the messages are *not* delivered to anyone but the sender until a
moderator has approved it to be sent. Other operating modes include delivering the message to everyone,
but minimizing it so the reader must take action to see it. [MSC3531](https://github.com/matrix-org/matrix-spec-proposals/pull/3531)
and [MSC4179](https://github.com/matrix-org/matrix-spec-proposals/pull/4179) operate in that space,
largely to react to messages already sent. This proposal does not compete with or hinder those other
proposals/operating modes.

Without policy servers, holding a message *and* not delivering it would not be feasible. Policy servers
add the necessary infrastructure to have an event be checked by someone/thing external to the room
before it is added to the room.

Like other functionality using policy servers, this proposal works best in a [MSC4416](https://github.com/matrix-org/matrix-spec-proposals/pull/4416)
world, but is not dependent on MSC4416. Some fallback advice is provided in this proposal for rooms
which don't support MSC4416.


## Proposal

The [`POST /sign`](https://spec.matrix.org/v1.18/server-server-api/#post_matrixpolicyv1sign) endpoint
provided by policy servers is extended to also return a new `M_HELD` error code with HTTP status code
[`202`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/202). (`200` is already
used to return a signature, `202` is "Accepted; non-committal".)

Where a request to `/sign` is caused by a Client-Server API request, the `M_HELD` error code and `202`
status code are proxied to the client too. This affects *all* event-sending endpoints in the Client-Server
API.

Homeservers which receive `M_HELD` from the policy server SHOULD deliver the relevant event down the
sender's sync stream with a flag in `unsigned` to allow clients to show the event as "not yet fully
sent" (if desired):

```jsonc
{
  "unsigned": {
    "hold": {
      "state": "pending" // or "accepted" or "rejected" (see rest of MSC)
    }
  },
  // other event fields here
}
```

How the policy server acquires approval (or rejection) is left as an implementation detail. A policy
server might hold a message for extended checks, or for human review, or both. If the policy server
receives approval, it federates/fans out the event to the room itself (with appropriate policy server
signature), including to the sender's server. When the sender's server sees the event echoed in this
way, it un-holds the event and updates `unsigned.hold.state` to be `accepted` for the original sending
user's sync stream. This means the sender's client will see the event twice: once when held, and
again once accepted.

**TODO**: During implementation, verify that clients are "happy" to receive events twice in their
sync streams.

If the policy server ultimately rejects the event, it sends a [to-device](https://spec.matrix.org/v1.18/client-server-api/#send-to-device-messaging)
message to *all* of the sender's devices:

```jsonc
{
  "type": "m.event_rejected",
  "content": {
    "room_id": "!wherever",
    "event_id": "$whatever",
    "reason": { // this is a standard Matrix error contained in a field
      "errcode": "M_FORBIDDEN",
      "error": "This message contains probable spam"
    },
    "signature": {
      "policy.example.org": {
        "ed25519:policy_server": "<unpadded base64 signature>"
      }
    }
  }
}
```

As implied, the to-device message `content` is signed by the policy server using the room's advertised
policy server signing key. This is to allow clients to verify the authenticity of the message before
showing errors to the user. Unverified messages SHOULD be ignored by the client. All fields of `content`
are required.

Though `event_id` should be plenty of information for the client, we provide a `room_id` to help clients
find the appropriate event and room a bit faster. If the event belongs to a different room ID than
the one given, the client SHOULD ignore the to-device message.

Assuming the to-device message is verified and not ignored by the client, the client renders the event
as a send failure. Leveraging existing UI for the send failure is encouraged.

**Note**: After an event is accepted or rejected, the server is not required to track the event anymore.
The event is only "tracked" in the sync stream when held or accepted, though a server MAY watch for
rejection and send that down the sync stream too. The server never needs to remember where in the sync
stream a (previously) held event resides - if a client re-initial-syncs or backpaginates over a previously
synced section, for example, then the server MAY NOT return the held event, regardless of whether it's
pending, accepted, or rejected. The intention behind this is to allow a server to fit a "fire and forget"
model rather than a heavily state-tracked model. The only exception is the server needs to be aware
of an event being "accepted" by the policy server.

**TODO**: During implementation, try to leverage the to-device method for acceptance too and see how
it fits. It probably works, but we need to deliver the event to the origin's other users too, so the
origin will be receiving the event in duplicate anyway.


### Fallback/non-compliance

Because most rooms today don't have [MSC4416](https://github.com/matrix-org/matrix-spec-proposals/pull/4416)
support, servers can "bypass" the policy server by sending events to the room without talking to the
policy server. Such events are already left as an implementation detail to handle under the spec. One
possible outcome is the policy server redacting/refusing to sign the event due to bypass.

If an event is held by the policy server but the server sends it to the room anyway, the policy server
MAY refuse to sign the event as an immediate rejection. The policy server MAY also return `202 M_HELD`,
though the requesting server might not see rejections. If a server receives `202 M_HELD` for an event
it didn't send, it SHOULD discard that event rather than soft fail, reject, or accept the event.

Policy servers can detect if/when a server sends an event anyway despite being held by comparing the
event's origin with the `/sign` request's origin. If the server calling `/sign` is different from the
event `sender`, the event's origin server has sent the event anyway. Depending on implementation, the
event's origin server might also federate/fan out the event to the policy server normally via `/send`.
If that happens, the event's origin server most likely is experiencing a bug rather than trying to be
malicious, though the policy server might not make that distinction when deciding how to handle the
event being sent without explicit approval.


## Potential issues

* Clients receive events twice in some cases, which might cause them to explode and/or cause disruption
  in the timeline. Note that this isn't the same as receiving the same *content* twice: the client
  receives the same *event ID* twice. **This needs testing via implementation.**

* Servers are asked to track held events so they can inform clients when they become un-held, but they
  also need to track the event as extremities. Servers SHOULD NOT use held events as `prev_events`
  until the event is explicitly accepted to avoid policy servers also holding all events in the chain.

  If the policy server doesn't hold all events in the chain then other servers might reject future
  events from the origin server because they can't meaningfully find/fetch the held event.

  Note that because of how policy servers detect an event being "sent anyway", if an origin *does*
  serve a held event to another server for the purposes of `prev_events` validation, then that other
  server *might* (*SHOULD*) ask the policy server to sign it because it will not yet have the policy
  server's signature. This can cause the policy server to immediately reject the event or cause the
  other server to discard/drop it, potentially causing other events in the chain to also fail.

  TLDR: Servers can avoid a world of pain by tracking which events of theirs are held, or at least
  making sure to not use held events as `prev_events`. One way to accomplish this might be to not
  persist their own held events and instead wait for the echo from the policy server to re-validate
  its own signature, confirming that it did indeed send the event originally. A server can know it's
  receiving an echo from a policy server by looking up the room's `m.room.policy` state event and
  comparing the `via` server name.

* Messages held by this mechanic are not shown to other users in the room, including moderators. This
  might not be desirable to the room's community. Other proposals like [MSC3531](https://github.com/matrix-org/matrix-spec-proposals/pull/3531)
  and [MSC4179](https://github.com/matrix-org/matrix-spec-proposals/pull/4179) are reactionary and
  might serve that community better.

* Messages held by this mechanic also "hold" their spot in the DAG. Events can't have their DAG positions
  changed due to their signatures and hashes, so it's possible for a sender to have a message held
  then become banned before their message is approved. That may cause their message to be soft-failed
  despite acceptance due to being sent "after" they were banned.

  This can also cause DAG weirdness if the event is accepted after a series of other events. Because
  it'll be received as an extremity, other servers might try to "heal" the DAG by referencing the
  old event as a `prev_event`. This is normal behaviour for rooms for gaps a few events wide, but
  larger gaps are less common.

* Depending on the message content, sending events with a delay might cause confusion in the conversation
  flow. Though the original event's timestamp will be preserved, past discussions in Matrix rooms have
  shown that even a delay of 10 or 15 seconds is enough to create social confusion. For example, a
  user says "sunsets are better than sunrises" and someone else replies "no, sunrises are better". If
  there was a delay in sending a third user's "I agree" message, they could be agreeing that sunrises
  are better when they meant to agree that sunsets are better. Users don't always notice that the
  timestamps are different in these cases, especially when the delay is within the same clock minute.

  This effect is amplified if the conversation has moved on to another topic, even if the delayed
  message is more comprehensive than "I agree". Seeing a message about sunrises/sunsets when the
  conversation is now about operating systems is jarring.

  How and when to use message holding is ultimately a decision for the community, though this proposal
  recommends that events be rejected if they wouldn't make sense in the current conversation context.


## Alternatives

**TODO**: Complete this section after implementation. Writing code for this feature is expected to
establish alternatives, including opinions about whether this is even a good idea.


## Security considerations

**TODO**: Complete this section after implementation for the same reasons as the Alternatives above.


## Unstable prefix

While this proposal is not considered stable, implementations MUST only return `202` status codes if
the request also contains `?msc4498=true` in the query string. This applies to all endpoints affected
by this proposal.

**Note**: We probably want to bump the endpoint version of everything involved depending on how the
implementation effort goes. If things start breaking down when they receive unsolicited `202` status
codes, then a new endpoint version is required. Otherwise we can probably get away with just adding
the status code to the existing endpoint versions. **This needs testing.**

While this proposal is not considered stable, the following identifier changes also take effect:

* `M_HELD` becomes `ORG.MATRIX.MSC4498_HELD`
* `held` under `unsigned` becomes `org.matrix.msc4498.held`
* `m.event_rejected` becomes `org.matrix.msc4498.event_rejected`

Early implementation authors reading this should note that the proposal is subject to change and
therefore their implementation(s) might also need changing. Early unstable implementation is still
encouraged though to explore this proposal's feasibility and usability, and to address the various
"needs testing" comments throughout the proposal.


## Dependencies

This proposal has no direct dependencies.
