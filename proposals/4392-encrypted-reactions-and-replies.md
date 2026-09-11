# MSC4392: Encrypted reactions and replies

Matrix supports end-to-end encryption, which covers message content, but not
various pieces of metadata. Pieces of information not covered by encryption
include reply metadata as well as everything about reactions.

The original MSC for reactions included aggregations, but it was [removed in the
final draft](https://github.com/matrix-org/matrix-spec-proposals/commit/749198fd4a9efa4dc8eb0565ad05746ffa70aa7f)
as it turned out that the server-side behavior was completely broken and no
clients used it. Since nobody has taken the time to fix it, it's clear that
reactions work well enough without server-side aggregations.

Server-side aggregations could still be added for unencrypted rooms even after
reactions are encrypted in encrypted rooms. It's more likely for aggregations to
be useful in high-traffic rooms, and encrypted rooms are less likely to have
high traffic.

Replies have never been covered under aggregations and were only unencrypted as
a future-proofing mechanism. Similar to reactions, there has been no indication
that anyone needs server-side aggregations for replies, and therefore there is
no reason to keep them unencrypted.

When this document talks about the "unencrypted payload", it is referring to the
cleartext/wire content that the homeserver sees. The "encrypted payload" is the
content that was encrypted, which the homeserver can't see.

## Proposal
Clients SHOULD include the entire `m.relates_to` object in the encrypted payload
of all events that include it.

### Encrypted replies
The `m.in_reply_to` and `is_falling_back` fields of `m.relates_to` SHOULD NOT be
copied to the unencrypted payload when sending replies in encrypted rooms. If
both payloads include either of the fields, clients SHOULD prefer the encrypted
one.

For non-threaded messages where `m.in_reply_to` is the only field, the
`m.relates_to` field SHOULD be omitted from the unencrypted payload entirely.

For thread messages, the rest of the `m.relates_to` object (i.e. `rel_type` and
`event_id`) MUST still be present in the unencrypted payload.

### Encrypted reactions
Clients SHOULD encrypt `m.reaction` events in encrypted rooms. The unencrypted
payload SHOULD NOT include `m.relates_to` at all. If both payloads in a reaction
event include the `m.relates_to` object, clients SHOULD prefer the encrypted one.

## Potential issues

### Backwards compatibility
Some old clients will likely be confused by encrypted replies and reactions.

At least for replies, a migration period is recommended where clients initially
send the entire `m.relates_to` object in both the encrypted and unencrypted
payloads, and eventually start stripping the unencrypted copy when a sufficient
level of support for the encrypted reply metadata has been reached.

Reactions could use a similar migration period, but it is uncertain whether
current clients will accept encrypted `m.reaction` events at all.

### Push notifications
The proposed reaction format is indistinguishable from normal encrypted messages,
which means servers would have to send wakeup pushes to mobile clients for all
of them. This could be remediated with a separate flag in the unencrypted payload
that indicates it should not trigger a push, e.g. `"m.priority": "low"`.
[MSC3996](https://github.com/matrix-org/matrix-spec-proposals/pull/3996) has
explored a similar problem for encrypted mentions-only rooms.

## Alternatives
Some sort of breaking change is required to fix metadata leakage. It could be
done as a part of a bigger breaking change, such as switching to extensible
events and/or MLS.

## Security considerations
This MSC is fixing various privacy issues that exist currently.
It should not create any new security or privacy issues.

## Unstable prefix
Not applicable, this MSC is only moving things between the unencrypted and
encrypted payloads, no new names are being introduced.

## Dependencies
None.
