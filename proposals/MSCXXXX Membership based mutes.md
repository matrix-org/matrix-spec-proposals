# MSC0000: Membership based mutes WORKING TITLE

## Introduction

As covered in in MSC_POLICY_MUTE currently in matrix mutes are done via powerlevel manipulation.
This MSC has the simple purpose of defining a path forward that alleviates this problem. Yes it does
require a room version bump but this MSC will explain why this is an acceptable compromise.

To achieve Mutes via membership a new membership state is proposed of `muted`. It would allow you to
exclusively send EDUs and no PDUs.

## Proposal

This proposal defines the `muted` membership type. If a user has this membership type in a room they
are restricted to exclusively sending the read marker EDUs and nothing more.

The legal transitions for the `muted` membership type based on Room version 10 would be
`join` -> `muted` -> `ban`,`join`

When a users membership is `muted` they may leave the room by setting their own membership to `ban`
this transition ignores power levels and instead behaves as if it was a leave. But if the person tries to
re-join the room they will be banned the same way as anyone else. The reason for going this way is simple.
It preserves your ability to leave a room while your muted but you cant return without the moderators of the
room desiring you to have the ability to return.

This also solves the issue of forcing implementations to break the matrix tradition and evaluate not just
the previous membership state but 2 membership states back to determine if its legal or not that would have been
required to enable leaves.

An exception to the earlier mentioned restriction that you cant send PDUs and EDUs except read markers
is that you can send a membership event that changes your membership from `mute` to `ban`.

## Potential issues

_Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example._

Someone is going to have to spend the time to figure out what the template should actually have in it.
It could be a document with just a few headers or a supplementary document to the process explanation,
however more detail should be included. A template that actually proposes something should be considered
because it not only gives an opportunity to show what a basic proposal looks like, it also means that
explanations for each section can be described. Spending the time to work out the content of the template
is beneficial and not considered a significant problem because it will lead to a document that everyone
can follow.

## Alternatives

The alternative of staying with our current Mutes as PL way has been dismissed as undesirable due to the
scaling issues. And also for the fact that it makes state resolution complexity grow at a faster rate
due to that powerlevels have to all be resolved always.

Going the path of RBAC or another powerlevels overhaul was also dismissed because this MSC intends to in
a perfect world be able to be implemented quite quickly in a vacuum that is not tied to any other MSC.

## Security considerations

The `muted` membership type is going to be yet another thing that you can mess up implementing and that is
recognised as an ok. The authors of this MSC believes that is an acceptable compromise since we avoid
the PL churn of current mute implementations. We also believe that the potential issue of being trapped in
rooms is mitigated by making self bans an option to mitigate the potential to bypass a mute fully by leaving
the room.

## Unstable prefix

_If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal._

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).