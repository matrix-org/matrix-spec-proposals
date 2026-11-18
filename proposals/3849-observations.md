# MSC3849: Observations.

Matrix policy rooms have seen some problems in their use. 

1) Trust. Communities are hesitant to watch (subscribe) to each other's
   policy rooms as implementations of policies take any policy rule from
   the list and enact them as a direct instruction.
   Not only is this a problem for trusting the list curators but also trusting
   that there is not a hostile take over.

2) Classification of bans. There is no way to classify or provide context
   for the ban other than using the free-form *reason* field.
   Communities have resorted to using several lists to indicate the severity
   of bans or the issue.

## Proposal

We propose two new events (and possibly a third) for policy rooms.
These can then be shared with confidence in a filtering system which
determine what actions should be taken based on the observations and
your own reinforcement of watched policy lists.

### Observations

Policy rules currently introduce a recommendation for an action to be
taken on a user (though, we are only aware of `m.ban` being used).

While the enforcement of policy rules are implementation dependent,
it is unclear how you selectively enforce rules from the same list
(when a list is being shared).
Rules themselves are used as a synchronisation tool to enact one set of
policies against an entity across a room, server or user.
For example adding a rule to `m.ban` `@evil:example.org` to my list
would be used by Mjolnir to synchronize that ban to a group of rooms.

We see the synchronization of bans as a separate concern to the sharing
of an observation.

In order to warn the wider community about `@evil:example.org`'s behaviour
we have to recommend they also have to be banned, and existing tools will
take the recommendation directly as soon as they are aware of a rule.

Instead we propose sharing observations.

```
  "content": {
    "entity": "@alice:example.org",
    "observation": "spam",
    "observed_server": "example.org"
  },
  "type": "m.policy.observation.user"
```

We're undecided on whether to propose an observation for an event
but in cases where the observation is about an action or
something an author is associated with we propose linking
to them with an `observed` and `observed_server` field.
This is so that you can get a general idea of the content
being created by a user/server without depending on
direct observations. It also makes auditing and trailing
a decision a little easier.


```
  "content": {
    "observation": "spam",
	"entity": "$w23r0932ir:foo.net"
    "observed": "@alice:example.org",
    "observed_server": "example.org"
  },
  "type": "m.policy.observation.event"
``` 

Observations can be made about any entity in the same way as policy rooms.


It's generic to all kinds of entities and gray. You can make positive
or negative observations.

The `author` and `author_server` fields are added to make lookup of observations
about entities created by one user or server easier.


### Labels to provide Context (This one is a maybe)

Labels are used to provide context for an observation.

It is expacted that most observations will be common,
though we provide a means for them to be extended.

```
    "content": {
      "label": "moderation",
    }
```

```
    "content": {
      "label": "spam",
      "parent_room": "!this:example.org",
      "parent_label": "moderation"
    }
```

alternatively you can just standardise the set of labels (boring).

### Reinforcement of Observations

We propose a reinforcement system so that users can mark whether they
agree or disagree with observations. 

Reinforcement can also actually just be done with the same observation
system, but meh.


```
{
  "content": {
    "observation": "$event_id",
    "policy_room": "$room_id",
    "reinforcement": "agree",
  },
  "type": "m.policy.reinforcement",
  "state_key": "$event_id(maybe?)"
}
```

 
## Potential issues

### Directory of abuse

The categorisation of entities (in the case of combating abuse) can
create a problem where your banlist becomes a directory that can be used
by bad actors to locate content.
This is a problem if you are distinctly catagorizing entities as providers of
harmful content such as CSAM.
We recommend keeping observations of an extreme nature as ambiguous
as possible in order to avoid this.

Other ways to tackle this problem might involve hashing the entity
e.g. the user id or the media id of content (though I am stressing at
this stage we are not proposing observations on media).

Each entity has to be considered differently if hashing of identifiers
is used as the hashes can be attacked differently depending on how they
are derived.
For example hashing of a user's mxid is vulnerable to a kind of table
generation where someone who is in in a lot of public matrix rooms can
they can very likely map a large mxid space into a table
(as there are relatively few matrix ids).

Using salts unique per entry may make problems like this computationally
harder to solve, but this also means that using the ban list becomes
computationaly expensive too e.g. we now have to create
`subscribedBanlists.map(entries).length` number of hashes per user we
want to test for a match ourselves.
Help would be appreciated in other solutions here though if there
is something simpler.

It could be decided that even if hashing identifiers is understood to
be flawed, it might be better than nothing at all.
It does take resources or a trip out of Matrix to be able to view a
complete recovered ban list.
Though it could be argued it is safer not to create a false sense of security.

### Privacy

Making observations and sharing observations about users or their activities
(rooms, events) can be privacy invasive.
MSC3845 [describes](https://github.com/matrix-org/matrix-spec-proposals/blob/76700eec9693d72923aa1326ca64640c4ba7d9d1/proposals/3845-expanding-policy-rooms-to-reputation.md?plain=1#L139) this approach as

>a large/complete loss of privacy.


Steps can be taken to restrict how far observations are spread
(e.g. making policy rooms knockable rather than public) but this
doesn't seem satisfactory.
Hashing identifiers might also help here but suffers from the same
problems described in "Directory of abuse".

Within the context of moderation there may be an avenue to argue
observations are an essential function to running a community, but this
observation system is general and this doesn't feel great either.


## Alternatives

- Hashing identifiers.
- MSC3845 whereby you essentially decline to make an observation on
  the user and instead rate them in an ambiguous contextless way.
  This means you don't need to worry about the privacy and directory of
  abuse issues this proposal has.
  It does have the drawback that there is no context for an opinion and
  therefore you have to trust the curator's opinion in all contexts.

## Security considerations

See issues.

If advanced filtering systems are later used using the data provided in
this proposal, it may be possible to farm positive observations and influence,
agreement to create malicious observations (to get someone banned).
Though, these can be defended against in some capacity by making sure
positive observations are also made about entities that you do like.

## Unstable prefix

* `m.policy.observation` => `org.matrix.msc.3849.observation`
* `m.policy.reinforcement` => `org.matrix.msc.3849.reinforcement`
* `m.policy.label` => `org.matrix.msc.3849.label`


## Dependencies

None afaik.
