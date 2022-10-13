# MSC0000: Membership based mutes WORKING TITLE

## Introduction

As covered in in MSC_POLICY_MUTE currently in matrix mutes are done via powerlevel manipulation.
This MSC has the simple purpose of defining a path forward that alleviates this problem. Yes it does
require a room version bump but this MSC will explain why this is an acceptable compromise.

To achieve Mutes via membership a new membership state is proposed of `mute`. It would allow you to
exclusively send EDUs and no PDUs.

## Proposal

This proposal defines the `mute` membership type. If a user has this membership type in a room they
are restricted to exclusively sending the read marker EDUs and nothing more except leaving via setting
their membership to `ban` as defined later.

The legal transitions for the `mute` membership type based on Room version 10 would be
`join` -> `mute` -> `ban`, `join`, `leave`(Exclusively via kick)

When a users membership is `mute` they may leave the room by setting their own membership to `ban`
this transition ignores power levels and instead behaves as if it was a leave. But if the person tries to
re-join the room they will be banned the same way they would be if someone else sent a valid ban. 
The reason for going this way is simple. It preserves your ability to leave a room while your muted 
but you cant return without the moderators of the room desiring you to have the ability to return.

This also solves the issue of forcing implementations to break the matrix tradition and evaluate not just
the previous membership state but 2 membership states back to determine if its legal or not that would have been
required to enable leaves.


### Authorisation rules.

To be written. Contributions welcome.
## Potential issues

On the potential issue that this MSC requires rooms that want to employ it to be created after the room version
its included in becomes default or their homeserver makes it default or they manually select it for an upgrade is
deemed acceptable. The reason this is deemed acceptable is because as has been made clear in discussions with
community moderation teams for multiple communities not all communities want to use mutes in their toolkit and therefore
not all communities will feel the need to upgrade their room version to gain access to this feature. 

Room version upgrades them self's are being worked upon making more smooth. There is work in the area of deleting state
for example that requires better room version upgrade mechanics. There is also history importing work being done as
another avenue of lessening the impact of room version upgrades in the future. 

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
the PL churn of current mute implementations. We also believe that the potential issue of being trapped in
rooms is mitigated by making self bans an option to mitigate the potential to bypass a mute fully by leaving
the room.

## Unstable prefix

This MSC is not recommended to be implemented before Authorisation rules are properly specified but if implemented.
Please use the version string of `support.feline.mute.mscAAAA.v0`

Once Authorisation rules are specified its expected that the unstable version after that is v1. This is because the
pre authorisation rules properly written down version cant be trusted to interoperate and this is why its NOT recommended 
to implement a version that is based on this MSC before that section is written. 

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).
