# MSC3779: "Owned" state events

## Problem

[Live location sharing](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) and [group VOIP signalling](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) both need non-admin users to be able to create state events, but the default room power levels prevent this.

This means that to allow normal users to place a call or share their live location, either:

* users must be granted a higher power level, or
* rooms must have non-default power levels to allow anyone to create state events.

We anticipate that other future applications will have a similar need for normal users to be able to create state events.

## Proposal

We propose allowing unprivileged users to create "owned" state events, where the `state_key` equals their MXID, or starts with their MXID plus underscore.

This will require a new room version since it affects room permissions.

(Note: this is inspired by [MSC3757 Restricting who can overwrite a state event](https://github.com/matrix-org/matrix-spec-proposals/pull/3757), but these two proposals are independent.)

### Affected events (state_key starts with sender MXID)

For example, to start sharing a live location:

```json5
{
    "type": "m.beacon_info",
    "state_key": "@matthew:matrix.org_uiyeesknsfbhhbsdf",
    "sender": "@matthew:matrix.org",
    "content": {
        // details omitted
    }
}
```

The above event will be allowed even if the user does not have the `state_default` power level because the state key starts with the sender's MXID plus underscore.

Similarly, if the state key were exactly the sender's MXID it would also be allowed:

```json5
{
    "type": "m.beacon_info",
    "state_key": "@matthew:matrix.org",
    "sender": "@matthew:matrix.org",
    "content": {
        // details omitted
    }
}
```

### Unaffected events (where state_key does not start with sender)

Events like the following will NOT be affected:

```json5
{
    "state_key": "@andyb:matrix.org_uiy", // NOT affected - wrong MXID
    "sender": "@matthew:matrix.org",
    // Other parts omitted
}
```

```json5
{
    "state_key": "", // NOT affected - must start with MXID
    "sender": "@matthew:matrix.org",
    // Other parts omitted
}
```

For these events the existing rules on power levels will apply. (Note: in fact, the first event will be rejected by rule 8 of the Authorisation Rules even if the sender has a sufficient power level, because the state_key does not equal the sender's MXID.)

### Unaffected events (where event type is a special case)

Events such as `m.room.power_levels` that require `state_key` to be `""` will not be affected.

Events such as `m.room.create` and `m.room.member` which have special handling in the Authorisation Rules will not be affected.

## Spec wording

In section 7.5 of the Client-Server API, the section [m.room.power_levels](https://spec.matrix.org/v1.2/client-server-api/#mroompower_levels) paragraph 3 should be changed to read:

> The level required to send a certain event is governed by `events`, `state_default` and `events_default`. If an event type is specified in events, then the user must have at least the level specified in order to send that event. If the event type is not supplied, it defaults to `events_default` for Message Events **and owned State Events**, and `state_default` for **other** State Events. **Owned state events are events with a `state_key` that equals the sender's MXID, or starts with the sender's MXID plus an underscore.**


In section 5 of the Server-Server API, [5.1.1 Definitions](https://spec.matrix.org/v1.2/server-server-api/#definitions) paragraph 1 should be changed to read:

> #### Required Power Level
> A given event type has an associated *required power level*. This is given by the current `m.room.power_levels` event. The event type is either listed explicitly in the events section or given by either `state_default` **(for non-owned state events)** or `events_default` **(for message events and owned state events)**. **Owned state events are events with a `state_key` that equals the sender's MXID, or starts with the sender's MXID plus an underscore.**

Additionally, to improve clarity, we propose that the relevant section be explicitly mentioned in the room version definition, section "3.4 Authorisation rules". Rule 7 should be changed to read:

> If the event type’s *required power level* **(see "m.room.power_levels" in the Room Events section of the Client-Server API)** is greater than the `sender`’s power level, reject.

## Alternatives

### Manually set power_levels

In Element Call, rooms are created with `m.room.power_levels` set to allow the `m.call.member` event to be emitted by users with power level 0. This only works if you control the room creation process. Given that we probably want people to be able to participate in calls and share live locations in any room by default, requiring each room's power levels to be changed seems onorous.

### Change the default power_levels for some event types

We could modify the default power levels of a room to include a list of the event types that we want to be allowed, but this would create a growing, centrally-managed list of event types, and make life difficult for applications whose event type has not yet been included in the spec.

### Combine this proposal with MSC3757

We did consider bundling this MSC as part of [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757) but since they are actually independent and that MSC has already received some review we felt that the more principled approach was to keep them separate. We do prefer that they be included in the same room version if accepted.

## Security considerations

### Attacks on room state

Restrictions on creation of state events were introduced to prevent graffiti (e.g. changing room topic) and denial-of-service attacks which increase the size of the room state to unmanageable levels. By allowing all users to create some state events by default, we make it possible for a room's state to be modified by users who do not have any special permission.

By restricting these events to those with a state_key unique to the sender, we prevent unauthorised users from modifying room topics or other similar state, and we make it clear who is responsible for any such state.

If an individual user is sending too many state events, the server should apply rate limiting.

If many users are performing a distributed attack on room state, this should be managed via moderation tools.

Any other proposal that allows non-admin users to update room state (e.g. by special-casing particular event types) will likely allow similar attacks.

### Beware of non-empty state_keys on special events

Servers should take special care to ensure that important event types such as `m.room.power_levels` and `m.room.topic` have no effect when the `state_key` is set to start with the sender's MXID instead of the empty string as they usually do.  This proposal allows some such events to be created by unprivileged users, and they should be ignored in contexts where `state_key` should be empty.
