# MSC3845: Expanding Policy Rooms towards Distributed Reputation

The Matrix network and protocol are open. However, some users, rooms or servers (let's call them
"entities") may not play well together, which results in the necessity to kick, ignore or ban
entities from individual rooms, spaces or other groups of rooms. This happens in particular when
a user or an entire homeserver adopt toxic behaviors, such as bullying, spamming or attempting to brigade
other users. As it turns out, kicking, ignoring or banning entities is a complicated task in
presence of federation. To aid with such actions, the Matrix spec defines [a vocabulary](https://spec.matrix.org/v1.3/client-server-api/#mban-recommendation) for storing,
publishing and sharing *recommendations* on entities, in particular banning.
Individual users, room or space moderators or even homeserver administrators may either issue
such recommendations or follow existing recommendations, in both cases letting clients/bots/homeservers
that implement this spec take the necessary actions.

In many cases, however, banning is too boolean. Actually deciding whether an entity should be banned
(or muted, or throttled, or any other possible recommendation) is something that may need to be decided
after taking into account several sources. For instance, a community may decide to adopt a policy
through which a user is banned from the entire community if they behave as a troll on at least three
of their rooms. If they behave as a troll in a single room, they should perhaps get away with a warning,
or perhaps be muted for 15 minutes, or lose the ability to post links and images, etc.

To achieve this, we need two mechanisms:
- a mechanism to store, publish and share the *opinion* of a community (or a single user) on an entity;
- a mechanism to store, publish and share actual *actions* against an entity (such as kicking or muting).

The current proposal builds upon policies introduced in MSC2313 to serve as the former, letting
communities share their opinion of an entity as a number in [-100, 100]. Further tools may be developed
to take action against entities based on the collation of opinions.

We stress out that the Matrix network itself is neutral: it has no opinion on users or content. Different
communities are bound to have different opinions on entities. This mechanism is solely intended to simplify
writing tools that aid communities and individuals that trust each other's judgement help protect each other
against entities that they judge malicious or toxic to their own well-being.

## Proposal

The Matrix spec [defines](https://spec.matrix.org/v1.3/client-server-api/#mban-recommendation)  `m.policy.rule.<kind>` state events, as follows:

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
        "opinion": -50,
        "reason": "keeps trying to get other users to join the Dark Side, whatever that is"
    }
},
```

We expand the **`enum`** `recommendation` with a new variant

| Variant | Description |
|---------|-------------|
| `m.opinion` | The current policy states an *opinion* on an entity. The `content` MUST have a field `opinion` (see below). |

We expand the `content` with a new field

| Field     | Type | Description |
|-----------|------|-------------|
| `opinion` | Integer in [-100, 100], optional | A subjective opinon on the behavior of the entity, where `-100` is the worst possible opinion and `+100` is the best possible opinion. This field MUST be present if `type` is `m.opinion`. |

Tools are free to mix and match `opinion`s from different *sources that they trust* to come up with a
decision on e.g. whether an entity should be allowed in a community.

### Opinion values

This MSC does not present any normative value for which actions should be undertaken. However, the intuition behind this MSC is that:

- `-100` represents an entity with a highly toxic behavior (e.g. a scammer, or a homeserver that hosts scammers and refuses to take measures against them), who should be permanently banned from any interaction with the user/community if possible;
- `+100` represents an pillar of the community (e.g. someone who has been a member of the community for a long time and routinely participates to defuse potential complicated situations), whose abuse reports should be taken seriously;
- any value between `-20` and `+20` is an average user/homeserver/room.

Individual communities are free to decide of the default `opinion` value for an entity for which no `opinion` has been published. In particular, some communities offering public joins may decide that new users start with a negative `opinion` and progressively gain positive `opinion` as they interact with the rest of the community.

Such policies are not meant to be specified as part of the Matrix protocol. Rather, we recommend that tools (e.g. moderation bots) be designed to explore this space.

## Potential issues
### Conflicting Opinions

Two different communities may very well have very different opinions on an entity. That is
actually not an issue but rather a feature. If these communities cannot trust each other's
judgement, perhaps because they share different worldviews, they should not attempt to use
each other's published opinions.

### Combining Opinions

This MSC does not specify how to combine opinions from two trusted groups. If group A assigns
an opinion of -20 to Marvin and group B assigns an opinion of -10 to Marvin, does this mean
that Marvin should have a total opinion of -30? -15?

We do not expect to specify this in the current MSC but rather in a further MSC down the line,
once the Matrix community has had the opportunity to experiment with opinions.

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

It is our hope that the mechanism of explicit opinions will actually help fight thought
bubbles.

## Alternatives

Alternative solutions have been proposed to combat online toxicity. However, these solutions
typically require a large/complete loss of privacy.

We expect that by decentralizing opinions and putting them in the hands of communities and
individual users, we will help demonstrate that such proposals are unnecessary.

## Unstable prefix

During prototyping, `m.opinion` will be prefixed as `org.matrix.msc3845.opinion`.
