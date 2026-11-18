# MSC3647: Bring Your Own Bridge - Decentralizing Bridges

# Background

Currently, on matrix, "Bridging" is something that is often done by a specific appservice, sitting
on either your, or someone else's homeserver.

This appservice would be the "gate" to whatever chat network is bridged at that point in time,
sometimes multiple networks at once, and would hold the "authority" to send messages through this
magical "wormhole" it has established with this other chat network.

Often, someone would like to "double-puppet" in a bridge room, this means that the user's account on
both sides of the bridge is able to be "puppeted", to be controlled, to give the illusion of
complete seamless interaction from "that" user on both sides of the bridge.

However, the above requires trust to the bridge operator, as it then has full control over your
account, both the one on Matrix, and on another chat platform.

This, together with the situation that a bridge is often operated by someone "else", can create
security risks if someone were or had to "log in" to the bridge's double-puppet feature on every one
it encounters. As a result, this disincentives double-puppeting on a federation level, and makes it
a feature only "reasonable" for local homeserver portal rooms, where the user wholly trusts and/or
owns the bridge that is running it.

# Proposal

This proposal aims to change that, by allowing bridges to "negotiate" who will bridge who.

This'll mean that bridges will have two roles, a bridge can be "hosting" a room, provide an
authoritative view on the room from the other platform (i.e. bridging for users who do not have
matrix accounts, or do not double-puppet), and a bridge can be "visiting", requesting the hosting
bridge to exclude events from a particular user on both sides of the room, to then step in and
provide those events itself.

This happens by the visiting bridge (who can observe a room being a bridged room with a
[MSC2346](https://github.com/matrix-org/matrix-doc/pull/2346) state event, "listening in" via the
puppeted user's sync) requesting the hosting bridge to "step aside", this happens via a DM in which
both bridge bots, over matrix, start an exchange to establish trust.

This exchange has two components;
- verifying that the VB (visiting bridge) has access to the attested user's matrix account.
- verifying that the VB has access to the attested user's bridged chat platform account (i.e. a
  telegram account).

Verifying the matrix user is relatively easy, this can be done by having the user send the response
to a challenge the HB (hosting bridge) sends to the VB, attesting that the bridge responded through
the user's account. This can be done by having the user open a DM with the HB, send a
to_device message, or to send a dummy event in the bridge room. (each have tradeoffs and considerations)

Verifying a platform account is tricker, as the bridged chat platform may not follow an exact format
as matrix does, may not allow sending messages directly to the HB "bridge bot" on that platform, or
simply has no generic method to have a user send a covert message to the HB bot.

The intention is that, once a VB has verified itself with one HB, it does not need to verify itself
again after the user joins another bridged room maintained by that HB, thus making this a one-way
exchange.

If the user wishes to switch bridges at any time, it does this by logging out of the old bridge, and
logging into a new one, after which that bridge verifies itself to every HB it sees. In this case,
the HB should proceed the verification as normal, but override its "trust status" it has from the
old VB to the new one.

*This proposal is WIP, the above describes the intentions and problems this solution would have,
technical specification will follow once a consensus is formed on how to proceed or solve above
problems.*

# Enabled features

## Decentralized Bridging

The first and primary usecase this proposal wishes to enable is, of course, the ability to "go
anywhere and bridge magically". That is to say; a user can join any room, and the VB will
automatically verify itself to the HB, enabling it to seamlessly double-puppet once/if the user
joins the other end of the bridge with its own user.

## Appservice-less bridges

With this proposal, a usecase where bridges become based on the regular CS API (as opposed to the
appservice API) can become a possibility, as bridges today are expected to maintain everything about
the room they're bridging to, including ghost users.

Thus, a user may only "have" a bridge to maintain a consistent identity across platforms. The
removal of the need for the AS API could move these bridges to remote spots, such as user-hosted
raspberry PIs, operating itself as a "normal" matrix user.

# Potential Issues

## Bridge Downtime

An obvious first issue when considering the above situation is one of; "What if the VB or HB is down?"

If either one bridge is down, then traffic to a bridged room halts, or is not forwarded to the
corresponding bridged chat.

Bridges today deal with this on a case-by-case basis, some bridges have configuration values to
backfill events from the chat platform to the bridged room, but some opt to only proxy live data, or
some choose a compromise, only backfilling the last X events.

This may cause a problem if the VB and HB cannot agree with eachother on how or what to backfill,
but this problem is largely overshadowed by the following one; What should the HB do once the VB
does not insert events "in time"?

The above may cause discontinuity in the room's timeline, with inserting events into the past not
being a viable (or even allowed) option, while
[MSC2716](https://github.com/matrix-org/matrix-doc/pull/2716) introduces methods to insert events
beyond the room's creation event, it does not provide methods to insert events in the middle of a
room, and this author questions if that should become a reality, considering the security
considerations it has.

If a HB is down, a VB posting "its" events in a HB-bridged room has the same problem, although
arguably with "more" breakage, instead of a subtle one.

This proposal does not aim to solve this issue, only provide a "happy path" for both bridges to
agree on, a suggestion for a future MSC resolving this is to allow the HB to "fill in" any missed
event on both sides of the bridge, while also notifying the VB about the events it has sent on "its
behalf".

## Multiple HBs

It is possible (albeit relatively rare) that a user might join two rooms, both of whom are bridged
to the same chat on another platform.

For this situation, this proposal suggests to have the VB verify itself with both bridged rooms
individually, as it may lessen ghost users in either bridged rooms.

## Multiple VBs for one user

Due to possible misconfiguration, a user may be logged into two bridges at any one time, both then
asserting verification for the user it wishes to bridge for.

This proposal doesn't concern itself with this problem, as it is a configuration issue with either
bridge, and non-actionable from the specification to rectify.

In such a situation as this, the user has to rectify the issue themselves, logging out from either
bridge.

## Joining a HB room while maintaining a personal portal room

It is plenty possible that a user joins a chat on a chat platform, while then discovering that this
chat also has a "canonical" room on matrix, and then subsequently joining it.

In this situation, the user's personal bridge may have created a portal room for the user while they
joined the chat on the chat platform. It then has a "dilemma" whenever it subsequently encounters a
bridged room for that portal room it just created.

The behavior for what happens after this is up for bridges to decide, but a suggested course of
action could be that the VB can decide to tombstone the portal room, pointing to the new bridged
room it saw, it should do this in case it was only maintaining this portal room for a single user,
or if all users it was double-puppeting have joined this one bridged room.

Note: care should be taken that this behavior should only apply for portal rooms specifically, as
in that these rooms are meant to be a view into the other chat platform for the puppeted users
alone. Some bridges blur the lines on this, but it could become dangerous if public portal rooms
were created, some random user might join, and it then suddenly tombstoning to a different room in
the federation.

## Decommissioned Bridge

A bridge might decommission itself, or otherwise become unable to be activated again. This can
happen for a myriad of reasons, but for the bridged user specifically, this may create the situation
of them suddenly being "invisible" to either side of the bridge.

This proposal does not aim to solve this issue, as it is largely similar to the "Bridge Downtime"
issue as described above, the above suggested solution of "stepping in" as long as the VB is
unresponsive could fix the issue for the bridged user, but a more fundamental problem is that the
bridged user has no generic way of signalling to the HB that the VB is unresponsive, and it wishes
to be bridged by the HB as normal.

The bridged user may be able to set themselves up with a new bridge, after which the new VB may
verify itself to all HBs it sees, overriding the previous trust establishment the HB had set up.

# Security Considerations

This proposal interacts with the complex security risks that a double-puppeting bridge gives. A
double-puppeting bridge intimately interacts with both user accounts, and users have to accept a
major risk trusting the bridge with this access.

That said, this proposal seeks to lessen the risk with using double-puppeted bridges on matrix, by
providing a method for bridges to be trusted, while interoperating with existing bridged rooms,
providing a smoother experience.

This proposal assumes that users already have trusted the bridge they're entering the room with, and
thus, no extra security risk is added, only removed, by having users be able to use their own
bridge.