# MSC3757: Restricting who can overwrite a state event.

## Problem

Currently there are three main ways to limit who can overwrite a state event:

 * If a user's PL is greater than the `m.room.power_levels` `state_default` field
 * If a user's PL is greater than the `m.room.power_levels` `events` field for that event type
 * If a state event has a state key which begins with an `@`, then the sender's mxid must match that state key.

This is problematic if an unprivileged user needs to publish multiple state
events of the same type in a room, but would like to set access control so
that only they can subsequently update the event. An example of this is if a
user wishes to publish multiple live location share beacons as per [MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)
and [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672), for instance one per device.  They will typically not want
other users in the room to be able to overwrite the state event,
so we need a mechanism to prevent other peers from doing so.

[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) originally proposed that the event type could be made variable,
appending an ID to each separately posted event so that each one could
separately be locked to the same mxid in the state_key.  However, this is
problematic because you can't proactively refer to these event types in the
`events` field of the `m.room.power_levels` event to allow users to post
them - and they also are awkward for some client implementations to
manipulate.

## Proposal

Therefore, we need a different way to state that a given state event may only
be written by its owner. **We propose that if a state event's state_key *starts with* a matrix ID (followed by an underscore), only the sender with that matrix ID (or higher PL users) can set the state event.**  This is an extension of the current behaviour where state events may be overwritten only if the sender's mxid *exactly equals* the state_key.

We also allow users with higher PL than the original sender to overwrite state 
events even if their mxid doesn't match the event's state_key. This fixes an abuse
vector where an unprivileged user can immutably graffiti the state within a room
by sending state events whose state_key is their matrix ID.

Practically speaking, this means modifying the [authorization rules](https://spec.matrix.org/v1.2/rooms/v9/#authorization-rules) such that rule 8:

> If the event has a `state_key` that starts with an `@` and does not match the `sender`, reject.

becomes:

> If the event has a `state_key` that starts with an `@`, and the substring before the first `_` that follows the first `:` (or end of string) does not match the `sender`, reject - unless the sender's powerlevel is greater than the event type's *required power level*.

For example, to post a live location sharing beacon from [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672):

```json=
{
    "type": "m.beacon_info",
    "state_key": "@stefan:matrix.org_assetid1", // Ensures only the sender or higher PL users can update
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

Since `:` is not permitted in the localpart and `_` is not permitted in the domain part of an mxid (see [Historical User IDs](https://spec.matrix.org/v1.2/appendices/#historical-user-ids)), it is not possible to craft an mxid that matches the beginning of a state key constructed for another user's mxid, so state keys restricted to one owner can never be overwritten by another user.

## Potential issues

None yet.

## Alternatives

As originally proposed in [MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) and [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672), we can require
the use of a state key equal to the sender's mxid, but this means we can only
have one such event of each type, so those MSCs proposed using different types
for each unique event.

An earlier draft of this MSC proposed putting a flag on the contents of the 
event (outside of the E2EE payload) called `m.peer_unwritable: true` to indicate
if other users were prohibited from overwriting the event or not.  However, this
unravelled when it became clear that there wasn't a good value for the state_key,
which needs to be unique and not subject to races from other malicious users.
By scoping who can set the state_key to be the mxid of the sender, this problem
goes away.

[MSC3760](https://github.com/matrix-org/matrix-spec-proposals/pull/3760)
proposes to include the `sender` (or a dedicated `state_subkey`)
as the third component of what makes a state event unique.

## Security considerations

This change requires a new room version, so will not affect old events.

As this changes auth rules, we should think carefully about whether could
introduce an attack on state resolution. For instance: if a user had higher
PL at some point in the past, will they be able to abuse somehow this to
overwrite the state event, despite not being its owner?

When using a state_key prefix to restrict who can write the event, we have
deliberately chosen an underscore to terminate the mxid prefix, as underscores
are not allowed in domain names.  A pure prefix match will **not** be sufficient,
as `@matthew:matrix.org` will match a state_key of form `@matthew:matrix.org.evil.com:id1`.

This changes auth rules in a backwards incompatible way, which will break any
use cases which assume that higher PL users cannot overwrite state events whose 
state_key is a different mxid.  This is considered a feature rather than a bug,
fixing an abuse vector where unprivileged users could send arbitrary state events
which could never be overwritten.

## Unstable prefix

While this MSC is not considered stable, implementations should apply the behaviours of this MSC on top of room version 9 as `org.matrix.msc3757`.

## Dependencies

None
