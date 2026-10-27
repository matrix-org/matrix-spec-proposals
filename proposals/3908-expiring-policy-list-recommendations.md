# MSC3908: Expiring Policy List Recommendations

## Introduction

Currently in matrix there is no canonical way to specify a desire to have an action that is coordinated via policy
list to be temporary and expire.
This proposal gives a field to express expiry within Policies which we hope will improve the user experience.
We also believe expiry on policies will reduce the amount of attention maintaining lists requires,
as currently emulating an explicit expiry field to work with tools such as mjolnir requires manually
removing policies after the expiry date.

The means of getting to this goal are simple. The use of a new `"expiry"` key. This key will define
the point in time the recommendation is considered expired.

By letting entries expire we easily enable features like making temp bans, making a mute from MSC3907
temporary and other future policy recommendations can also be temporary.

## Proposal

To enable policies to expire an `"expiry"` field is used that contains a timestamp (in milliseconds since the unix epoch) 
for when the policy expires.
An expired policy should have its recommendation discarded and any existing effects reverted.

The `"expiry"` field is optional and if `"expiry"` is set to `0` it is equivalent to permanent.

Implementations are free to determine how they check for expiry..
It is important that consumers understand that a policy is deemed to have expired
once the expiry date is met from a subjective perspective.
While we expect that there won't be much disagreement about when a date has been met,
it is still somewhat likely disagreement can occur between clients, bots, server modules
about whether the date has been met, especially around the boundary of the date.

Below is an example recommendation to mute the user `@evil:example.com` with the help of MSC3907
this recommendation expires 1 hour after it was sent. The mute was sent at 2000000000. Now please note that the
only timestamp that matters is the expiry timestamp.

```
{
  "content": {
    "entity": "@evil:example.com",
    "reason": "spam",
    "recommendation": "m.mute",
    "expiry": 2003600000
  },
  "sender": "@mjolnir:example.com",
  "state_key": "_evil:example.com",
  "type": "m.policy.rule.user",
  "event_id": "exampleid",
  "room_id": "!policylist:example.com"
}
```

## Potential issues

##### Effects of federation lag

It is possible that the duration for which a policy is in effect can be reduced by the time taken
to propagate the event to servers (and their clients) in the policy room, from the perspective
of the client which sent it.
In an exaggerated example, a policy with a recommendation to mute an entity sent at 12:00 with the intention
to mute a participant for 15 minutes may take 1 minute to propagate to all of their moderation tooling.
This could mean that the policy only in effect for 14 minutes.


##### Temporal disagreement for tooling that works collaboratively

It is possible that if two (or more) bots are responsible for enacting a policy list over a set of
rooms that they can disagree about whether the expiry date of a policy has been reached.
This can lead to them applying and reverting each other's actions in conflict
until they agree.
If this proves to be a serious concern we suggest that tools send an acknowledgement of expiry
event with a relation to the policy to inform other tools that they are about to revert
the effects of a policy.

## Alternatives

##### DAG based expiry

There have been alternatives considered that attempt to introduce the concept of a temporary ban
directly into the DAG but these have been dismissed as completely insecure or easy to bypass.
It is clear to the authors of this MSC that the current consensus in parts of the community
is that introducing dependencies on time into the authorization DAG is a no-go.
In either case this MSC deliberately avoids the complexities of dealing with
servers having different temporal perspectives.

## Security considerations

As is mentioned previously we deliberately avoid trying to achieve a consensus on when
a policy has expires.
By allowing the party that applies a policy recommendation
to trust only their own perspective on what time it is we believe the MSC is secure.

## Unstable prefix

During the time this MSC is unstable `expiry` key is replaced with `support.feline.policy.expiry.rev.2`

### Historical Prefixes

`support.feline.policy.expiry` was the first prefix for this MSC and it was replaced when 0 was made
to equal permanent.

## Dependencies

This MSC builds on MSC3909, MSC3907 and MSC3784 (which at the time of writing have not yet been accepted
into the spec).

It does not require any of these MSCs to be implemented but it works best when implemented together with the rest of these MSCs.

MSC3909 to heavily improve upon mutes, MSC3907 to make mute via policy list an option
and MSC3784 to help enable building better user experiences interacting with policy lists.
