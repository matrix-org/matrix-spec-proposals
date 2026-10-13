# MSC3907: Mute Policy Recommendation

## Introduction

Matrix policy lists currently have a very limited scope. This MSC is just the first out of a series
of MSCs that aim to expand this system. In this MSC we add a new recommendation of `m.mute`.

Mutes are a standard tool in the moderators toolkit on most platforms and are already
used informally on matrix today.
Typically to mute a member of a room, a moderator has two options. They either find the member
to mute a user listing in their client and edit their power level or they
edit their power level directly by editing the room's `m.room.power_level` event manually.
This is an error prone process as in either case the incorrect value can be given for the power
level and some degree of risk in racing if another moderator also edits the rooms power level.
On top of this, the process has to be repeated in each room that they wish to mute the user in.
Granted, some of this can be alleviated with use of a script/bot, but we believe a mute policy
recommendation would enable for a standard user expeirance for muting participants.
The mute recommendation would also open the door for the implementation of mute to be
changed transparently, and we will be introducing another MSC3909 that does this.

Mutes will become less clumsy to use if they can be applied as policy. Especially when used together with
MSC3907 to make them be able to expire on their own. MSC3909 will in the future also make them even better
by making them a membership state if that MSC is implemented. This MSC is technically fully independent
of these 2 MSCs.

## Proposal

This MSC will create a new Policy List recommendation of `m.mute`. Below is an example event for this MSC
that displays how it would be used in conjunction with MSC3908.

```
{
  "content": {
    "entity": "@evil:example.com",
    "reason": "spam",
    "recommendation": "m.mute",
    "expiry": 2000003600
  },
  "sender": "@mjolnir:example.com",
  "state_key": "_evil:example.com",
  "type": "m.policy.rule.user",
  "event_id": "exampleid",
  "room_id": "!policylist:example.com"
}
```

Below is the same event but without the expiry.

```
{
  "content": {
    "entity": "@evil:example.com",
    "reason": "spam",
    "recommendation": "m.mute",
  },
  "sender": "@mjolnir:example.com",
  "state_key": "_evil:example.com",
  "type": "m.policy.rule.user",
  "event_id": "exampleid",
  "room_id": "!policylist:example.com"
}
```

Note: The state key is an identifier for the rule, it is not supposed to be used for traceability
between the entity and the state event, it includes the mxid of the user in this example
for debugging purposes only.

When it's applied on a client level its recommended to be ignored as to not be redundant with the m.ban
recommendation. A future MSC is welcome to make m.ban and m.mute be recommended to be applied the same.

When the `m.mute` recommendation is used, the entities effected by the rule should be suspended from
participation where possible, but have their visibility of the room maintained.
The enforcement of this is deliberately left as an implementation detail to avoid imposing an on how
the policy rule is interpreted. However a suggestion for a simple implementation is as follows:

* is a `user` rule:
  + Applied to a user: Hide any new messages from the user's DM's, do not display notifications
    or pings from them.
  + Applied to a room: The user's power level should be lowered below the required level to send
    `events_default`.
  + Applied to a server: The user should be suspended from sending events and uploading media.
    Effectively leaving the user's account in a read-only state.

* is a `room` rule:
  + Applied to a user: New events from the room are ignored, not displayed in notifications and
    not shown to be active in a client.
  + Applied to a room: No-op? Could be changing `events_default` to the same level as moderators
  + Applied to a server: No-op? Could also be rendering the room read only from the specific server.

* is a `server` rule:
  + Applied to a user: No op
  + Applied to a room: No op
  + Applied to a server: No op.

The most important (and main motivation)
of these recommendations is when a `user` rule is applied to a `room`.

It should be noted that the current recommendation for a `user` rule applied to a `room`
can come at the cost of rapid PL churn if used frequently. We hope that MSC3909 can address this.

## Potential issues

- Causing state resolution to become more intensive due to causing a rapid growth in PL events being
  when implementations follow the advice for a `user` rule applied to a `room`.

## Alternatives

There are few if any viable alternatives to doing this via Policy lists to achieve the goals of the MSC.

But the way this MSC recommends applying a mute is straight up inferior to MSC3909 way of doing it.
The MSCs in this MSC package are all not dependent on each other but are greatly enhanced by each other.

Now as for how to practically implement a mute the merits of preferring the approach taken in MSC3909
are going to be discussed in that MSC.

## Security considerations

This MSC has no new security considerations for policy lists. But applying this MSC without the use of
MSC3909 will require that the applying party in the case of applying at a room level against a user
the issuance of new power level events. This is problematic due to the effects it has on the room state.
This is elaborated on in MSC3909

## Unstable prefix

During the time this MSC is unstable `m.mute` is replaced with `support.feline.policy.recomendation_mute`

## Dependencies

This MSC builds on MSC3909, MSC3908 and MSC3784 (which at the time of writing have not yet been accepted
into the spec).

It does not require any of these MSCs to be implemented but it works best when implemented together with the rest of these MSCs.

MSC3909 to heavily improve upon mutes, MSC3908 to make temporary mutes an option
and MSC3784 to help enable building better user experiences interacting with policy lists.
