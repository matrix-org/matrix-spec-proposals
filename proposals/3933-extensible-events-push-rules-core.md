# MSC3933: Core push rules for Extensible Events

[MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767) covers a system for extending
events with alternative representations for maximally compatible content in Matrix, however does not
declare the exact push rules needed to replace the existing `m.room.message`-based ones. This proposal
defines those push rules.

Only push rules for the following MSCs are considered - other MSCs, including possible future ones, are
expected to cover any other push rules needed for the extensible events system.

* [MSC1767 - Text and Encryption](https://github.com/matrix-org/matrix-doc/pull/1767)
* [MSC3551 - Files](https://github.com/matrix-org/matrix-doc/pull/3551)
* [MSC3552 - Images and Stickers](https://github.com/matrix-org/matrix-doc/pull/3552)
* [MSC3553 - Videos](https://github.com/matrix-org/matrix-doc/pull/3553)
* [MSC3927 - Audio](https://github.com/matrix-org/matrix-doc/pull/3927)

## Proposal

[MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767) already specifies that an
`event_match` condition of `content.body` actually inspects `m.markup`, and as such, we use that
functionality in this proposal.

[A number of underride rules](https://spec.matrix.org/v1.4/client-server-api/#default-underride-rules)
already exist to cover `m.room.encrypted` and `m.room.message` events, and with these events being
split into several other event types it is important to maintain the same notification state for users
participating in extensible event-capable room versions.

Using [MSC3931](https://github.com/matrix-org/matrix-spec-proposals/pull/3931) and
[MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932), we define the following
additional underride push rules for users:

**One-to-one (DM) rules**
```json5
{
  // Inspired by `.m.rule.encrypted_room_one_to_one`
  "rule_id": ".m.rule.extensible.encrypted_room_one_to_one", // note the `.extensible` part
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "room_member_count", "is": "2" },
    { "kind": "event_match", "key": "type", "pattern": "m.encrypted" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": [
    "notify",
    { "set_tweak": "sound", "value": "default" }
  ]
}
```
```json5
{
  // Inspired by `.m.rule.room_one_to_one`
  "rule_id": ".m.rule.extensible.message.room_one_to_one", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "room_member_count", "is": "2" },
    { "kind": "event_match", "key": "type", "pattern": "m.message" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": [
    "notify",
    { "set_tweak": "sound", "value": "default" }
  ]
}
```
```json5
{
  // Inspired by `.m.rule.room_one_to_one`
  "rule_id": ".m.rule.extensible.file.room_one_to_one", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "room_member_count", "is": "2" },
    { "kind": "event_match", "key": "type", "pattern": "m.file" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": [
    "notify",
    { "set_tweak": "sound", "value": "default" }
  ]
}
```
```json5
{
  // Inspired by `.m.rule.room_one_to_one`
  "rule_id": ".m.rule.extensible.image.room_one_to_one", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "room_member_count", "is": "2" },
    { "kind": "event_match", "key": "type", "pattern": "m.image" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": [
    "notify",
    { "set_tweak": "sound", "value": "default" }
  ]
}
```
```json5
{
  // Inspired by `.m.rule.room_one_to_one`
  "rule_id": ".m.rule.extensible.video.room_one_to_one", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "room_member_count", "is": "2" },
    { "kind": "event_match", "key": "type", "pattern": "m.video" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": [
    "notify",
    { "set_tweak": "sound", "value": "default" }
  ]
}
```
```json5
{
  // Inspired by `.m.rule.room_one_to_one`
  "rule_id": ".m.rule.extensible.audio.room_one_to_one", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "room_member_count", "is": "2" },
    { "kind": "event_match", "key": "type", "pattern": "m.audio" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": [
    "notify",
    { "set_tweak": "sound", "value": "default" }
  ]
}
```

**Non-DM rules**
```json5
{
  // Inspired by `.m.rule.encrypted`
  "rule_id": ".m.rule.extensible.encrypted", // note the `.extensible` part
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "event_match", "key": "type", "pattern": "m.encrypted" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": ["notify"]
}
```
```json5
{
  // Inspired by `.m.rule.message`
  "rule_id": ".m.rule.extensible.message", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "event_match", "key": "type", "pattern": "m.message" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": ["notify"]
}
```
```json5
{
  // Inspired by `.m.rule.message`
  "rule_id": ".m.rule.extensible.file", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "event_match", "key": "type", "pattern": "m.file" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": ["notify"]
}
```
```json5
{
  // Inspired by `.m.rule.message`
  "rule_id": ".m.rule.extensible.image", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "event_match", "key": "type", "pattern": "m.image" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": ["notify"]
}
```
```json5
{
  // Inspired by `.m.rule.message`
  "rule_id": ".m.rule.extensible.video", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "event_match", "key": "type", "pattern": "m.video" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": ["notify"]
}
```
```json5
{
  // Inspired by `.m.rule.message`
  "rule_id": ".m.rule.extensible.audio", // note the `.extensible` part & event type reference
  "default": true,
  "enabled": true,
  "conditions": [
    { "kind": "event_match", "key": "type", "pattern": "m.audio" }, // new event type
    { "kind": "room_version_supports", "feature": "m.extensible_events" } // new condition
  ],
  "actions": ["notify"]
}
```

For clarity, clients are not required to represent each of these rules as individual toggles: they
can (and likely should) represent them all behind a single flag for better understanding for users.

This MSC does not currently replace some other push rules, such as `.m.rule.call`, despite them
being impacted by Extensible Events - these are largely left for a future MSC.

## Potential issues

These rules are extremely verbose and relatively mechanical in nature, and further do not solve the
problem where a client might decide to render an unknown event like an image while not counting it
as a notification - while regrettable, this proposal defers a more sophisticated system to a later
MSC.

## Alternatives

More sophisticated approaches are likely possible. These are deferred to other MSCs - this proposal
aims to fill a gap as quickly as possible.

## Security considerations

No new security considerations as this simply takes existing rules and splits them down for extensible
events. However, server implementations may wish to relax rate limits on some push rule endpoints, like
[`PUT /enabled`](https://spec.matrix.org/v1.4/client-server-api/#put_matrixclientv3pushrulesscopekindruleidenabled)
and others used by clients to enable/alter push rules for bulk operations. An alternative to relaxing
rate limiting is to use [MSC3934](https://github.com/matrix-org/matrix-spec-proposals/pull/3934) or
similar instead.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc3933.*` in place
of `m.*`, noting that the event types themselves in the conditions might use a different unstable prefix.
