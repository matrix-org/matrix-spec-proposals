# MSCXXXX: Push rules for live location sharing

[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) and
[MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672) describe live location
sharing (LLS).  A user starts a share by sending an `m.beacon_info` state event (with their user id as the
`state_key`, setting `content.live: true`), streams location updates as `m.beacon` timeline events
referencing it, and stops the share by updating the state event to `content.live: false`.

Neither proposal defines how push notifications work for these events: as starting a share is
a state event, no default push rule matches it, meaning users have no way of being told when
someone is trying to share their location with them.

This proposal fills that gap, much as
[MSC3930](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3930-polls-notifications.md)
did for polls.

## Proposal

We define the following underride push rules, following the same pattern as 
[MSC3930](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3930-polls-notifications.md).
The rules are to be inserted immediately after the `.m.rule.poll_end` underride rule, in the order
presented.  We only push for LLS beginning (`content.live: true`), not stopping (`content.live: false`).

```jsonc
{
  "rule_id": ".m.rule.beacon_info_one_to_one",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "room_member_count", "is": "2"},
    // Note: `.` is escaped once, but for valid JSON we need to escape the escape.
    {"kind": "event_property_is", "key": "type", "value": "m\\.beacon_info"},
    {"kind": "event_property_is", "key": "content.live", "value": true}
  ],
  "actions": [
    "notify",
    {"set_tweak": "sound", "value": "default"}
  ]
}
```

```jsonc
{
  "rule_id": ".m.rule.beacon_info",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "event_property_is", "key": "type", "value": "m\\.beacon_info"},
    {"kind": "event_property_is", "key": "content.live", "value": true}
  ],
  "actions": [
    "notify"
  ]
}
```

Additionally, for unencrypted rooms, a new override rule is defined to explicitly suppress the `m.beacon`
location update events, inserted immediately after the `.m.rule.poll_response` override rule. 
This stops sending needless push for every LLS beacon update.

```jsonc
{
  "rule_id": ".m.rule.beacon",
  "default": true,
  "enabled": true,
  "conditions": [
    {"kind": "event_property_is", "key": "type", "value": "m\\.beacon"}
  ],
  "actions": []
}
```

## Potential issues

The `.m.rule.beacon` suppression cannot take effect in encrypted rooms, where location updates are
sent as `m.room.encrypted` events and therefore match the `.m.rule.encrypted` underride on the
server. Clients which re-evaluate push rules against the decrypted event (as the major
implementations do) will suppress the notification via `.m.rule.beacon` at that point; the cost of
the spurious push wakeups themselves is a pre-existing problem for all encrypted event types that
are uninteresting once decrypted, and is out of scope here.

Re-sending `m.beacon_info` with `live: true` (e.g. extending a share's timeout) will notify again.
This is arguably correct ("X is (still) sharing their live location"); clients may wish to
de-duplicate notifications for a beacon they already know about.

As with [MSC3930](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/3930-polls-notifications.md),
these rules are a stop-gap of the current push rules system rather than a step
towards a general solution for extensible events, and future work on notifications for extensible
events would supercede them.

## Alternatives

A client-managed custom push rule (any client of the recipient inserts an equivalent user-scoped
rule via the push rules API) would work without server changes, but requires every client
implementation to manage the rule's lifecycle and leaves users of clients which haven't done so
without notifications. Default server-side rules match how every other notifying event type works.

## Security considerations

None beyond those of MSC3489/MSC3672 themselves. The rules do not expose event content; they only
cause pushes for an event type that room members receive anyway.

## Unstable prefix

While this MSC is not considered stable, implementations should use the following identifiers,
matching the unstable event types from the
[unstable prefix section of MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672):

| Stable | Unstable |
|---|---|
| `.m.rule.beacon_info_one_to_one` | `.io.element.rule.beacon_info_one_to_one` |
| `.m.rule.beacon_info` | `.io.element.rule.beacon_info` |
| `.m.rule.beacon` | `.io.element.rule.beacon` |
| `m.beacon_info` (in conditions) | `org.matrix.msc3672.beacon_info` |
| `m.beacon` (in conditions) | `org.matrix.msc3672.beacon` |

## Dependencies

This MSC builds on [MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) and
[MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672)