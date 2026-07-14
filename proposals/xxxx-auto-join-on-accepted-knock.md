# MSCXXXX: Auto-joining rooms when a knock is accepted

[MSC2403](https://github.com/matrix-org/matrix-spec-proposals/pull/2403) (knocking) deliberately
modelled accepting a knock as an ordinary invite: the knocking user receives an invite, which
their client must then accept by joining. In practice this is a poor experience: the user has
*already* expressed their intent to join the room by knocking, and yet when an admin lets them
in, nothing happens until they notice the invite and accept it by hand — often long after the
conversation they wanted to join has moved on.

This proposal:

1. recommends that servers automatically join their users to rooms when an invite arrives which
   accepts a pending knock;
2. specifies how clients discover *who* accepted the knock, given the invite state may be
   skipped over entirely — which [MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268)
   (sharing room keys for past messages) needs in order to accept the inviter's key bundle;
3. specifies how a multi-device user's clients avoid all simultaneously downloading that key
   bundle, since a server-initiated join (unlike a client-initiated one) happens on all of the
   user's devices at once.

## Proposal

### Auto-joining on accepted knocks

When a homeserver receives an invite for one of its users, and the user has a pending knock in
that room — i.e. the invite event's `auth_events` contain the user's own knock membership event —
the server SHOULD immediately join the user to the room on their behalf, rather than waiting for
a client to accept the invite.

The knock-in-`auth_events` check is the correct signal (rather than, say, checking the user's
current membership is `knock`) because it demonstrates the *inviter* was accepting the knock:
the invite was authorised against the knock, so a stale or racing invite sent independently of
the knock does not qualify.

Since the user's knock already expressed unambiguous intent to join, no additional consent is
needed. Servers MAY allow users or administrators to opt out of this behaviour.

If the join fails (for example because the invite was rescinded in the interim, or the join is
rejected over federation), the invite remains and clients fall back to today's manual-accept
behaviour.

### Identifying the accepter

Because the server joins the user promptly, clients typically observe the membership transition
`knock` → `join` within a single sync, never seeing the intermediate invite. This loses
information clients need — most importantly for [MSC4268], where the invited user's client must
know who invited them in order to accept that user's room key bundle, and for UX (e.g. "Alice
accepted your request to join").

To address this, when a server joins a user to a room itself as the result of an accepted knock,
the join event it creates MUST include the user ID of the sender of the accepted invite in the
`prev_sender` field of the event's `unsigned` data, alongside the existing `prev_content`:

```json
{
  "type": "m.room.member",
  "state_key": "@bob:example.org",
  "sender": "@bob:example.org",
  "content": { "membership": "join" },
  "unsigned": {
    "prev_content": { "membership": "invite" },
    "prev_sender": "@alice:example.org",
    "replaces_state": "$invite_event_id"
  }
}
```

`prev_sender` — the sender of the state event which this event replaced — is an existing
Synapse extension to `unsigned` which clients already rely on in other membership contexts (for
example to attribute an invite when computing direct-message metadata); this proposal makes it
normative for this case.

### Multi-device key bundle claiming

[MSC4268] delivers a room key bundle as an encrypted to-device message to *each* of the invited
user's devices, pointing at an encrypted blob in the media repository. When a join is initiated
by a client, only the joining device downloads and imports the bundle eagerly; the user's other
devices obtain any keys they later need from key backup or the bundle itself, on demand.

A server-initiated join, by contrast, arrives on all of the user's devices in the same instant,
and with it the temptation for every device to download the bundle simultaneously — N downloads
of the same blob, mostly on devices where the user may never even open the room.

To restore the one-eager-downloader behaviour:

* On a server-initiated join, clients SHOULD NOT eagerly download a room key bundle. They SHOULD
  retain the bundle details and import the bundle lazily, when first needed (for instance, when
  the user first views the room, or upon the first undecryptable message), preferring key backup
  if the keys have already appeared there.

* A server which joins a user to a room on their behalf MAY designate one of the user's devices
  as the *bundle claimer* by sending it (and only it) a to-device message of type
  `m.key_bundle_claim` (unstable prefix `org.matrix.mscxxxx.key_bundle_claim`), with the server's
  own user as the sender:

  ```json
  {
    "type": "m.key_bundle_claim",
    "sender": "@bob:example.org",
    "content": {
      "room_id": "!room:example.org"
    }
  }
  ```

  The server SHOULD pick the device it believes the user is most likely to be actively using —
  for example the device with the most recent activity, preferring devices with a sync request
  currently in flight.

* A client receiving `m.key_bundle_claim` for a room with a pending key bundle SHOULD download
  and import the bundle immediately, as it would have done for a client-initiated join. Clients
  MUST ignore `m.key_bundle_claim` messages whose `sender` is not their own user ID (see
  [Security considerations](#security-considerations)).

The hint is purely advisory: it is an optimisation which restores eager behaviour on (usually)
exactly one device. If it is lost, ignored, sent to a dead device, or never sent at all (e.g. by
an older server), every device still converges on the correct keys through the lazy path.

Although this proposal is motivated by accepted knocks, the claiming behaviour is specified in
terms of any *server-initiated join*, so that future mechanisms by which a server joins a user
to a room can reuse it.

## Potential issues

* The device the server picks may be offline or permanently dead; the bundle is then only
  claimed lazily. This is deliberate: the lazy path must exist anyway (the hint is unencrypted
  and unauthenticated beyond the server's word), so the hint being wrong costs only latency on
  devices which were not the user's current focus. Note that in the common interactive case —
  the user is looking at the device from which they knocked — that device lazily imports the
  bundle the moment the user opens the newly-joined room, hint or no hint.

* The bundle media may have been removed by the time a lazy device wants it (media retention);
  such devices fall back to key backup, which the claiming device will have populated.

* Auto-joining changes long-standing default behaviour for accepted knocks. Server implementations
  may prefer to roll this out behind an option (the Synapse implementation is opt-in via
  `auto_accept_invites.enabled_for_accepted_knocks`).

## Alternatives

* **Clients elect a claimer deterministically** (e.g. lowest device ID) with no server
  involvement. Rejected as the primary mechanism: the elected device is not infrequently a
  stale or offline session, and clients cannot observe device liveness; the server can.
  (Deterministic election also survives as an implicit special case: with no hint, the lazy
  path effectively elects "whichever device the user touches first".)

* **Attach the designation to the bundle message itself.** Impossible for the server — the
  MSC4268 bundle pointer is olm-encrypted, so the server cannot tell which to-device messages
  are bundles, and the *inviter* (who writes the per-device payloads) is the one party with no
  visibility into the recipient's device liveness.

* **Per-device `unsigned` annotation on the join event in `/sync`.** Avoids a new event type,
  but event `unsigned` is currently at most per-*user*
  ([MSC4115](https://github.com/matrix-org/matrix-spec-proposals/pull/4115)); making it vary
  per-device cuts against response caching in implementations for little gain.

* **Server-written account data** naming the designated device. There is no precedent for
  server-authored account data, and it leaves per-room state behind which needs cleaning up.

* **Auto-join from the client instead of the server.** A client seeing an invite that accepts
  its own knock could join automatically. But this reintroduces the herd (every online device
  races to join — harmless but noisy), does nothing for users with no client online at accept
  time (the whole point of knocking on a room you're waiting to enter), and misses clients
  which are backgrounded and only receive push.

## Security considerations

* Auto-joining acts on the user's behalf without a fresh confirmation. The knock itself is that
  confirmation: it is an explicit, user-initiated request to join exactly this room. A malicious
  admin can already do nothing more than admit the user to the room they asked to enter.
  (Contrast with auto-accepting general invites, which this proposal does not do.)

* `m.key_bundle_claim` is an unencrypted to-device message. Only the user's own homeserver can
  deliver a to-device message with the user's own ID as `sender` (the client-server API stamps
  the sender, and over federation a server can only send for its own users), and clients MUST
  check the sender is their own user ID. A malicious homeserver can therefore forge or withhold
  hints — but the homeserver already controls to-device delivery wholesale, and the hint only
  influences *which* device downloads a bundle it was already sent. The worst a forged hint
  achieves is a redundant download; a withheld hint degrades to lazy claiming.

* `prev_sender` is server-asserted (it lives in `unsigned`). A malicious homeserver could name
  the wrong accepter, causing the client to accept (or fail to find) a key bundle from that
  user. MSC4268's own protections apply unchanged: bundles are only accepted from the room
  member the client believes invited them, over authenticated media, with the sender's identity
  checked at import.

## Unstable prefix

Until this proposal is accepted:

| Stable identifier | Unstable identifier |
|---|---|
| `m.key_bundle_claim` | `org.matrix.mscxxxx.key_bundle_claim` |

`prev_sender` is already emitted by Synapse without a prefix; this proposal specs the existing
behaviour rather than renaming it.

## Dependencies

This MSC builds on [MSC2403] (knocking) and [MSC4268] (sharing room keys for past messages),
both merged.
