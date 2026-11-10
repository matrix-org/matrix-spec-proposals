# MSC3909: Membership based mutes

## Introduction

As covered in in MSC3907 currently in matrix mutes are done via powerlevel manipulation.
This MSC has the simple purpose of defining a path forward that alleviates this problem. Yes it does
require a room version bump but this MSC will explain why this is an acceptable compromise.

To achieve Mutes via membership a new membership state is proposed of `mute`. It would allow you to
exclusively send Read markers and exempt events as defined later.

A passive benefit of this MSC that is notable is that with the introduction of Partial joining of rooms the minimum
state to join said room is important. As far as the authors understand this state is obligatorily going to be
negatively effected by PL events climbing in number. This MSC mitigates this and this is a real world
relevant example of why this MSC matters.
## Proposal

This proposal defines the `mute` membership type. If a user has this membership type in a room they
are restricted to exclusively sending receipts, leaving via setting

their membership to `leave-mute` as defined later and `m.room.redaction` events.

This proposal also introduces the new membership type of `leave-mute` this special membership
is set if a user leaves the room while their membership is `mute` this way you can still leave
rooms while muted without introducing a security flaw.

The legal transitions for the `mute` membership type based on Room version 10 would be
`join` -> `mute` -> `leave-mute`, `join`(Requires sufficient PL to set membership to `mute`), `leave`(Exclusively via kick),
`ban`.

The legal transitions for the `leave-mute` membership type based on Room version 10 would be
`mute` -> `leave-mute` -> `invite`(Requires sufficient PL to set membership to `mute` and to set membership to `invite`) , 
`leave-mute`, `leave`(Requires sufficient PL to set membership to `mute`) `ban`.

### Authorisation rules.

To be written. Contributions welcome.
## Potential issues

On the potential issue that this MSC requires rooms that want to employ it to be created after the room version
its included in becomes default or their homeserver makes it default or they manually select it for an upgrade is
deemed acceptable. The reason this is deemed acceptable is because as has been made clear in discussions with
community moderation teams for multiple communities not all communities want to use mutes in their toolkit and therefore
not all communities will feel the need to upgrade their room version to gain access to this feature. 

The UX around room version upgrades is being worked upon to make them less disruptive. There is work in 
the area of deleting state for example that requires better room version upgrade mechanics. There is also history importing 
work being done as another avenue of lessening the impact of room version upgrades in the future. 

The authors of this MSC believes that communities that desire to use this MSC to its full potential are perfectly happy
to accept the compromises involved in a room version bump. This MSCs purpose can be achieved via powerlevels 
in earlier room versions. This comes at the cost of a skyrocketing state resolution complexity but this is always
an option for communities that don't want to upgrade their room version or if this MSC fails.

The authors of this MSC are not aware of any other potential issues that have not been covered elsewhere in this MSC.

## Alternatives

The alternative of staying with our current Mutes as PL way has been dismissed as undesirable due to the
scaling issues. And also for the fact that it makes state resolution complexity grow at a faster rate
due to that powerlevels have to all be resolved always.

Going the path of RBAC or another powerlevels overhaul was also dismissed because this MSC intends to in
a perfect world be able to be implemented quite quickly in a vacuum that is not tied to any other MSC.

## Security considerations

The `mute` membership type is going to be yet another thing that you can mess up implementing and that is
recognised as an ok. The authors of this MSC believes that is an acceptable compromise since we avoid
the PL churn of current mute implementations. The ability to bypass a mute by leaving the room is mitigated
by the `leave-mute` membership type while still allowing full normal functionality except for re-joining a room via invite
as muted.

Because redactions are exempt from Mutes for privacy reasons this does re open the exploit that is closed by denying profile
updates on paper. This exploit does not in practice get reintroduced to any large degree as clients don’t render redact
reasons. And it is recommended that stakeholders that are worried about this abuse path use clients that render so called hidden
events so you can see the redactions to observe if they have suspicious patterns. 
## Unstable prefix

This MSC is not recommended to be implemented before Authorisation rules are properly specified but if implemented.
Please use the version string of `support.feline.mute.msc3909.v0.2`

Once Authorisation rules are specified it's expected that the unstable version after that is v1. This is because the
pre authorisation rules properly written down version cant be trusted to interoperate and this is why its NOT recommended 
to implement a version that is based on this MSC before that section is written. 

## Historical Prefixes

`support.feline.mute.msc3909.v0` was the prefix for the first iteration of the MSC. This prefix was for when self banning
was included.

`support.feline.mute.msc3909.v0.1` was the prefix for the second iteration of the MSC. This prefix was current before
the bug that ban was omitted from the transitions was fixed and redactions are now legal for muted parties to issue.

## Dependencies

This MSC builds on MSC3907, MSC3908 and MSC3784 (which at the time of writing have not yet been accepted
into the spec).

It does not require any of these MSCs to be implemented but it works best when implemented together with the rest of these MSCs.

MSC3907 to coordinate mutes via policy list, MSC3908 to make temporary mutes an option when coordinated via policy lists
and MSC3784 to help enable building better user experiences interacting with policy lists.
