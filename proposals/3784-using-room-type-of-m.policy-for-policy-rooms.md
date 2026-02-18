# MSC3784 Using room type of m.policy for policy rooms

## Introduction

This simple MSC aims to make it easier for machines and people alike to be made instantly aware if a 
room is a policy list. To facilitate this this MSC recommends using the already established `type` 
attribute to flag rooms as policy rooms. This builds upon the precedent set by Spaces and their 
`"type": "m.space"`. Adopting this for Policy rooms allows all stakeholders to instantly know if its 
a Policy room or not for rooms covered by this proposal. 

For the purposes of this MSC policy lists can at times be called a policy room. This MSC does not intend 
to change the name of the feature its just used to be very clear that we are talking about rooms with a 
specific usecase. 

## Proposal

This proposal is well quite simple. Allow for Policy rooms to be marked as such using the 
`"type": "m.policy"`. The precedent for this comes from Spaces where they introduced this system in a
limited capacity. This proposal expands this system to help all stakeholders quickly identify 
policy rooms in a machine compatible way that is computationally cheap. It has additional benefits like
allowing clients that are capable of editing policy to display editing tools for policy rooms when they
detect that a room is a policy room using this mechanic. For machine interaction with policy rooms this
proposal supplies a very fast way to tell if a room is definitively supposed to be a policy room or if 
the user might have supplied a legacy room or typed in the wrong room ID / alias depending on how things
are configured. 

Legacy rooms in this proposal are defined as all rooms that predate this proposal and they are free to upgrade
if they desire to but they are also free to stay on their current room version and not upgrade their
room to include a type event in the creation event. All stakeholders are expected to gracefully support 
interacting with legacy rooms until a future proposal changes this recommendation. 

The Author of this MSC believes that even with the problem of legacy rooms not being covered this MSC will
be useful in the future with more use of policy rooms. 


## Potential issues

As is covered in the proposal section this MSC has the potential issue relating to Legacy rooms.
The Author of this MSC thinks its that its an acceptable trade-off. 


## Alternatives

The alternative of using Peeking over fed to try to figure out if a room is a policy list has been
considered but considering that its currently considered at the time of writing to be a very in development
technology its deemed wholly unsuited for this application. The system this proposal recommends is the same
one that was used for spaces. Spaces have proven them self's in the real world and so has this system.

## Security considerations

None that the author is aware of at the time of writing due to the mostly informative nature of the data.
Due to that no client should trust that just because it says m.policy it is indeed a policy room the security
implications should be minimal.

## Unstable prefix

If you want to implement this MSC before its merged your free to use the unstable type of 
`support.feline.policy.lists.msc.v1`. 

After this MSC gets merged if a stakeholder has elected to remove its support for the unstable prefix if any
support existed or support never existed revert to Legacy room behavior for rooms that used the unstable prefix.

## Dependencies

The Author is not aware of any unstable MSC dependencies for this MSC.
