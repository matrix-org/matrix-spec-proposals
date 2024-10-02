# MSC0000: Media identifier moderation policy

Moderation policies are used to refer to entities that
need to be takendown.

No such policy exists for media because of a number of safety,
security, and legal reasons.

A moderation policy that targets media is highly desired,
because there is no current means to share knowledge about
abusive content other than through backchannels.

This is because we must not inadvertantly propagate the media
by referring to it directly.

## Proposal

This proposal builds upon both [MSC0000 Hashed policy entitites]
and [MSC0000 m.takedown recommendation].

A new policy type is introduced `m.policy.rule.mxc`.

A policy targetting the media `mxc://example.com/0`
would have the following content:

```json
{
  "hashes": {
    "sha256": "ZDSM130dcJ578ANfiJxoN5Nle2+c5uEkDuHHduxj6AM="
  },
  "recommendation": "m.takedown"
}
```

A reason must not be used

### Recommendations

#### MSC0000 `m.takedown`

- When applied to a user: Media is automatically purged from
  local storage and is never displayed in the client.

- When appiled to a room: Messages containing the media
  uri are automatically redacted.

- When applied to a server: Media matching the mxc uri is immediately
  quarantined or removed.

A reason should never be provided when this recommendation is used.
This is to prevent policy lists being used to classify media
on Matrix in order to deliberately seek a certain classification of
material.

#### `m.ban`

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


## Alternatives

### Content or perceptual hashing

Hashing the content of the media and distributing the media could
be the same as distributing a content address.

Distributing perceptual hashes is also problematic.

## Security considerations

### Dictionary attack

Please see [MSC0000 m.takedown].

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

* [MSC0000 `m.takedown`]
* [MSC0000 hashed policy entity]
