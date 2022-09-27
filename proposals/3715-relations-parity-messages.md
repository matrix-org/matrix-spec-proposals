# MSC3715: Add a pagination direction parameter to `/relations`

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) introduced the
`/relations` API as an endpoint to paginate over the relations of an event. Unfortunately,
it is missing a `dir` parameter which is necessary to properly load thread timelines
at an arbitrary location.

Consider a long thread (e.g. consisting of 300 events), if a user receives a link
to an event somewhere in the middle it is desirable for the client to only display
a few dozen messages: the event itself and some context before and after it. As
the user scrolls additional content from the thread should be fetched.

Currently clients are forced to fetch *the entire thread* until the target
message (plus any surround context) is reached in order to implement this
functionality. A simpler implementation would allow the client to:

1. Load events in a thread backwards from a pagination token,
2. Load events in a thread forwards from a pagination token,
3. Load context around an event.

1 & 3 are currently possible; this MSC attempts to solve condition 2.

With the `dir` paraemter on `/relations, it now becomes possible for a client to:

1. Call `/context` on the target event to get a pagination token.
2. Call `/relations` twice (once with `dir=b` and once with `dir=f`) on the same
   pagination token to collect any contextual events.
3. Store the resulting pagination tokens to paginate further, if necessary.

This allows the thread to be fetched in arbitrary chunks:

```mermaid
flowchart RL
    subgraph /relations?dir=f
    $2-->$1
    end
    $1-->$0
    subgraph /context/$0
    $0
    end
    $0-->$-1
    subgraph /relations?dir=b
    $-1-->$-2
    end
```

## Proposal

It is proposed to add the `dir` parameter to the `/relations` API for parity with `/messages`.
It will [have the same as definition as for `/messages`](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomidmessages),
which is copied below:

> The direction to return events from. If this is set to `f`, events will
> be returned in chronological order starting at `from`. If it is set to `b`,
> events will be returned in *reverse* chronological order, again starting at `from`.
>
> One of: `[b f]`.

In order to be backwards compatible with MSC2675 (and Synapse's legacy
implementation), the `dir` parameter must be optional (defaulting to `b`). This
differs from the specification of `/messages` where the `dir` parameter is
required.[^1]

Including the `dir` parameter will make it easier to request missing relation
information without needed to paginate through known information -- this is
particularly needed for mobile or low-bandwidth devices where it is desired to
keep the round-trips to the server to a minimum.

It is additionally useful to unify similar endpoints as much as possible to avoid
surprises for developers.

Since this endpoint can now be used to paginate backwards over children events,
it is also useful for the `from` parameter to accept `prev_batch` values from
previous calls (as well as `next_batch` values, as is currently specified). The
[definition of the `from` parameter](https://spec.matrix.org/unstable/client-server-api/#get_matrixclientv1roomsroomidrelationseventid)
is updated:

> Can be a `next_batch` token **or `prev_batch`** token from a previous call, or a
> returned `start` token from `/messages`, or a `next_batch` token from `/sync`.

(Bold indicates new text.)
## Potential issues

`/messages` does have one additional parameter (`filter`) which would still not
be implemented for `/relations`. It is unclear if this parameter is useful here.


## Alternatives

The endpoint could be replaced with the `/event_relationships` API proposed in
[MSC2836](https://github.com/matrix-org/matrix-doc/pull/2836). That API would
add significant complexity over the current `/relations` API (e.g. arbitrary
of relations) and is not necessary to simply iterate events in the reverse ordering.

Instead of having a different default direction from `/messages`, a `v2` version
could be added which accepts the `dir` parameter with the same default directionality
as `/messages`, but the opposite of the current (`v1`) version of the endpoint.


## Security considerations

None.

## Unstable prefix

Before standardization, `org.matrix.msc3715.dir` should be used in place of `dir`.

[^1]: Note that [Synapse's implementation](https://github.com/matrix-org/synapse/blob/10a88ba91cb16ccf757984f0a7d41ddf8b4dc07f/synapse/streams/config.py#L48)
does not require a `dir` parameter for the `/messages` API and defaults to `f`
if it is not provided.
