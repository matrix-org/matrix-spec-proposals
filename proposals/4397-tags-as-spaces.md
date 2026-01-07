# MSC4397: Tags as Spaces

## Problem

We currently have two different APIs which both let users group their rooms together: Custom Tags and private Spaces.  
This doubles our maintenance burden for both client SDKs implementations, server implementations, and the spec itself.  
For instance, we end up having to address issues like API shape, room ordering, performance, geo-redundancy, metadata-footprint in two different ways in two different places, doubling effort and ending up with a big wart in the spec.

The situation is not dissimilar to the /groups misadventure, where we introduced an entirely new set of APIs for managing sets of rooms, before we realised that rooms themselves could be used to group rooms together (i.e. Spaces as per [MSC1772](https://github.com/matrix-org/matrix-spec-proposals/pull/1772)).  Replacing groups with spaces has generally been seen as a good thing; should we consolidate tags into spaces too?

## Proposal

We could define an account\_data key called `“m.tag_space”` which points to the room ID of a private space used to list subspaces of rooms which the user can use to tag their rooms.

The normal spaces API is then used to tag rooms within these subspaces.  Clients which aren’t aware of this MSC will display and manage it as a normal private space.  Clients which are aware may choose to display the `m.tag_space` space with custom UI \- e.g. by splitting the roomlist up into sections defined by the subspaces.

## Potential issues

* Custom tags already exist in the spec, and they work..  
* Clients already implement tags everywhere for Favourites & Low Priority  
* The benefits for client (and server) implementers are therefore small right now for moving to spaces, given they likely already have tag support implemented.  
* Changing space membership is currently ratelimited; for a good UX we’d need to special-case ratelimiting for private spaces, which then runs the risk of letting abusive users DoS the server with (relatively heavy) state events.  
* We’d want to do a coordinated ecosystem-wide migration of Favs & Low Priority over to the new space system

## Alternatives

* Keep the custom tags API, but instead benefit from future metadata privacy etc by backing account\_data as state events in an account\_data room in future, which may also be needed for multihomed accounts one day.  So we’d end up with tags-as-rooms at least, if not tags-as-spaces.

## Conclusion

This MSC has been opened as a tracker for this idea, but until spaces provide a significant benefit over account\_data (e.g. by protecting metadata) the suggestion is to keep using the Custom Tags API for this purpose \- and then migrate all tags (including favs & LP) over to spaces if/when the time comes.

## Unstable prefix

If anyone wants to experiment with this MSC, please use `org.matrix.msc4397.tag_space` as the account\_data key.