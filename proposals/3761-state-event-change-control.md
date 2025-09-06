# MSC3761: State event change control

Currently Matrix doesn't support an option of allowing some people in the room to change or modify a
particular state event, though this would be ideal for cases like
[Live Location Sharing](https://github.com/matrix-org/matrix-spec-proposals/pull/3672) where the user
would like to publish more than one beacon's worth of information. Currently in Matrix a user's ability
to send a given state event is limited by power levels (`state_default` and `events` dictionary) as
well as the state key itself: if the state key is a user ID, only that user can send that event. However,
if multiple beacons are required, the access control would mean that the sender needs to use arbitrary
state keys and thus would allow anyone with permission to send those events permission to edit/change
the beacon.

***TODO: A better intro, probably from https://github.com/matrix-org/matrix-spec-proposals/pull/3757***

Related MSCs:
* [MSC3760: State sub-keys](https://github.com/matrix-org/matrix-spec-proposals/pull/3760)
* [MSC3757: Restricting who can overwrite a state event](https://github.com/matrix-org/matrix-spec-proposals/pull/3757)
  (string-packed state key version)

## Proposal

We introduce a new state event called `m.event.acl` with a `content` which looks as follows:

```json5
{
    // We only define "change" for now, but leave deliberate room for concepts of
    // additional, removal, etc.
    //
    // All fields in this object are optional.
    "change": {
        // The user IDs which can make the change. The sender is *not* automatically
        // part of this array, so must be explicitly included.
        "user_ids": ["@myself:example.org"],

        // Array of top level keys on the power level event. Putting "redact" here means
        // "anyone with permission to redact can edit this". Sub-keys are not supported
        // though also not expected to be needed.
        "with_power_for": ["redact"]
    }
}
```

The `state_key` for this ACL event would be arbitrary.

The ability to send this ACL event would still be subject to power levels, except in the special case where the
sender uses a `state_key` of their own user ID: this bypasses the `events["m.event.acl"]` power level check,
allowing the user to define a single ACL for their state events. If they want multiple ACLs, they will need
permission to do so.

To apply this ACL to a state event, the sender would include an `?acl=$event_id_of_acl` query parameter to
[`PUT /state/:type/:key`](https://spec.matrix.org/v1.2/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
which denotes the ACL event to apply to the to-be-sent state event. If the sender fails the existing ACL on the
target state event, the event cannot be sent. Similarly, if the ACL event ID is not able to be located, the event
cannot be sent.

***TODO: Should the state event be rejected if the ACL event ID cannot be resolved, or just treat it as an ACL of "no one"?***

The ACL event ID is then appended to the top level of the state event as `acl`:

```json5
{
    "type": "org.example.event",
    "state_key": "whatever",
    "acl": "$abcdef",
    "content": {
        // event-specific detail
    },
    // etc
}
```

Changes to that state event, including the removal of the ACL event ID from the event (by not sending an `?acl` on
subsequent `PUT`s), must include the ACL event which allows the change in its `auth_events`.

Additionally, anyone who can normally redact a (state) event can *always* redact the ACL'd state event and the ACL
event itself.

Only events which are **not** included in `auth_events` can be ACL'd. This means that ACL events cannot be ACL'd,
however because the ACL'd state events point to a specific event ID this should not be a problem: even if a room
admin changes the ACL, the events which are using that ACL are not affected.

## Potential issues

***TODO***

## Alternatives

***TODO***

## Security considerations

***TODO*** - most of them are in the proposal text already.

## Unstable prefix

While this MSC is not incorporated into a stable room version, `m.event.acl` and its behaviour should only be used
rooms versioned as `org.matrix.msc3761` (using v9 as a base for all other algorithms).
