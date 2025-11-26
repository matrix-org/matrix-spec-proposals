# MSC4384: Supporting alternative room directory sorting

The "room directory" for a server is made up of two endpoints: [`GET /publicRooms`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3publicrooms)
and [`POST /publicRooms`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3publicrooms).

Both endpoints state that the directory is sorted by "largest rooms first", which creates some
challenges:

1. Typically, a new user to a server will join the first 1-3 top rooms in the directory. On a server
   like matrix.org, this may mean the room(s) they're joining are not as relevant or applicable to
   new users.
2. Because of the above, larger rooms can also end up with higher proportions of spam because accounts
   will usually go top to bottom on the room list.
3. For servers which are centered around a community, "largest" may not represent that community's
   interests or needs best. A general chat may have low member counts, for example, but still be
   important enough to have at the top of the list.
4. In some cases, rooms are encouraged to fill themselves with bots or fake accounts to get higher
   standing in the room directory. This can be used to create harm that is hard to detect without
   a [moderated directory](https://matrix.org/homeserver/room-directory/).

This proposal removes the "largest first" requirement from both endpoints, allowing for implementation
specific sorting to happen. Though not specified in this proposal, implementations might be interested
in supporting a "pinned rooms" configuration option to ensure specific rooms remain at the top of the
room directory before sorting the remainder as "largest first" - this ensures that server-centered
communities can pin relevant rooms at the top and still have increased visibility on their remaining
rooms, though doesn't necessarily solve spam or abuse mitigations to the same degree.

## Proposal

Both the [`GET /publicRooms`](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3publicrooms)
and [`POST /publicRooms`](https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3publicrooms)
endpoints drop the "largest rooms first" requirement and instead say that sorting is an implementation
detail. The specification may wish to retain a recommendation to sort by largest first by default to
give server implementations some guidance on how to implement a basic room directory.

If servers choose a different sorting algorithm for the room directory, they will need to ensure that
the results are in a stable order for pagination to work. This may mean, for example, that "pinned"
rooms are put at the top of the total results list rather than each page of results delivered to the
client.

## Potential issues

Mentioned in the proposal, servers may implement sorting algorithms which are unstably sorted, leading
to confusing pagination results. This would be considered a bug in the implementation rather than a
bug in the spec (or a feature in the implementation if it's desirable for whatever reason).

Though highly unlikely, there may be a client in the wild which requires the results to be ordered by
size. By nature of how the endpoints are usually implemented, it's expected that most (if not all)
clients will simply show the results verbatim, unaware of any particular ordering to the rooms.

## Alternatives

It's possible that an MSC is not necessarily required to make this change. The room directory endpoints
were created and documented an eternity ago, and don't use explicit "MUST" or "SHOULD" language as a
result. This MSC is created to document alignment on changing the ordering algorithm for historical
purposes.

## Security considerations

Improving relevance in results can ensure that new users land in moderated rooms first instead of
large, potentially unmoderated, rooms. This improves the overall safety experience for users on the
public federation.

## Unstable prefix

Not applicable. The risk of breaking clients is exceptionally low, and namespacing the endpoints to
support a change in language feels excessive.

However, while this proposal is considered unstable, servers are encouraged to only change the order
when the administrator has explicitly indicated that they want to do that. This may be done by an
"experimental feature flag" or other server-specific configuration, for example.

## Dependencies

This proposal has no direct dependencies.
