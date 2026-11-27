# MSCXXXX: Sharing room history on server-initiated joins

[MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268) is now part of the spec
(see [Sharing keys between users](https://spec.matrix.org/v1.19/client-server-api/#sharing-keys-between-users)).
It lets a user who joins an encrypted room read messages sent before the join, as long as the
room's `m.room.history_visibility` was `shared` or `world_readable` when those messages were sent.

The mechanism is driven by the **inviter's client, at invite time**. When Alice invites Bob,
Alice's client does the following before it sends the invite:

1. It builds a bundle of the room keys whose Megolm sessions are marked `shared_history: true`.
2. It uploads the bundle as an encrypted attachment.
3. It sends an Olm-encrypted `m.room_key_bundle` to-device message to each of Bob's devices that
   is correctly signed by Bob's cross-signing keys. The message carries the attachment's location
   and key.

Bob's homeserver queues the to-device message until Bob's devices sync. Bob's client stores the
bundle details when they arrive. It downloads and imports the bundle **only if it has recently
accepted an invite from Alice** to that room. The spec recommends 24 hours as the limit. The rule
protects Bob from being made to download, and trust, key material sent by arbitrary users.

As a result, **Alice does not need to be online when Bob joins or reads the history**. Everything
Bob needs is already in his to-device inbox and in the media repository. This proposal keeps that
behaviour: **the inviter, and only the inviter, prepares the bundle, at invite time**.

The design assumes that the invitee's client performs the join. Increasingly, the server performs
it instead:

* **Auto-accepted invites.** Servers can accept invites on the user's behalf, for example with
  Synapse's `auto_accept_invites`.
* **Accepted knocks.** Servers can join a knocking user automatically once a moderator accepts the
  knock by inviting them. The moderator is the inviter, and the moderator's client sends the
  bundle together with the invite.

In both cases the bundle is sent as usual. However, the invitee's membership goes from `invite`
(or `knock`) to `join` without any action by the invitee's client. This causes three problems:

* The client may first see the room as already joined, with no invite state.
* The invite may never appear in a sync response. This happens when it is coalesced into the join
  within a single sync, when the sync is limited, or with sliding sync.
* The bundle can arrive before or after the client learns about the room.

The client never "accepted an invite", so a client that follows the spec **refuses the bundle**,
and the user sees "You don't have access to this message" for history they are entitled to.

This proposal amends the MSC4268 acceptance rule so that **every** server-initiated join that
replaces an invite gets the inviter's bundle. The inviter is identified **only from signed room
events**, and no new server behaviour is needed.

## Proposal

### Definitions

* A **server-initiated join** is a transition of the user's own `m.room.member` event to `join`
  that none of the user's clients performed, and that replaces an `invite`. Typical sources are
  auto-accepted invites and the automatic join of an accepted knock. A join performed by another
  of the user's own devices looks the same to this client, and is treated the same way.
* The **inviter** of such a join is the `sender` of the user's own `invite` membership event that
  the join replaced.

### Only the inviter shares

The sending side is unchanged from MSC4268. The inviter's client builds, uploads and sends the
bundle **when it sends the invite**, whether or not it expects the invitee's server to accept the
invite automatically. No other member is expected to share history with the joiner. No member
needs to be online after the invite has been sent.

A client that accepts a knock by inviting the knocker is inviting in the MSC4268 sense. It MUST
share history exactly as for any other invite.

### Detecting a server-initiated join

A client detects a server-initiated join when a sync response moves a room to the joined state
and the client did not request that join itself. This covers three situations:

* the room was previously **invited** or **knocked**;
* the room was **left** or **unknown**, and the user's join event in the response has
  `unsigned.prev_content.membership` equal to `invite`, or the response contains the user's own
  `invite` event. `unsigned.prev_content` is already part of the spec.
* the room was **unknown** to the client, for example on the first sync after the server joined
  the user. In this case the client SHOULD additionally require the join event to be recent (for
  example, an `origin_server_ts` less than 24 hours old). An initial sync of an existing account
  would otherwise treat every old join as a candidate.

### Identifying the inviter

The client takes the inviter from the user's own `invite` membership event, which is a signed
room event. It uses the first of the following sources that is available:

1. The invite the client **stored** when it saw the room in the invited state.
2. The user's own `invite` event, if it is **part of the same sync response**, for example in the
   timeline.
3. Otherwise, the room **history**. The client paginates backwards through `m.room.member` events
   with `GET /rooms/{roomId}/messages`, using a filter on `types: ["m.room.member"]`. It looks at
   the user's own membership events, newest first:
   * a `join` is skipped: it is the current join, or a profile change made while joined;
   * the first `invite` found gives the inviter;
   * any other membership found before an `invite` means that the join did not replace an invite.

   The client SHOULD bound this lookup, for example to a few pages.

The user's own membership events are always visible to them, so the lookup works in every room
where history sharing applies. If the client cannot find the inviter, it does not treat the join
as an invite acceptance, and it imports no bundle.

The client MUST NOT use unsigned, server-asserted fields such as `unsigned.prev_sender` to identify
the inviter.

### Accepting the bundle

The MSC4268 rule "*if Bob has recently accepted an invite to the room from Alice*" is extended. A
client MUST treat a server-initiated join whose inviter is Alice as Bob having accepted an invite
from Alice.

The time of acceptance is **when the client observes the join**, not the event's
`origin_server_ts`. The usual window (RECOMMENDED: 24 hours) runs from that moment.

All other MSC4268 rules still apply:

* bundles are only accepted from the inviter;
* only keys for that room are imported;
* the forwarder is recorded and shown.

### Bundles received before the join

A client can receive the inviter's `m.room_key_bundle` before it observes the join, even before
it knows about the room. In that case the client MUST store the bundle details, as MSC4268 already
requires. It MUST NOT discard them because the room is unknown or not joined.

When the client later observes a server-initiated join and identifies the same inviter, it MUST
import the stored bundle. It MUST NOT wait for a new bundle. It SHOULD keep the pending state
across restarts, so that an interrupted import is resumed.

### When to download

Once the inviter has been identified, the client SHOULD download and import the bundle **as soon
as it observes the join**, as it would after accepting an invite itself. A client MAY instead
defer the download until the history is needed, for example when the user opens the room or when
it hits an undecryptable event that predates the join. A client that defers MUST still import the
bundle before the acceptance window ends.

A device that imported the bundle SHOULD back up the imported keys to the user's key backup, if
one is enabled. The user's other devices can then obtain the keys from the backup.

## Potential issues

* **Every device downloads the bundle.** A server-initiated join is visible to all of the user's
  devices at once, and each of them imports the bundle. This is the same cost as MSC4268 when
  each device accepts an invite itself. Clients that care about bandwidth can use the optional
  deferral described above.
* **Extra request to find the inviter.** When the invite is not in the sync response, the client
  makes a few `/messages` requests per server-initiated join. This only happens for recent joins
  that replace an invite.
* **The inviter could not share.** The inviter's client may lack the keys, or may not support
  MSC4268. It may also find that the invitee had no devices signed by their cross-signing keys at
  invite time. In these cases the joiner gets no history. This is a deliberate trade-off: no other
  member shares, and nobody is asked later.
* **Devices created after the invite.** Only the devices that existed at invite time receive the
  bundle. A later device gets the keys only through key backup.
* **Media expiry.** If the bundle media expires before the client downloads it, the client falls
  back to key backup. Importing promptly, which is the default above, keeps this window short.

## Alternatives

* **A server-provided inviter (`unsigned.prev_sender`).** Some servers add the previous sender of
  a state event to `unsigned`, which would save the history lookup. The field is not in the spec,
  and the server asserts it without any signature. The signed `invite` event gives the same
  information without trusting the server, so this proposal does not rely on `prev_sender`.
* **A server hint designating one device to download (`m.key_bundle_claim`).** This would avoid
  every device downloading the bundle. However, it needs new server behaviour, and it fails if the
  chosen device is offline or gone. It also makes the bundle import depend on a message that may
  never arrive. Downloading on every device is simpler and always works.
* **Requesting a bundle from members after the join.** This would require someone to be online
  when the joiner needs the history. It would also make members other than the inviter share
  history. Both conflict with the behaviour this proposal keeps.
* **Per-session key requests (`m.room_key_request`) with `shared_history`.** This was the approach
  of [MSC3061](https://github.com/matrix-org/matrix-spec-proposals/pull/3061), which was reverted
  after a security disclosure.
* **Accepting bundles from anyone after a server-initiated join.** This would defeat the protection
  that MSC4268 gives against forced downloads and key-store poisoning.

## Security considerations

* **The trust model is unchanged.** Bundles are still prepared only by the inviter, only for
  devices correctly signed by the invitee's cross-signing keys, and only from sessions marked
  `shared_history: true`. The inviter chose to add the joiner by sending the invite, as in
  MSC4268.
* **The inviter comes from signed events.** The client identifies the inviter only from the
  user's own `invite` event, which is part of the room DAG, and never from unsigned data. A
  malicious server could only make the client accept a bundle that the named user really sent to
  it for that room.
* **Consent to join.** When a server auto-accepts invites, the user did not consent to each join.
  Any user able to invite them can therefore make them accept a bundle for that room. Three
  things bound the impact: the 24-hour window, the restriction of imported keys to that room, and
  the attribution of the imported keys. A server that auto-accepts invites from untrusted users
  already exposes its users to unwanted rooms, so this proposal adds no new kind of exposure.
* **History lookup.** The `/messages` lookup only reads the user's own membership events. It
  reveals nothing to the server that the server does not already know.
* **Attribution.** Keys imported from the bundle are attributed to the inviter, as in MSC4268.
  Clients must not show them as authenticated by the original sender.

## Unstable prefix

This proposal introduces no new event types, fields or endpoints. It relies only on `m.room_key_bundle`
and `shared_history` from MSC4268, `unsigned.prev_content`, and `GET /rooms/{roomId}/messages`, all
of which are already in the spec.

## Dependencies

* [MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268), sharing room keys for
  past messages: accepted and merged into the spec.
* [MSC4147](https://github.com/matrix-org/matrix-spec-proposals/pull/4147), `sender_device_keys` in
  Olm payloads: accepted.
