# MSC4073: Shepherd teams

Matrix currently has significant problems with its specification change process. There are several common complaints
from contributors:

1. "Nobody responds to my MSC"
2. "It takes forever to get an MSC passed"
3. "It's not clear what the status of my MSC is, or what I am supposed to do next"

From conversations with various Spec Core Team (SCT) members, all of these have (at least) one identical root cause:
the SCT does not have enough bandwidth to manage, review, and approve all of the submitted MSCs. This causes
communication to become minimal, and for MSCs considered "less critical" to languish and eventually become abandoned
by their authors, who often give up on Matrix protocol development entirely due to their bad experiences. The SCT
cannot be bypassed, because its final approval is required for any MSC to be considered mergeable.

## The current process

In the current MSC process, it is the responsibility of the SCT to manage the discussion and direction of every MSC,
and ultimately give its final approval before a merge is possible. A shepherd may be assigned to guide the MSC
process independently of the SCT - but they ultimately only serve the role of a *guide*, and do not hold any
authority over the final decision to merge or reject. A shepherd is also not required, and frequently is not
assigned. Altogether, this often leaves an impression with contributors of "appealing to a disinterested SCT".

## Proposal

This MSC aims to solve these problems, or at least make a first significant step towards doing so, by changing the
scope of responsibility of the SCT. It introduces the concept of a "shepherd *team*", and makes them primarily
responsible for the MSC's progress. This team is assigned on a *per-MSC* basis, and it is modelled after
[the "shepherd teams"](https://github.com/NixOS/rfcs/blob/master/rfcs/0036-rfc-process-team-amendment.md) in
[the NixOS RFC process](https://github.com/NixOS/rfcs#readme).

The new process will work as follows:

1. Community members submit nominations for shepherds, in the MSC's discussion thread. The nominees should be people
   who are closely familiar with the subject matter of the MSC, but not be the author. Community members may also
   nominate themselves.
2. The SCT selects multiple nominees to become the "shepherd team"; ideally 3 or 4 people.
	- The SCT may likewise nominate candidates (eg. if there are too few nominees), but should leave the opportunity
	  for other community members to object to the SCT's nominations.
	- No more than half of the shepherds may be SCT members.
	- The shepherd selection should avoid conflicts of interest, and be a diverse representation of perspectives on
	  the topic (within the boundaries of the Code of Conduct).
3. The shepherd team will be responsible for guiding the discussion on the proposal. This discussion should
   incrementally improve the proposal until outstanding concerns have been resolved. They may request administrative
   assistance from the SCT if eg. moderator intervention is required.
4. If the MSC proposes to standardize functionality that is already informally supported in one or more protocol
   implementations in a different form, the shepherd team should additionally reach out to the relevant implementation
   developers to notify them of the proposal, and to invite their review.
5. Once the shepherd team feels that all concerns have been resolved satisfactorily, and that there is no meaningful
   refinement left to be done, they can carry out a final technical review, and call FCP (Final Comment Period). Alternatively, if the shepherd team feels that the proposal is not salvageable, they may choose to reject it.
	- This requires unanimous agreement from all shepherds.
	- The SCT must be informed immediately by the shepherds when the FCP starts, so that the SCT can make a public
	  'last call' for feedback. Likewise, the SCT must be informed of a decision to reject.
	- The FCP process itself remains as it was before.
6. If FCP passes without objection, the shepherds declare the MSC accepted, and notify the SCT. The SCT will then
   merge the proposal.

Some of the most important takeaways from this:

- The SCT is no longer the final reviewer and approver; this responsibility is delegated to the shepherd team for
  that MSC.
- The shepherd team is trusted to ensure that:
	1. the proposal represents diverse interests, and
	2. the proposal does not conflict with other proposals, coordinating with shepherds for other MSCs if necessary.
- The SCT no longer concerns itself with the *content* of MSCs, but only with supervising the process.
- The SCT may still intervene where necessary to resolve administrative disputes, or replace shepherds if they become
  unavailable.

Throughout the process, the original author(s) remain responsible for updating the proposal in response to feedback,
as is currently already the case. If the author(s) wish to step back, they may - in agreement with the shepherd team -
choose to transfer this responsibility to the shepherd team (or another community member) instead.

These changes are a significant step towards a more community-driven protocol, by putting more of the specification
process in the hands of community members, and more crucially, it frees up significant capacity from the SCT.

This proposal does not currently encompass the question of "who writes the final specification text?" - that is left
unchanged from the current situation, and may be clarified or changed in a separate MSC.

### Tasks for the SCT

For the implementation of this proposal, the SCT will carry out the following tasks:

1. Develop guidance for shepherd teams, explaining their responsibilities and how to go about implementing these, as
   well as defining any additional circumstances under which the SCT should be notified. Particular attention should
   be paid to the topics of preventing burnout, and constructive conflict resolution.
2. Develop and publish guidance for the SCT itself, on how to select a representative shepherd team for a given MSC,
   and which concerns (eg. organizational distribution, diverse viewpoints) to take into account in their selection.

### Transitioning existing proposals

There is currently a large set of existing MSCs that is in some kind of stalled state. These are currently under the 
responsibility of the SCT directly, as that has been the process thus far. To prevent organizational chaos and to
account for the expected low initial availability of shepherds, it would be unwise to immediately transition all of
these proposals to the shepherd team model.

Instead, these proposals will be gradually transitioned; starting with languished proposals for which there is a known
"support base" of proponents and, conversely, a known interest in critical review. These can serve as the initial
testcases for this new policy, and it may even be worth starting this process experimentally before this MSC has been
fully accepted.

Drawing lessons from these initial experiences, the process can then be improved where necessary and, over time, be
applied to the remainder of the pending MSCs that were started under the old policy.

## Anticipated outcomes

Primarily, this should unblock the many MSCs that some community members feel strongly about, but that the SCT has
not had the capacity to advance, eg. because it accommodates a relatively specialized need. This should overall
significantly improve on the throughput and responsiveness of the MSC process, much like it has already done for
NixOS.

Indirectly, this would improve community trust and engagement regarding protocol development, because contributors
would no longer feel ignored, and they can continue building additional work on top of previous work - where that
previously would have been blocked on a 'stuck' MSC, and the uncertainty of it ever getting merged.

Another anticipated indirect effect is increased transparency in the specification design process; it is currently an
issue that a lot of specification design happens 'internally', behind closed doors, and this can currently be gotten
away with due to every MSC going through a central point of review (the SCT) before merging, where any 
incompatibilities can be ironed out.

In the 'shepherd team' model, this is no longer possible, as one cannot expect 'internal' and undocumented decisions
to be taken into account by other shepherd teams in their final review, and so all such specification development
*must* happen out in the open (as is ultimately desirable for an open protocol).

## Security concerns

It is *technically* possible for an organized effort to disrupt the specification by passing something without SCT
review. However, this has not been a problem for NixOS at all, and would require compromising the *entire* shepherd
team. Additionally, administrative intervention from the SCT remains possible in exceptional cases (like when a
shepherd has become unavailable), and this could likewise be applied to such cases.

## Alternative approaches

- __Scaling up the SCT:__ Organizations become more unwieldy as they try to scale up monolithically. Additionally,
  this requires more full-time commitments than anyone currently seems to be willing and able to fund, and would
  bring conflict-of-interest concerns with it. This does not seem viable.
- __Doing nothing:__ Increasing amounts of potential contributors are bouncing off Matrix due to the problematic MSC
  process, and it is well-documented that there are currently very few external contributions. This would likely lead
  to a slow death of Matrix as an open protocol.
- __Bigger MSC scopes:__ This would reduce the amount of units for the SCT to review and manage, but make changesets
  so large that the discussion of the implementation details would likely exponentially explode, making the problem
  worse on another axis.
