# MSCYYYY: Tagged Forwards

Forwarding a message today (e.g. Element's "Forward" action) simply resends the same content as a new
message from the forwarding user, with nothing marking it as a forward at all: a viewer has no way to
tell a forwarded message apart from something the forwarding user actually wrote themselves. Other
chat platforms, Discord's message forwarding being one example, instead show the message with a small
"Forwarded" indication and enough context to see where it came from.

This proposal defines an optional `m.forwarded_from` field on an ordinary message's content, marking it
as a forward of another event and carrying enough information to attribute it, without requiring a
viewer to have access to the room the message was originally sent in.

- A new, optional content field, `m.forwarded_from`, usable on any `m.room.message` (any `msgtype`),
  not a new event type: a forwarded message stays a completely ordinary message to any client that
  doesn't understand this proposal.
- No embedded content copy is needed: forwarding already means sending a copy of the original content
  as this message's own content, so `m.forwarded_from` only needs to carry attribution, not a second
  copy of what's already right there.
- Forwarding a message that is itself already a forward collapses to the original source, rather than
  building a chain, matching how Discord's own forwarding behaves.
- Forwarding without attribution remains available: setting `m.forwarded_from` is a per-forward choice,
  not mandatory, since a user forwarding something may not want to disclose where it came from.

## Proposal

### The `m.forwarded_from` field

A forwarded message is an ordinary `m.room.message` whose content is a copy of the original message's
content, taken at forward time, with an additional `m.forwarded_from` field describing where it came
from. Its fields:

**Mandatory**

- `event_id`: the original message's event ID.
- `room_id`: the room the original message was sent in.
- `sender`: Matrix ID of the original message's author.

**Optional**

- `displayname`: snapshot of the original author's display name at forward time, for nicer default
  rendering. Clients MUST fall back to the bare `sender` Matrix ID when it is absent, the same as
  Matrix already does anywhere else a display name is unset.
- `origin_server_ts`: the original message's own `origin_server_ts`, copied. RECOMMENDED, so a client
  can show something like "3 days ago" for the original send time without needing to resolve the live
  original event first.

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Has anyone seen this? Wild.",
    "m.forwarded_from": {
      "event_id": "$original:example.org",
      "room_id": "!originalroom:example.org",
      "sender": "@bob:example.org",
      "displayname": "Bob",
      "origin_server_ts": 1719000000000
    }
  }
}
```

`sender` is mandatory, and `displayname` is RECOMMENDED, for the same reason embedding attribution is
useful anywhere else in Matrix that a cross-room reference exists: the person viewing a forwarded
message may not share a room with its original author at all, e.g. a message forwarded out of a private
room into a public one. Clients SHOULD still attempt to resolve the live original event (via `event_id`
+ `room_id`) where accessible, for a "view original" action or to detect that it has since been edited
or redacted, but this is a bonus, not a requirement: the forwarded message's own content is already a
complete, renderable copy regardless of whether the original is still reachable.

### Forwarding a forward

Forwarding a message that itself carries `m.forwarded_from` SHOULD set the new message's
`m.forwarded_from` to the same `event_id`/`room_id`/`sender`/`displayname`/`origin_server_ts` as the
message being forwarded, rather than pointing at the immediately-forwarded message itself. This
collapses any chain of re-forwards down to crediting the true original author no matter how many times
something gets forwarded onward, the same way Discord's own forwarding avoids building a visible chain
of "forward of a forward of a forward."

### Rendering

A compliant client rendering a message with `m.forwarded_from` SHOULD show an indication like
"Forwarded from Alice" above the message content, using `sender`/`displayname` the same way any other
attribution in Matrix falls back from a display name to a bare Matrix ID, and MAY make it clickable to
jump to the live original where `event_id`/`room_id` are accessible. A client with no support for this
proposal renders the message exactly as it would any other, since the forwarded content is ordinary
message content; this proposal only adds an optional way to notice and label that.

## Potential issues

- **Only compliant clients show the "Forwarded from" indication.** A message forwarded today, or by a
  client that doesn't implement this proposal, still looks like original content, exactly as it does
  now. This proposal only closes that gap for clients that adopt it; it cannot retroactively add
  attribution to forwards that never included `m.forwarded_from` in the first place.
- **`m.forwarded_from` is self-asserted, unverified metadata.** Nothing ties `event_id`/`room_id`/
  `sender`/`displayname` to the actual content or authorship of the referenced event; a user could claim
  a message was forwarded from a real, innocuous event while the forwarded content itself says something
  entirely different, or attribute content to an author who never sent it. Clients SHOULD verify against
  the live original where accessible, and flag a mismatch (see Security considerations, below).
- **Collapsing a forward-of-a-forward relies on client cooperation, not enforcement.** Nothing stops a
  client from ignoring the collapsing behavior in Forwarding a forward, above, and pointing
  `m.forwarded_from` at the immediately-forwarded message instead of the true original. This proposal
  recommends collapsing for a better user experience, the same way it recommends, but cannot force,
  verifying attribution against the live original.

## Alternatives

- **Model this as an `m.relates_to` relation** (e.g. `rel_type: "m.forward"`), instead of a plain
  content field. Rejected for the same reason [MSC4501](https://github.com/matrix-org/matrix-spec-proposals/pull/4501)
  rejects it for reposts: `m.relates_to`-based relations are resolved by walking the *same room's*
  event graph, so a foreign `room_id` alongside `rel_type` would be silently ignored by that machinery,
  and a forward doesn't need bundled aggregations or thread rollups in the first place.
- **A dedicated event type** (e.g. `m.room.forwarded_message`), instead of a field on ordinary
  `m.room.message`. Rejected: forwarding needs to work for any existing `msgtype` in any ordinary room,
  and a new event type would mean every client's existing message-rendering pipeline would need to
  special-case it. A plain content field means non-compliant clients keep working unchanged, exactly as
  they do today.
- **Also embedding a full copy of the original content inside `m.forwarded_from`**, the way
  [MSC4501](https://github.com/matrix-org/matrix-spec-proposals/pull/4501)'s `m.social.relates_to` embeds
  `content`. Rejected as unnecessary here: forwarding already means the message's own top-level content
  *is* the copy, so a second copy nested inside `m.forwarded_from` would just duplicate it for no
  benefit.
- **Requiring `m.forwarded_from` on every forward, with no anonymous option.** Rejected: a user
  forwarding something may not want to disclose which room or which account it came from, e.g.
  forwarding out of a private room whose existence they'd rather not reveal to the destination room's
  members (see Security considerations, below). Making attribution opt-in per forward preserves today's
  behavior as a fallback.

## Security considerations

- **Forwarding with attribution discloses the source `room_id`.** A compliant client resolving the live
  original, or simply a sufficiently technical viewer reading the raw event, learns the room ID the
  message came from, which may itself be sensitive (its existence, its membership, or just that the
  forwarding user is in it). Clients SHOULD make this clear to a user before they forward with
  attribution, and SHOULD offer the no-attribution fallback (see Alternatives, above) for cases where a
  user wants to share content without disclosing its source.
- **Fabricated or mismatched attribution.** As noted in Potential issues, above, nothing prevents a
  forwarded message's visible content from disagreeing with the real content of the event
  `m.forwarded_from` points at, or crediting an author who never sent it. Clients SHOULD indicate when a
  live original event can no longer be found or has been redacted, and SHOULD verify the claimed
  `sender`/content against the live original where accessible, flagging a mismatch as a fabricated or
  altered forward rather than silently trusting it.
- **No new client-server or server-server API surface, and no new end-to-end encryption concerns.**
  This proposal only defines a new, optional content field; a forwarding client already has to read
  (and, if applicable, decrypt) the original content and re-send it as new content in the destination
  room, exactly as forwarding already works today. `m.forwarded_from` rides along in that same,
  already-re-encrypted-per-destination content object.

## Unstable prefix

Until this proposal is accepted into the spec, implementations should use the following identifier:

| Stable (once accepted) | Unstable (for now)                  |
| ------------------------ | -------------------------------------- |
| `m.forwarded_from`       | `org.matrix.mscYYYY.forwarded_from`    |

## Dependencies

This MSC has no dependencies. It builds entirely on existing, already-stable Matrix mechanisms:
ordinary `m.room.message` events and their existing content schema.
