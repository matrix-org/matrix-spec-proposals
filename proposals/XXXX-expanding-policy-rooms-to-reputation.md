# MSCXXXX: Expanding Policy Rooms towards Distributed Reputation

The Matrix network and protocol are open. However, some users, rooms or servers (let's call them
"entities") may not play well together, which results in the necessity to kick, ignore or ban
entities from individual rooms, spaces or other groups of rooms. This happens in particular when
a user or an entirey homeserver adopt toxic behaviors, such as bullying or attempting to brigade
other users. As it turns out, kicking, ignoring or banning entities is a complicated task in
presence of federation. To aid with such actions, MSC2313 defines a vocabulary for storing,
publishing and sharing *recommendations* on entities, in particular banning.
Individual users, room or space moderators or even homeserver administrators may either issue
such recommendations or follow existing recommendations, in both cases letting clients/bots/homeservers
that implement this spec take the necessary actions.

In many cases, however, banning is too boolean. Actually deciding whether an entity should be banned
(or muted, or throttled, or any other possible recommendation) is something that may need to be decided
after taking into account several sources. For instance, a community may decide to adopt a policy
through which a user is banned from the entirey community if they behave as a troll on at least three
of their rooms. If they behave as a troll in a single room, they should perhaps get away with a warning,
or perhaps be muted for 15 minutes, etc.

To achieve this, we need two mechanisms:
- a mechanism to store, publish and share the *opinion* of a community (or a single user) on an entity;
- a mechanism to store, publish and share actual *actions* against an entity (such as kicking or muting).

The current proposal builds upon policies introduced in MSC2313 to serve as the former, letting
communities share their opinion of an entity as a number in [0, 100). Further tools may be developed
to take action against entities based on the collation of opinions.

We stress out that the Matrix network itself is neutral: it has no opinion on users or content. Different
communities are bound to have different opinions on entities. This mechanism is solely intended to simplify
writing tools that aid communities and individuals that trust each other's judgement help protect each other
against entities that they judge malicious or toxic to their own well-being.

## Proposal

MSC2313 defines `m.policy.rule.<kind>` state events, as follows:

```jsonc
{
    "type": "m.policy.rule.user", // Or `m.policy.rule.server` or `m.policy.rule.room`.
    "state_key": "rule_1",        // Arbitrary.
    "content": {
        "entity": "@alice:example.org",
        "recommendation": "m.ban",
        "reason": "undesirable behaviour"
    }
},
```

We expand this to:

```jsonc
{
    "type": "m.policy.rule.user", // Or `m.policy.rule.server` or `m.policy.rule.room`.
    "state_key": "rule_2",        // Arbitrary.
    "content": {
        "entity": "@darthvader:example.org",
        "recommendation": "m.opinion",
        "opinion": 5,
        "reason": "keeps trying to get other users to join the Dark Side, whatever that is"
    }
},
```

We expand the `enum` `recommendation` with a new value `m.opinion`. This value states that the
policy states an opinion published by its issuer.

We expand the `content` with a new field

| Field     | Type | Description |
|-----------|------|-------------|
| `opinion` | Integer in [0, 100) | A subjective opinon on the behavior of the entity. A value of `0` represents an extremely poor opinion, while a value of `100` represents an extremely favorable opinion. |

Tools are free to mix and match `opinion`s from different *sources that they trust* to come up with a
decision on e.g. whether an entity should be allowed in a community.

## Potential issues
### Conflicting Opinions

Two different communities may very well have very different opinions on an entity. That is
actually not an issue but rather a feature. If these communities cannot trust each other's
judgement, perhaps because they share different worldviews, they should not attempt to use
each other's published opinions.


### Malicious Gossip

A malicious community Marvinites may use this mechanism to publish negative opinions on
user Alice, attempting to poison the perception of Alice among the community of Bobites.

As above, the solution to this is to realize that another Marvinites and Bobites have different
opinions and that Bobites should not use the opinions published by Marvinites.


### Accidental Snitching

The community of Alicites may publish a positive opinion on users that they appreciate. If,
however, the activities of Alicites are illegal in some regions, authorities may decide to
use the opinions published by the Alicites to try and locate users friendly to Alicites.
Similarly, a malicious group of Marvinites may use the opinions published by the Alicites
and use it as a base for online bullying.

The fact that apinions are stored and shared within Matrix rooms can help to some degree,
as Matrix rooms may be configured to require invites. If Alicites and their sympathizers
are in a position to be prosecuted or bullied, they may use this mechanism to restrict
access to opinions to users that they trust sufficiently.

Another consideration is that Alicites may need to restrict themselves to only publishing
negative opinions, rather than both positive and negative opinions.


### Thought Bubbles

By subscribing to a community's opinion feed, a user may end up restricting their worldview
to that of their community, as is already illustrated by a number of existing social networks.

However, existing social networks typically create these bubbles through a form of black box
analysis. By opposition, the mechanism of opinions can be audited. Further, tools can be built
e.g. in Matrix clients to let users investigate the opinions they follow, tweak them,
deactivate them.

## Alternatives

Alternative solutions have been proposed to combat online toxicity. However, these solutions
typically require a large/complete loss of privacy.

We expect that by decentralizing opinions and putting them in the hands of communities and
individual users, we will help demonstrate that such proposals are unnecessary.

## Unstable prefix

During prototyping, `m.opinion` will be prefixed as `org.matrix.mscxxxx.opinion`.
