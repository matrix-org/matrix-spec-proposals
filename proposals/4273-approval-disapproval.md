# MSC4273: Approve and Disapprove ratings for moderation policies

Currently, when watching a moderation policy list, there is no way to express
approval or disapproval of certain policies.

Typically, Matrix moderation tooling requires that moderators accept all
policies within a moderation policy list in an all-or-nothing approach. We call
this profile of policy list subscription _direct propagation_: any policy that
appears on a watched list with _direct propagation_ semantics are directly
considered and actioned by tooling. Examples of this include Mjonlir & Draupnir.

For example: `charity`, the moderator of `cat-community.example.com`, cannot
subscrbe to the list, `#bat-coc-bl:bat-community.example.org` without accepting
all of the existing policies. This is problematic because `charity`'s friend
`bob` was banned from the list for arguing with a moderator. `charity` respects
the ban in the bat community, but still needs to be able to interact with their
friend.

Addtionaly, this all-or-nothing approach increases the amount of trust that
moderators place onto the curators of moderation policy lists. As watching a
list gives the list curators the ability to manage members within the
subscribing community.

For example: `luna`, the moderator of `bat-community.example.com` notices that
`cat-community.example.com` is watching the list, and uses their power to ban
more of `charity`'s friends.

These problems lead to situations where communities avoid watching other
moderation policy lists entirely, either because of a few policies that they
take issue with, or it is simply unsafe to do so because of the level of trust
placed on the curators of a list when watching them.

## Proposal

We introduce a new moderation policy meta rating event type,
`m.policy.rule.approval`. This policy exists purely for moderators to express
their approval or disapproval for policies in other lists.

Content Schema:

```yaml
properties:
  rating:
    description: |-
	  A binary rating of either string literals approve or disapprove.
    type: string
	enum:
	  - approve
      - disapprove
  event_id:
    type: string
    description: |-
      The event ID of the moderation policy that this is a rating for.
    example: "$some_event_id"
type: object
required:
  - rating
  - event_id
```

Example:

```json
{
  "sender": "@luna:bat-community.example.com",
  "type": "m.policy.rule.approval",
  "content": {
    "rating": "approve",
    "event_id": "$wioefjwoijefo:example.com"
  },
  "state_key": "lciRM4XTjq9bj3QMawAbXFH7pCRJEvft34ZmhGBNsxc="
}
```

### Discussion

These policies allow for moderation tools to develop _approval
only_[^approval-only] policy list subscription modes. Whereby policies are only
considered from a list when they have been approved by a moderator. Please note,
that due to the _lazy_ nature of matching, the workload on moderators for
approving policies when watching a list will be minimal[^minimal-workload].

Additionally, subscriptions that use _direct propagation_ can remove policies
from consideration that have been _disapproved_ by a moderator.

[^approval-only]: https://github.com/the-draupnir-project/planning/issues/4

[^minimal-workload]:
    They will only have to approve policies that are matching encountered
    entities. For example, there is no need to approve a policy banning a user
    that has not been encountered yet as they have not attempted to join any
    known room.

The examples given in this proposal have so far only considered the application
of these ratings to the room level. However In the future, if policy lists are
considered for consumption within clients for the purpose of blocking on a user
level, these ratings provide a fundamental primivive for a subjective
distributed reputation system.

## Potential issues

### Direct propagation of approval ratings

If moderation tools implement the proposal naively, it's possible that approval
ratings themselves can be considered alongside normal moderation policies. For
example, `charity` is watching the list `#bat-coc-bl:bat-community.example.com`
curated by `luna` with a _direct propagation_ policy list subscription profile.
`charity` is also watching the list `#people-i-hate:bat-community.example.com`
with an _approval only_ subscription profile. `luna` notices this, and approves
policies from `#people-i-hate:bat-community.example.com` within the
`#bat-coc-bl:bat-community.example.com` list. If `charty`'s tooling naively
propagates the approval ratings, then their tool will enact policies from
`#people-i-hate:bat-community.example.com`.

#### Mitigation

To prevent this, implementations SHOULD use an allowlist of senders when
considering `m.policy.rule.approval` ratings by default, rather than the
specifics of a policy list subscription profile.

## Alternatives

### Local storage

Approval ratings could be kept on local storage rather than in policy rooms.
However, this would reduce the potential for interoperation of different tools
and clients.

## Security considerations

See ptoential issues.

## Unstable prefix

The event type `m.policy.rule.approval` will use the unstable type
`org.matrix.msc4273.approval`.

## Dependencies

None
