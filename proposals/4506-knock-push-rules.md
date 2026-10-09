# MSC4506: Push rules for knocking

[MSC2403](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2403-knock.md)
lets users knock on a room: they send an `m.room.member` event with
`content.membership: knock`, and wait for someone in the room to accept (invite) or reject (kick)
them. A knock is only useful once someone who can act on it notices it - but today no push rule
matches a knock, and the default `.m.rule.member_event` override rule explicitly matches all
`m.room.member` events and applies no push actions.

MSC2403 acknowledged the gap and deliberately deferred it:

> To help knocks be noticed earlier, it would be nice to send a push notification to those in the
> room who can act on a knock when it comes in, rather than everyone in the room. This would
> require a push rule to fire only when that user's power level is high enough to accept or reject
> a knock. With the current push rules implementation it is possible to place a condition on the
> sender's power level, but unfortunately the same does not exist for event recipients. This MSC
> thus does not propose any changes to push rules at this time, but acknowledges that it would be
> useful for a future MSC to address when the underlying push rules architecture can support it.

This MSC aims to fill that gap.  It adds the missing push rule architecture (a condition on the
recipient's permissions) and uses it to define a default push rule for knocks which notifies
only the members who can act on them.

It takes some inspiration from [MSC4505](https://github.com/matrix-org/matrix-spec-proposals/pull/4505)
and in turn [MSC3903](https://github.com/matrix-org/matrix-spec-proposals/pull/3930)

## Proposal

### New condition: `recipient_permission`

A new push rule condition kind is added, the recipient-side analogue of the existing
[`sender_notification_permission`](https://spec.matrix.org/v1.11/client-server-api/#conditions-1)
condition:

```jsonc
{"kind": "recipient_permission", "key": "invite"}
```

The condition matches if and only if the user for whom the push rules are being evaluated has
a power level greater than or equal to the level required to perform the action named by `key`
(in the context of the event's room).

`key` is one of the permission-defining keys of
[`m.room.power_levels`](https://spec.matrix.org/v1.11/client-server-api/#mroompower_levels):
`invite`, `kick`, `ban` or `redact`.

Both the user's power level and the required level are
determined as they would be for performing the action itself, evaluated against the current state
at the time of the event: the same point-in-time semantics as `sender_notification_permission`.

If `key` is none of the values above, the condition does not match.

### New default override rule: `.m.rule.knock`

Using the new condition, a default override rule is defined, inserted immediately after
`.m.rule.invite_for_me` - and thus before `.m.rule.member_event` (which would
otherwise suppress it):

```jsonc
{
  "rule_id": ".m.rule.knock",
  "default": true,
  "enabled": true,
  "conditions": [
    // Note: `.` is escaped once, but for valid JSON we need to escape the escape.
    {"kind": "event_property_is", "key": "type", "value": "m\\.room\\.member"},
    {"kind": "event_property_is", "key": "content.membership", "value": "knock"},
    {"kind": "recipient_permission", "key": "invite"}
  ],
  "actions": [
    "notify",
    {"set_tweak": "sound", "value": "default"}
  ]
}
```

`key: "invite"` is used because accepting a knock *is* inviting the knocker: the set of
users who can accept a knock is exactly the set who pass this condition. (Rejecting a knock is a
kick, but a user who can only reject and not accept is not who this notification is for; see
the Alternatives section.)

## Potential issues

In rooms where `invite` requires no power (the `m.room.power_levels` default for `invite` is 0),
every member is pushed for every knock. This is semantically correct, and rooms that select the
knock join rule to gate entry are overwhelmingly expected to also raise the `invite` level.
Users who can act on knocks but don't want to hear about them can disable the rule; it is an
ordinary default rule.

A knocking user may re-send their knock membership event (e.g. to update the `reason`, or a
profile change while knocked); each such event matches the rule again and re-pushes.
Re-knocking after being denied likewise pushes again, which is correct behaviour but could be
used to nag; the existing anti-abuse tools (server-side rate limiting of knocks, and rejecting +
banning) apply.

A user whose power level is raised past the invite level after a knock was sent will not be
retroactively pushed about pending knocks; clients already surface pending knocks in the room UI
(e.g. as a banner), which covers this case.

The `recipient_permission` condition makes push rule evaluation depend on the recipient, not just
the event. This is already the case for other conditions (`contains_display_name`,
`event_match` on `user_id`-templated rules), so it introduces no new architectural constraint for
implementations which evaluate rules per-user, but implementations which cache a single
evaluation result per event would need to take the recipient's power level into account.

As with any new condition kind, *clients* which re-evaluate push rules locally (as the major
implementations do, treating unknown condition kinds as never matching) will not notify for the
new rule until they implement the condition, even when their homeserver already pushes for it -
for push-gateway-driven clients the push arrives but is discarded when the client recomputes the
event's actions.

## Alternatives

 * Notify everyone in the room: (i.e. don't introduce the `recipient_permission` condition).
   This is simpler, but of questionable value given we're pushing people for something they can't
   act on, and it amplifies potential abuse vectors.  The only justification would be if you
   were relying on non-moderators in the room to spot the knock and then nudge a moderator
   or mod-bot to accept the knock.

 * Support `key: "kick"` as well as `invite` for the `recipient_permission` condition.
   A user with kick-but-not-invite power can only reject knocks; potentially we could push them
   about knocks, but it feels like a strange default. A room that wants different behaviour
   can define custom rules with `recipient_permission` directly anyohw.

 * Don't set a default on the server at all.  Any client of the recipient could insert a user-scoped
   rule via the push rules API - but no existing condition can express "I can invite", so this
   does not avoid the new condition; and per-client rule lifecycle management leaves users of other
   clients without notifications. A default server-side rule matches how every other notifying
   event type works.

## Security considerations

The condition's inputs (the room's power levels and membership events) are ordinary room state
already visible to all members; no new information is exposed.

A malicious knocker can cause pushes to room moderators, but could already cause pushes to the
same or larger audiences by other means (e.g. sending messages to any public room); knock rate
limiting applies.

## Unstable prefix

While this MSC is not considered stable, implementations should use the following identifiers:

| Stable | Unstable |
|---|---|
| `.m.rule.knock` | `.org.matrix.msc4506.rule.knock` |
| `recipient_permission` (condition kind) | `org.matrix.msc4506.recipient_permission` |

## Dependencies

None