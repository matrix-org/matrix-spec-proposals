# MSC4527: State event power levels

Many communities on Matrix choose to enforce a strict [`m.room.power_levels`] that restricts members from sending
unknown or future event types by setting `events_default` > `users_default` and setting specific `events` overrides
for event types they desire to allow (e.g. `m.reaction` and `m.room.message`).

When a room's power levels are configured in this way, the value in `events` overrides `state_default`, hence an
unprivileged user can send a permitted event type as a state event. This allows that event to become part of room state
permanently, which is behavior often undesirable in large public rooms as it increases room complexity.

This proposal introduces a separate map for controlling the power levels required to send state events separately from
message events, alongside the required changes to [auth rules] and the [redaction algorithm].

**Note:** At the time of writing, [Room Version 12] is the latest room version available. This proposal uses v12 as a
base room version for ease of reference, but the concepts/changes can apply to future room versions as well.

## Problem

Given this power levels event:
```json
{
    "events": {
        "m.room.message": 0
    },
    "events_default": 1,
    "state_default": 50,
    "users_default": 0
}
```

An unprivileged user can legally send the following event:

```jsonc
{
    "type": "m.room.message",
    "state_key": "test",
    "content": {
        "body": "Hello, room state!",
        "msgtype": "m.text" // required by `m.room.message`
    }
}
```

## Proposal

This proposal makes breaking changes to the event authorization rules, and therefore requires a new room version.

### Changes to the `m.room.power_levels` schema

A new key `state` is added to the [`m.room.power_levels`] event, of type `{string: integer}`. Identically to `events`,
the `state` key consists of a mapping from event type to power level required.

If the field is missing, or the room has no `m.room.power_levels` event, the value of `state` is assumed to be `{}`.

Example `m.room.power_levels` event:

```jsonc
{
    "events": {
        "m.room.message": 0,
        "m.reaction": 0,
        "m.sticker": 0
    },
    "events_default": 1,
    "state": { // Added by this proposal
        "m.room.avatar": 50,
        "m.room.canonical_alias": 50,
        "m.room.encryption": 100,
        "m.room.history_visibility": 100,
        "m.room.name": 50,
        "m.room.power_levels": 100,
        "m.room.server_acl": 100,
        "m.room.tombstone": 150
    },
    "state_default": 50,
    "historical": 100,
    "invite": 0,
    "kick": 50,
    "ban": 50,
    "redact": 50,
    "users": {},
    "users_default": 0
}
```

### Required power level

An event is considered a _state event_ if the `state_key` property is present.

The *required power level* to send an event, with the exception of membership events and redactions, is as follows:
1. **If the event is a _state event_:**
    1. If the event type is specified in `state`, the user must have at least the level specified to send that event.
    2. If the event type is not specified, the user must have at least the `state_default` power level to send that event.
2. If the event type is specified in `events`, the user must have at least the level specified to send that event.
3. If the event type is not specified, the user must have at least the `events_default` power level to send that event.

The required power level for redactions and membership events remains unchanged from the current specification.

### Auth rules

Step 8 of the [event authorisation rules][auth rules] is updated to use the above definition of _required power level_.

### Redaction algorithm

The [redaction algorithm] is updated to preserve the `state` key on `m.room.power_levels` events, similarly to `events`.

## Potential issues

### Increased complexity of `m.room.power_levels`

This proposal introduces yet another key to the power levels event, which requires management by clients. Clients are
also required to determine which events are state events and list them in the appropriate map.

## Alternatives

### Continue using `events` for both state and message events

The existing model could be preserved, which requires room administrators to accept that any event type that
unprivileged users may send may also be sent as a state event. This proposal exists to address this very concern.

### Global minimum power level to send state

This proposal could be simplified to require one minimum power level to send all state events, no matter what the
`events` map defines. For example, it could be enforced that to send any state event, even one present in `events`, the
user must have at least `state_default`.

This was not chosen because there are legitimate scenarios where room admins may want to allow users to set certain
event types.

### Naming of the `state` map

The name `state` was chosen due to similarity to `state_default`, `events`, and `events_default`. It could alternatively
be named `state_events`, or similar.

## Security considerations

This proposal does not introduce any new class of authorization vulnerability, as the behavior is otherwise unchanged
from the current specification.

Implementations must ensure that the power levels specified in `events` and `state` are used to determine the required
power level as this proposal specifies.

This proposal does not introduce any new security considerations, as far as its author is aware.

## Implementation considerations

Implementations of this MSC's room version will need to ensure that room creation templates, upgrade APIs, etc. properly
handle the `state` key.

Clients will need to update their power level updating UX to distinguish between custom state and message events,
alongside properly assigning known event types to the proper map.

## Unstable prefix

This proposal's functionality will exist in an unstable room version until another MSC can assign it to a stable room
version. This is a normal process for the specification. See [MSC4304 (merged)][MSC4304] for an example of this process.

Implementations should use `dev.zirco.msc4527.v1` as an unstable room version using v12 as a base until this MSC can be
adopted into a stable room version.

## Dependencies

None.

[`m.room.power_levels`]: https://spec.matrix.org/v1.19/client-server-api/#mroompower_levels
[auth rules]: https://spec.matrix.org/v1.19/rooms/v12/#authorisation-rules
[Room Version 12]: https://spec.matrix.org/v1.19/rooms/v12/
[redaction algorithm]: https://spec.matrix.org/v1.19/rooms/v12/#redactions
[MSC4304]: https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4304-room-version-12.md
