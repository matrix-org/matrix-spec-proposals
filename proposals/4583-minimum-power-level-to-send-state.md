# MSC4583: Minimum power level to send state

Many communities on Matrix choose to enforce a strict [`m.room.power_levels`] that restricts members from sending
unknown or future event types by setting `events_default` > `users_default` and setting specific `events` overrides
for event types they desire to allow (e.g. `m.reaction` and `m.room.message`).

When a room's power levels are configured in this way, the value in `events` overrides `state_default`, hence an
unprivileged user can send a permitted event type as a state event. This allows that event to become part of room state
permanently, which is behavior often undesirable in large public rooms as it increases room complexity.

This proposal introduces a room-wide minimum power for sending state, `state_minimum`, alongside the required changes to
[auth rules] and the [redaction algorithm].

**Note:** This proposal has a similar goal to that of [MSC4527], but uses a different mechanism to solve the same
problem.

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

A new integer key, `state_minimum`, is added to the [`m.room.power_levels`] event, alike to `state_default`.

If the field is missing, or the room has no `m.room.power_levels` event, the value of `state_minimum` is assumed to be
`50`.

Example `m.room.power_levels` event:

```jsonc
{
    "events_default": 1,
    "events": {
        "m.room.message": 0,
        "m.reaction": 0,
        "m.sticker": 0,
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
    "state_minimum": 50, // Added by this proposal
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

The *required power level* to send an event, with the exception of membership events and redactions, is updated to be
as follows:
1. **If the event is a _state event_:**
    1. If the event type is specified in `events`, the user must have at least power level
       `max(events[type], state_minimum)` to send that event.
    2. If the event type is not specified, the user must have at least power level `max(state_default, state_minimum)`
       to send that event.
2. If the event type is specified in `events`, the user must have at least the level specified to send that event.
3. If the event type is not specified, the user must have at least the `events_default` power level to send that event.

The required power level for redactions and membership events remains unchanged from the current specification.

### Auth rules

Step 8 of the [event authorisation rules][auth rules] is updated to use the above definition of _required power level_.

### Redaction algorithm

The [redaction algorithm] is updated to preserve the `state_minimum` key on `m.room.power_levels` events.

## Potential issues

### Increased complexity of `m.room.power_levels`

This proposal introduces yet another key to the power levels event, which requires management by clients. Clients which
currently read the power levels state in a room might not understand this key, and will need to be updated to represent
if an action is legal. This is acceptable, considering the security benefits this proposal provides, and prevents
further breaking changes such as those introduced by [MSC4527].

### Desired editable state events

In some cases, it may be desirable for unprivileged users to be able to set state events in a room. The benefits of this
proposal primarily benefit large public rooms, which are most likely to use a restrictive power levels configuration
like the one demonstrated above. Sticky events, as specified in [MSC4354 (merged)][MSC4354], largely relieve this
problem for the two most obvious cases, those being [MatrixRTC][MSC4143] and [MSC3489] live location sharing.

## Alternatives

### Change nothing

The existing model could be preserved, which requires room administrators to accept that any event type that
unprivileged users may send may also be sent as a state event. This proposal exists to address this very concern.

### Explicitly list power level per state event

The approach taken by [MSC4527] could be taken, defining a `state` map. This was not chosen because of the additional
complexity that proposal adds to clients, introducing potential security concerns with older clients.

## Security considerations

This proposal does not introduce any new class of authorization vulnerability, as the behavior is otherwise unchanged
from the current specification.

Implementations must ensure that the power level specified in `state_minimum` is properly used to determine the required
power level as this proposal specifies.

This proposal does not introduce any new security considerations, as far as its author is aware.

## Implementation considerations

Implementations of this MSC's room version will need to ensure that room creation templates, upgrade APIs, etc. properly
handle the `state_minimum` key.

Clients will need to update their power level updating UX to allow editing this key.

## Unstable prefix

This proposal's functionality will exist in an unstable room version until another MSC can assign it to a stable room
version. This is a normal process for the specification. See [MSC4304 (merged)][MSC4304] for an example of this process.

Implementations should use `dev.zirco.msc4583.v1` as an unstable room version using v12 as a base until this MSC can be
adopted into a stable room version.

## Dependencies

None.

[`m.room.power_levels`]: https://spec.matrix.org/v1.19/client-server-api/#mroompower_levels
[auth rules]: https://spec.matrix.org/v1.19/rooms/v12/#authorisation-rules
[Room Version 12]: https://spec.matrix.org/v1.19/rooms/v12/
[redaction algorithm]: https://spec.matrix.org/v1.19/rooms/v12/#redactions
[MSC3489]: https://github.com/matrix-org/matrix-spec-proposals/pull/3489
[MSC4143]: https://github.com/matrix-org/matrix-spec-proposals/pull/4143
[MSC4304]: https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4304-room-version-12.md
[MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354
[MSC4527]: https://github.com/matrix-org/matrix-spec-proposals/pull/4527
