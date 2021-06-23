(a stream of incoherent consciousness from matthew which should go somewhere)

Invite-graph based reputation data:

* Users need a reputation score to issue invites or join public rooms.
* A user can have many reputation scores in different audiences (and perhaps a global average?)
* A room (degenerate case: user) can align itself with a given audience in order to consume the reputation data for that audience.
* The people that a user invites inherits a proportion of their reputation.
* If your reputation in an audience is ever reduced, it similarly reduces the reputation you have ever conveyed to anyone else (which propagates through the invite graph).
* Users increase reputation by:
  * Inviting someone.
  * Upvoting their messages in a room (i.e. for the suitability of that audience)
* Users decrease reputation by:
  * Blocking them.
  * Downvoting their messages in a room (i.e. for the suitability of that audience)

Need to ensure the accounts are of a decent quality - making it harder to create sockpuppet accounts and associating them with real people is more important than the actual reputation problem.

Build a war game simulation to test?


Problems:
 * How are audiences defined?  Just a given unique set of users?  Which then makes inheriting reputation easy between audiences - if the overlap is significant, the chances are the reputation rules are the same. 
   * But is it possible to have the same set of users in two different rooms have different rules for reputation?  Probably yes, as the potential audience may include future invitees or indeed the general public, so history visibility rules should probably also contribute to this.  But given privacy rules can change over time, each room should effectively define its own audience.  So in the end, an audience === a room.
 * Create a large network of fake users, and go and have them all vote up each other's score for a given audience.
   * This can be solved if the root inviter is penalised, which then destroys all the reputation they conveyed to their graph.

Could Reputation == Power Level (!?!?!)

Inheritence semantics for reputation between different audiences is hard.
  * You should base the reputation of a stranger on their reputation in other communities that you or your communities have some overlap with.
  * Do you consider 2nd hand reputation data at all from private rooms?  Or do you look only at the public reputation data?

How do you do these calculations in a byzantine world?

How do you do these calculations whilst preserving privacy?
  * Only consider reputation data from rooms you are actually in?
  * Store reputation data in room state?
  * Have a function (HS? client? AS? spider?) that aggregates reputation data (and proves that the aggregation is accurate, almost like blockchain mining?)?
  * Or have a separate reputation global db seperate from room state that people contribute metrics into (which gathers the aggregate data into a single place, and makes it easier to query reputation data for strangers)

How do you avoid backstabbing?  (People maliciously ganging up on someone to downvote them)?

How do you avoid a voting war?  (Community fragments; different factions turn up and try to downvote the other)?
 * This is effectively two different audiences emerging in a single room.
 * Perhaps this means we should model audiences separately from rooms.
 * Perhaps audiences are literally ACL groups?  And eventually, one might change the ACLs of a room to eject one of the groups?
 * Or do you just synthesise audiences based on cliques of people who support each other?  The act of upvoting someone is effectively aligning yourself as being part of the same audience?


So:
  * Gather all public upvote/downvotes/invites/blocks in a global DB.
  * Partition this into audiences based on who votes on who.  Stuff which is read and not complained about could provide a small implicit approval?  Although this makes it easy to flood content to boost your reputation, so bad idea.
    * Partitioning algorithm could be quite subtle.
    * You could end up with lots of small audiences (including invalid ones), and it's fairly unclear how they get aggregated into a single view.  How should you treat a stranger who you have no audience-overlap with at all?  Treat them as effectively having zero reputation from your perspective?

Problem:
  * If the douchebag who invites spammers never says anything, how do you go vote on their reputation?  Should there be some kind of back-propagation?  Or is there explicitly a "this person invited a douchebag" downvote?  Or hang on - how can they ever get reputation in the first place to invite their sockpuppets if they don't say anything (beyond the initial invite)?
  * What if users simply don't talk in public?  Is it right that we prevent them issuing invites just because they stick to private rooms?  What about inviting people into those private rooms?  I guess the point is that if these are public invites, then they need to have some kind of public reputation, or rely on out-of-band private invitation to establish trust?
  * Are we rewarding people who don't change their habits?  There's no time component considered here, and we punish people's entire history of invites and rep if they misbehave.  The only way to escape is to create a new identity atm.  Is this a feature or a bug?
  * How does this handle people's accounts getting 0wn3d and doing things which wipe out their reputation?  => This is always a risk; ignore it.
  * Do you need a particular level of reputation to be able to vote on people?

Summary?
 * Partition the global population into multiple overlapping clusters called 'audiences' based on mutual(?) upvote/downvote relationships in public rooms.
 * Clusters of the same people but in different rooms could be modelled as separate (but overlapping) clusters.
 * Each audience builds up a reputation score for the global population, blending in damped scores from overlapping audiences.
 * Anyone can upvote/downvote, but the votes will not contribute to your personal opinion unless the voter overlaps with your audience's scoresheet.
 * A room could adopt a given audience (that of the moderators'?) for considering the reputation of who can join, invite people, etc.
 * A user uses their own 'audience of one' scoresheet to put a threshold on filtering out contact from other users (invites, messages, etc).
 * Their personal scoresheet is presumably a blend of all the audiences they are already in.
 * The act of inviting someone gives them some reputation, within your audiences, proportional to your own.  Similarly blocking reduces reputation.
 * If you are downvoted, it retrospectively reduces the weight of all of your upvote/downvotes (at least for audiences that the downvoter's opinion contributes to).  Similarly for upvoting.
 * This penalisation process is transitive.

 Do we even need the penalisation stuff if audience partitioning works?
