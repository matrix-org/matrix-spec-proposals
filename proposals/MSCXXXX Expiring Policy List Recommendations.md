# MSC0000: Expiring Policy List Recommendations

## Introduction

Currently in matrix if you desire to have an action coordinated via policy list be temporary you have
no canonical way to communicate this that is parsable by policy list parsers. This proposal aims to
change this. By giving Policy List entries the ability to expire we keep down the amount of events
we have to send and we also make it straight up more user friendly.

The means of getting to this goal is simple. The use of a new `"expiry"` key. This key will define
at what point the recommendation is considered expired. Further detail about this system is found in
the proposal section.

By letting entries expire we easily enable features like making temp bans, making a mute from MSC_POLICY_MUTE
temporary and other future policy recommendations can also be temporary.

## Proposal

To enable policy list entries to expire a `"expiry"` field will be added that contains a timestamp for
when the policy expires. An expired policy is to have its effects reverted if applied.

Implementations are free to determine how they do their expiry checking on applied recommendations.
A policy list recommendation is deemed expired once its expiry timestamp is reached from your perspective.

Policy list expiry is from your own perspective to make it so we can ignore issues related to distributed
accurate time.

Below is an example recommendation to mute the user `@evil:example.com` with the help of MSC_POLICY_MUTE
this recommendation expires 1 hour after it was sent. The mute was sent at 2000000000. Now please note that the
only timestamp that matters is the expiry timestamp.

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

## Potential issues

It is also deemed perfectly acceptable that if an recommendation for a mute that was at time of sending going
to be in effect for 5 minutes is only applied for 4 minutes because of the time it took to receive. This choice
was made because it makes it so we avoid the issues mentioned earlier. Its expected that realistic lag times
for recommendations to propagate is going to be measured in maximum of seconds so in the real world the effects
are usually quite minimal under normal conditions.

## Alternatives

There have been alternatives considered that attempt to introduce the concept of a temporary ban into the DAG
and these have been dismissed as completely insecure or easy to bypass. It is clear to the authors of this MSC
that the current consensus in the parts of the matrix community that understand the mathematics of state resolution
is that time and the DAG should be kept apart because its a very complicated problem to attempt to solve if
we can even solve it.

Going the direction of doing all this at the Policy application level means we avoid the complexities of
dealing with time in the DAG and since this is done at the applying parties own temporal perspective we avoid
all the issues of synchronisation of time and doing that in a way that we consider secure and decentralised.

## Security considerations

As is mentioned in multiple earlier sections this MSC tries its best to avoid the issues that normally comes
with dealing with time by making it so this MSC hinges on that the party that applies a policy recommendation
trusts their own perspective on what time it is. As long as you trust your own perspective this MSC is secure.

## Unstable prefix

During the time this MSC is unstable `expiry` key is replaced with `support.feline.policy.expiry`

## Dependencies

This MSC builds on MSC_DAG_MUTE, MSC_POLICY_MUTE and MSC3784 (which at the time of writing have not yet been accepted
into the spec).

It does not require any of these MSCs to be implemented but it works best when implemented together with the rest of these MSCs.

MSC_DAG_MUTE to heavily improve upon mutes, MSC_POLICY_MUTE to make mute via policy list an option
and MSC3784 to help enable building better user experiences interacting with policy lists.