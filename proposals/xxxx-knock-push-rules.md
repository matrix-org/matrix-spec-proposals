# MSCXXXX: Push rules for knocks

[MSC2403](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2403-knock.md)
(Matrix v1.1) lets users knock on a room: they send an `m.room.member` event with
`content.membership: knock`, and wait for someone in the room to accept (invite) or deny (kick)
them. A knock is only useful once someone who can act on it notices it — but today no push rule
matches a knock. Worse, the default `.m.rule.member_event` override rule explicitly matches all
`m.room.member` events with no actions, so a homeserver sends **no push at all** when someone
knocks. A knocker on a room whose moderators are offline or backgrounded can wait indefinitely.

MSC2403 itself acknowledged the gap and deliberately punted:

> To help knocks be noticed earlier, it would be nice to send a push notification to those in the
> room who can act on a knock when it comes in, rather than everyone in the room. This would
> require a push rule to fire only when that user's power level is high enough to accept or reject
> a knock. With the current push rules implementation it is possible to place a condition on the
> sender's power level, but unfortunately the same does not exist for event recipients. This MSC
> thus does not propose any changes to push rules at this time, but acknowledges that it would be
> useful for a future MSC to address when the underlying push rules architecture can support it.

This is that future MSC. It adds the missing push rule architecture — a condition on the
*recipient's* permissions — and uses it to define a default push rule for knocks which notifies
exactly the members who can act on them.

Note that this works identically in encrypted rooms: membership events are not encrypted, so
knocks are visible to server-side push rule evaluation even when the room is end-to-end encrypted.

## Proposal

### New condition: `recipient_permission`

A new push rule condition kind is added, the recipient-side analogue of the existing
[`sender_notification_permission`](https://spec.matrix.org/v1.11/client-server-api/#conditions-1)
condition:

```jsonc
{"kind": "recipient_permission", "key": "invite"}
```

The condition matches iff the user for whom the push rules are being evaluated (the would-be
recipient of the notification) has, in the room the event is in, a power level greater than or
equal to the level required to perform the action named by `key`. `key` is one of the
permission-defining keys of
[`m.room.power_levels`](https://spec.matrix.org/v1.11/client-server-api/#mroompower_levels):
`invite`, `kick`, `ban` or `redact`. Both the user's power level and the required level are
determined exactly as they would be for performing the action itself, including all the defaults
(`users_default`; 0 for `invite`; 50 for `kick`, `ban` and `redact`; and the fallbacks that apply
when the room has no `m.room.power_levels` event), evaluated against the current state at the time
of the event — the same point-in-time semantics as `sender_notification_permission`.

If `key` is none of the values above, the condition does not match (consistent with how unknown
conditions are handled generally).

### New default override rule: `.m.rule.knock`

Using the new condition, a default **override** rule is defined, inserted immediately after
`.m.rule.invite_for_me` — and thereby, crucially, *before* `.m.rule.member_event`, which would
otherwise suppress it:

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

`key: "invite"` is used because accepting a knock *is* inviting the knocker (MSC2403): the set of
users who can accept a knock is exactly the set who pass this condition. (Denying a knock is a
kick, but a user who can only deny and not accept is not who this notification is for; see
Alternatives.)

For the purposes of
[MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932), this rule is not
affected by room version limitations: knocks can only occur in room versions supporting them, so
in other room versions the rule is simply inert, and gating it would only complicate
implementations.

## Potential issues

In rooms where `invite` requires no power (the `m.room.power_levels` default for `invite` is 0),
every member is notified of every knock. This is semantically correct — every member really can
accept the knock — and rooms that select the knock join rule to gate entry are overwhelmingly
expected to also raise the `invite` level, as the Element clients' room creation presets do.
Users who can act on knocks but don't want to hear about them can disable the rule; it is an
ordinary default rule.

A knocking user may re-send their knock membership event (e.g. to update the `reason`, or a
profile change while knocked could be re-serialised by some implementation); each such event
matches the rule again and re-notifies. Re-knocking after being denied likewise notifies again,
which is correct behaviour but could be used to nag; the existing anti-abuse tools (server-side
rate limiting of knocks, and denying + banning) apply.

A user whose power level is raised past the invite level after a knock was sent will not be
retroactively notified of pending knocks; clients already surface pending knocks in the room UI
(e.g. as a banner), which covers this case.

The `recipient_permission` condition makes push rule evaluation depend on the recipient, not just
the event. This is already the case for other conditions (`contains_display_name`,
`event_match` on `user_id`-templated rules), so it introduces no new architectural constraint for
implementations which evaluate rules per-user, but implementations which cache a single
evaluation result per event would need to take the recipient's power level into account.

As with any new condition kind, *clients* which re-evaluate push rules locally (as the major
implementations do, treating unknown condition kinds as never matching) will not notify for the
new rule until they implement the condition, even when their homeserver already pushes for it —
for push-gateway-driven clients the push arrives but is discarded when the client recomputes the
event's actions. The inputs the condition needs (the room's `m.room.power_levels` and the user's
own power level) are ordinary room state that rule-evaluating clients already hold.

## Alternatives

**Notify everyone in the room** (a rule without the `recipient_permission` condition): simpler,
but noisy and wrong — in a typical moderated room most members cannot act on the knock, and being
told "X requested to join" with no ability to respond is pure noise. MSC2403 explicitly called
for power-level-gated notification.

**`key: "kick"` instead of, or in addition to, `invite`**: a user with kick-but-not-invite power
can only *deny* knocks. Notifying them would be defensible but is a strictly worse default: the
purpose of the notification is to get the knocker admitted. A room that wants different behaviour
can define custom rules with `recipient_permission` directly.

**A client-managed custom push rule**: any client of the recipient could insert a user-scoped
rule via the push rules API — but no existing condition can express "I can invite", so this
does not avoid the new condition; and per-client rule lifecycle management leaves users of other
clients without notifications. A default server-side rule matches how every other notifying
event type works.

**A generic `recipient_power_level` condition with a literal threshold** (e.g.
`{"kind": "recipient_power_level", "is": ">=50"}`): more general, but brittle — the correct
threshold is whatever the room's `m.room.power_levels` says `invite` requires, which varies per
room and over time. Naming the *action* keeps the rule correct in every room. The literal-threshold
form can always be a future addition if a use case appears.

## Security considerations

The condition's inputs (the room's power levels and membership events) are ordinary room state
already visible to all members; no new information is exposed. Push gateways learn that *some*
rule matched, as for any push — `event_id_only` payloads reveal nothing about the event type.

A malicious knocker can cause pushes to room moderators, but could already cause pushes to the
same or larger audiences by other means (e.g. sending messages to any public room); knock rate
limiting applies.

## Unstable prefix

While this MSC is not considered stable, implementations should use the following identifiers:

| Stable | Unstable |
|---|---|
| `.m.rule.knock` | `.org.matrix.mscxxxx.rule.knock` |
| `recipient_permission` (condition kind) | `org.matrix.mscxxxx.recipient_permission` |

## Dependencies

This MSC builds on [MSC2403](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2403-knock.md)
(accepted; Matrix v1.1) and uses the `event_property_is` push rule condition from
[MSC3758](https://github.com/matrix-org/matrix-spec-proposals/pull/3758) (accepted; Matrix v1.7).
