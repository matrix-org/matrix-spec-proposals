# MSC3715: Add a pagination direction parameter to `/relations`

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) introduced the
`/relations` API to retrieve events which are directly related to a given event.

This API has been used as basis of many other features and MSCs since then, 
including threads.

Threads was one of the first usages of this API that allowed nested relations -
an event may have an m.reaction or m.replace relation to another event, which 
in turn may have an m.thread relation to the thread root.

This forms a tree of relations, which is necessary for clients to retrieve to
be able to correctly display threads and determine the latest event of a thread
to be able to correctly send read receipts and determine the thread's 
unread status.

## Proposal

It is proposed to add the `recurse` parameter to the `/relations` API.

> Whether to recursively include all nested relations of a given event. 
>
> If this is set to true, it will return the entire subtree of events related
> to the specified event, directly or indirectly.
> If this is set to false, it will only return events directly related to the 
> specified event.
>
> One of: `[true false]`.

In order to be backwards compatible with MSC2675 (and Synapse's legacy 
implementation), the `recurse` parameter must be optional (defaulting to 
`false`).

Regardless of the value of the `recurse` parameter, events will always be 
returned in the same order as they would be by the `/messages` API.

If the API call specifies an `event_type` or `rel_type`, this filter will be
applied to nested relations just as it is applied to direct relations.

## Potential issues

Naive implementations of recursive API endpoints frequently cause N+1 query 
problems. Homeservers should take care to implementing this MSC to avoid 
situations where a specifically crafted set of events and API calls could 
amplify the load on the server unreasonably.

## Alternatives

1. Clients could fetch all relations recursively client-side, which would 
   increase network traffic and server load significantly.
2. A new, specialised endpoint could be created for threads, specifically 
   designed to present separate timelines that, in all other ways, would
   behave identically to `/messages`

## Security considerations

None.

## Unstable prefix

Before standardization, `org.matrix.msc3981.recurse` should be used in place
of `recurse`.
