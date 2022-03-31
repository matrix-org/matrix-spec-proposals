# MSC3760: State sub-keys

## Problem

Currently there are three main ways to limit who can overwrite a state event:

 * If a user's PL is greater than the `m.room.power_levels` `state_default` field
 * If a user's PL is greater than the `m.room.power_levels` `events` field for that event type
 * If a state event has a state key which begins with an `@`, then the sender's mxid must match that state key.

This is problematic if an unprivileged user needs to publish multiple state events of the same type in a room, but would like to set access control so that only they can subsequently update the event. An example of this is if a user wishes to publish multiple live location share beacons as per [MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) and [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672).  They will typically not want other users in the room to be able to overwrite the state event, so we need a mechanism to prevent other peers from doing so.

## Proposal

We propose adding an optional `state_subkey` top-level field that allows multiple state events to exist which all have the same `state_key` but represent different pieces of state.

This means that the existing rules around access control to state events can be unchanged, but now one user can own multiple pieces of state that have the same `type`.

For example, to post a live location sharing beacon from [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672):

```json=
{
    "type": "m.beacon_info",
    "state_key": "@stefan:matrix.org", // Ensures the sender has control
    "state_subkey": "asset1",          // Does not clash with other events
    "content": {
        "m.beacon_info": {
            "description": "Stefan's live location",
            "timeout": 600000,
            "live": true
        },
        "m.ts": 1436829458432,
        "m.asset": {
            "type": "m.self.live"
        }
    }
}
```

State events that are missing `state_subkey` should behave exactly as if `state_subkey` had a value of `""`.

Two state events with identical `type` and `state_key` should be treated as independent if they have different values of `state_subkey`.

## Potential issues

This change involves modifying the way the keys in a room's state map are constructed, so may be complex to implement.

This will require a new room version.

## Alternatives

We could add a suffix to the `event_type`, as originally proposed in [MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489). This can make life difficult for clients who expect a fixed type, and it makes it hard to control power levels for event types.

We could stuff the mxid and subtype into the `state_key` field as proposed in [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757). This would involve changing the access control logic for state events, and objections were raised about the need to parse the state key's contents.

We could allow additional events that set up access control on a state event.

We could add a flag on the contents of the event (as originally proposed in [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757)), called e.g. `m.peer_unwritable: true` to say other users were prohibited from overwriting the event.  However, this is impractical because there isn't a good value for the state_key, which needs to be unique and not subject to races from other malicious users.

## Security considerations

The rules on who can modify a state event are unchanged by this proposal, which should simplify security concerns relative to the alternatives.

Server implementors will need to ensure that the state_subkey has no effect on the access control of state events.

This will require a new room version, meaning it will not affect old events.

## Unstable prefix

 * `state_subkey` should be referred to as `org.matrix.mscxxxx.state_subkey` until this MSC lands.

## Dependencies

None
