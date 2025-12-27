# MSC4207: Media identifier moderation policy

Moderation policies are used to refer to entities that
need to be taken down.

No such policy exists for media because of a number of safety,
security, and legal reasons.

A moderation policy that targets media is highly desired,
because there is no current means to share knowledge about
abusive content other than through back-channels.

This is because we must not inadvertently propagate the media
by referring to it directly.

## Proposal

This proposal builds upon both [MSC4205 Hashed policy entities](https://github.com/matrix-org/matrix-spec-proposals/pull/4205)
and [MSC4204 m.takedown recommendation](https://github.com/matrix-org/matrix-spec-proposals/pull/4204).

A new policy type is introduced `m.policy.rule.mxc`.

A policy targeting the media `mxc://example.com/0`
would have the following content:

```json
{
  "hashes": {
    "sha256": "ZDSM130dcJ578ANfiJxoN5Nle2+c5uEkDuHHduxj6AM="
  },
  "recommendation": "m.takedown"
}
```

As described in [MSC4204](https://github.com/matrix-org/matrix-spec-proposals/pull/4204),
a reason may be provided with the `m.takedown` recommendation.
However, in the context of media a reason must not be provided.

This is to prevent the policy being used to classify the media and to
keep the reason for takedown ambiguous.

### Recommendations

#### [MSC4204](https://github.com/matrix-org/matrix-spec-proposals/pull/4204) `m.takedown`

- When applied to a user: Media is automatically purged from
  local storage and is never displayed in the client.

- When applied to a room: Messages containing the media
  uri are automatically redacted.

- When applied to a server: Media matching the mxc uri is immediately
  quarantined or removed.

A reason should never be provided when this recommendation is used.
This is to prevent policy lists being used to classify media
on Matrix in order to deliberately seek a certain classification of
material.

#### `m.ban`

Moderators may wish to use `m.ban` when media is considered offensive,
or the subject of a dispute, but not necessarily worthy of
`m.takedown`.

- When applied to a user: Media is hidden entirely or behind a spoiler
  tag with an explanation.

- When applied to a room: Messages containing the media uri are
  automatically redacted.

- When applied to a server: The media is quarantined.

## Potential issues

### Reactive only

This only provides a reactive means to remove the media once it
has been sent to a room and downloaded on various homeservers.

It can only be proactive in instances where the attacker doesn't
know the media id has been listed yet, or the media simply
hasn't propagated to all target homeservers yet.

### Missing reason

As mentioned in
[MSC4204](https://github.com/matrix-org/matrix-spec-proposals/pull/4204)
in the
[concerns](https://github.com/Gnuxie/matrix-doc/blob/gnuxie/takedown/proposals/4204-takedown-recommendation.md#potential-issues),
the absence reason may make it difficult for moderators to determine
the context behind the policy.  An attempt to document the reason
privately exists through [MSC4206 Moderation policy auditing and
context](https://github.com/matrix-org/matrix-spec-proposals/pull/4206)

## Alternatives

### Content or perceptual hashing

Hashing the content of the media and distributing the media could
be the same as distributing a content address.

Distributing perceptual hashes is also problematic.

See [MSC4113: Image hashes in Policy Lists](https://github.com/matrix-org/matrix-spec-proposals/pull/4113).

## Security considerations

### Dictionary attack

Please see [MSC4205 Hashed policy entities](https://github.com/matrix-org/matrix-spec-proposals/pull/4205), in particular
the note on [dictionary attacks](https://github.com/Gnuxie/matrix-doc/blob/gnuxie/sha256-policy-entity/proposals/4205-sha256-policy-entity.md#dictionary-attack).

## Unstable prefix

`org.matrix.msc4207.mxc` -> `m.policy.rule.mxc`

## Dependencies

This MSC depends upon both:
* [MSC4205 Hashed policy entities](https://github.com/matrix-org/matrix-spec-proposals/pull/4205)
* [MSC4204 m.takedown recommendation](https://github.com/matrix-org/matrix-spec-proposals/pull/4204)
