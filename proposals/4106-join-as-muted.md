# MSC4106: Join as Muted

## Introduction 

Currently Matrix lacks the ability to implement proper membership screening mechanisms. This is
due to being unable to use power levels based screening, see
[MSC3909](https://github.com/matrix-org/matrix-spec-proposals/pull/3909) and
[MSC3907](https://github.com/matrix-org/matrix-spec-proposals/pull/3907) for a description of
the problems.

This proposal aims to by extending MSC3909 solve this problem as membership screening is a function that
is desired by some end users. Stakeholders like The Draupnir Project that the Author does participate
in can not proceed to solve these end user concerns in a satisfactory manner without mechanisms like
those that this proposal enable.

This Proposal resolves this problem by introducing a mechanism where all join rules flip from transitioning
membership to `join` from a previous state like `leave`,`invite`,`knock` or not having a membership at all to `mute`.

The idea with this being that if you join a room as muted you cant interact in a race condition way where
you get to fire of spam before automatic tooling mutes you pending membership screening.


## Proposal

A room that uses Join as muted operating mode will put a `default_membership` key in its `m.room.join_rules`
this key can only for now contain either `join` or `mute` as its state to indicate normal or altered operating
mode. If this is missing from the event normal behaviour is assumed. 

When `default_membership` equals `mute` trying to will instead of setting your membership to `join` will set it
to `mute` with a special consideration being that if you do not have a previous membership event, you are allowed
to set profile information. This is to make it so you have valid profile information for your initial join as muted
members are not allowed to update profile information usually to avoid an attack vector.

To be written. Proper list of all the transitions in detail.

### Authorisation rules.

To be written. Contributions welcome. (Please note that this MSC builds on MSC3909)

## Potential issues

This MSC comes with the disadvantage of even further complicating membership transitions than they are already.
The author dismisses this concern due to that this is the only viable to the author way of implementing this feature.

## Alternatives

All existing RBAC MSCs at the time of writing that the author is aware of have been dismissed due to them
all sharing the flaw of that you cant Access Control a unbounded amount of members like membership based
access controls can do. And as for the why not just mute them on join issue that is described earlier.

Also the alternative of making `default_membership` be a different but Boolean key was not picked as to
enable this mechanism to be extended in the future without causing client side stakeholders to be confused.
This design choice encourages being adaptable to that this can change in the future and therefore avoiding
a v11 situation. (Room version 11 caused Element iOS to crash when trying to open a v11 room.)

A separate state event was dismissed due to that it makes the most sense to put this in the join rules to the author.
This is a weak alternatives case the author does recognise and is therefore left open as a possible alternative for now.

Knocking on rooms as an alternative has been dismissed by the author due to that it requires the solving of peeking over
federation to enable you to view the room contents before you attempt to pass membership screening. It also is not a viable
alternative for rooms that want to have members only membership due to wanting to give all users the ability to see 
what users have access to their messages when no server or user is acting in bad faith. Services like view.matrix.org existing
shows how world readable history visibility is not acceptable to force users into just to enable Screening of members while
maintaining read only mode as a capability. 

## Security considerations

Alternatives section does go into Security Considerations a bit and so does this proposals Relatives in MSC3909 and MSC3907
when it comes to mutes so lets dig into what this MSC does for security. It should do relatively little to worsen
security as all it does is make it so someone who joins the room is muted instead and therefore blocking the 
attack vector of racing with the automatic tool that mutes you to enable membership screening. Membership screening
being the flagship usecase for this specific MSC. 

Now yes this MSC does worsen security by adding even more complexity to the already very complex membership state machinery
enabling more ways of screwing that up.

## Unstable prefix

This MSC is not recommended to be implemented before Authorisation rules are properly specified but if implemented. Please use the version string of `support.feline.mute.msc3909+msc4106.v0`

Once Authorisation rules are specified it's expected that the unstable version after that is v1. This is because the pre authorisation rules properly written down version cant be trusted to interoperate and this is why its NOT recommended to implement a version that is based on this MSC before that section is written.

## Dependencies

This MSC builds on MSC3909 as a direct dependency on it (which at the time of writing have not yet been accepted
into the spec).
