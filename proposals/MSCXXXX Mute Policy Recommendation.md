# MSC0000: Mute Policy Recommendation

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
changed transparently, and we will be introducing another MSC MSC_DAG_MUTE that does this.

Mutes will become less clumsy to use if they can be applied as policy. Especially when used together with
MSC_EXPIRY to make them be able to expire on their own. MSC_DAG_MUTE will in the future also make them even better
by making them a membership state if that MSC is implemented. This MSC is technically fully independent
of these 2 MSCs.

## Proposal

This MSC will create a new Policy List recommendation of `m.mute`. Below is an example event for this MSC
that displays how it would be used in conjunction with MSC_EXPIRY.

```
{
  "content": {
    "entity": "@evil:example.com",
    "reason": "spam",
    "recommendation": "m.mute",
    "expiry": 2000003600
  },
  "origin_server_ts": 2000000000,
  "sender": "@mjolnir:example.com",
  "state_key": "_evil:example.com",
  "type": "m.policy.rule.user",
  "unsigned": {},
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
  "origin_server_ts": 2000000000,
  "sender": "@mjolnir:example.com",
  "state_key": "_evil:example.com",
  "type": "m.policy.rule.user",
  "unsigned": {},
  "event_id": "exampleid",
  "room_id": "!policylist:example.com"
}
```

These events are both as they would be sent by a theoretical Mjolnir. Mjolnir's format was chosen for
the fact its used and this is intended to show how this could look in the real world for fields that
are implementation details.

Now how is this MSC applied in a vacuum. This MSC is recommended to be applied in the following way.
Please note that these recommendations are suggestions not requirements.

Because this rule type is practically useless unless the entity is a user this MSC Revision does not
allow the mute recommendation to be issued against rooms or servers. A future revision might.

When its applied on a client level its recommended to be ignored as to not be redundant with the m.ban
recommendation. A future MSC is welcome to make m.ban and m.mute be recommended to be applied the same.

When applied towards a user in a room a mute under this MSC would be executed by changing their power level
to a powerlevel that makes them unable to send events. Yes this does come at the cost of rapid PL churn
that is why MSC_DAG_MUTE exists to address this. That MSC will define how room level mutes are affected.

When applied towards a user on a homeserver level the homeserver can make the user read only. This is
effectively a lesser punishment than a deactivation since they can still access data cant just spread
problematic information.

Now as noted earlier these are only recommendations as to how you can implement the `m.mute` recommendation.

## Potential issues

Currently identified potential issues include. Causing state resolution to become more intensive due to
causing a rapid growth in PL events being issued.

## Alternatives

There are few if any viable alternatives to doing this via Policy lists to achieve the goals of the MSC.

But the way this MSC recommends applying a mute is straight up inferior to MSC_DAG_MUTE way of doing it.
The MSCs in this MSC package are all not dependent on each other but are greatly enhanced by each other.

Now as for how to practically implement a mute the merits of preferring the approach taken in MSC_DAG_MUTE
are going to be discussed in that MSC.

## Security considerations

This MSC has no new security considerations for policy lists. But applying this MSC without the use of
MSC_DAG_MUTE will require that the applying party in the case of applying at a room level against a user
the issuance of new power level events. This is problematic due to the effects it has on the room state.
This is elaborated on in MSC_DAG_MUTE

## Unstable prefix

During the time this MSC is unstable `m.mute` is replaced with `support.feline.policy.recomendation_mute`

## Dependencies

This MSC builds on MSC_DAG_MUTE, MSC_EXPIRY and MSC3784 (which at the time of writing have not yet been accepted
into the spec).

It does not require any of these MSCs to be implemented but it works best when implemented together with the rest of these MSCs.

MSC_DAG_MUTE to heavily improve upon mutes, MSC_EXPIRY to make temporary mutes an option
and MSC3784 to help enable building better user experiences interacting with policy lists.