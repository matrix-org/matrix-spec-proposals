# MSC4445: Clarify `/sync` timeline order

Currently, the spec describes the order of events in the `timeline` of `/sync` in this manner:

> Events are ordered in this API according to the arrival time of the event on the
> homeserver. This can conflict with other APIs which order events based on their
> partial ordering in the event graph. This can result in duplicate events being
> received (once per distinct API called). Clients SHOULD de-duplicate events based on
> the event ID when this happens.
>
> *-- https://spec.matrix.org/v1.18/client-server-api/#syncing*

The spec clearly states that `/sync` should return events according to the "arrival time
of the event on the homeserver" (`stream_ordering`). This is not how [Synapse has been
behaving](https://github.com/element-hq/synapse/blob/e3db7b2d81cabc7e4335afc051e28678e3a9dd02/synapse/handlers/sync.py#L882-L897)
since the
[beginning](https://github.com/element-hq/synapse/commit/a56008842b43089433768f569f35b2d14523ac39).
Even a [later
commit](https://github.com/element-hq/synapse/commit/e2accd7f1d21e34181dd4543eca30ad1ea971b4c)
claims the following:

> The sync API often returns events in a topological rather than stream
ordering, e.g. when the user joined the room or on initial sync. When
this happens we can reuse existing pagination storage functions.
>
> *-- [Synapse `e2accd7` commit message*](https://github.com/element-hq/synapse/commit/e2accd7f1d21e34181dd4543eca30ad1ea971b4c)

Normally, this would just be a spec-compliance problem in Synapse but I think this may
be the right way to think about it.


## Proposal

For initial `/sync`, we want to view a historical section of the timeline; to fetch
events by the "partial ordering in the event graph" (topological ordering) (best
representation of the room DAG as others were seeing it at the time). This also aligns
with the order that `/messages` returns events in. For `/sync`, we should also extend
this to any time we're initially returning a room (therefore historical events) to the
user (like a newly joined room). This behavior basically results in the same outcome as
if no history was sent down `/sync` and `/messages?dir=b` was used instead.

For incremental `/sync`, we want to get all updates for rooms since the last `/sync`
(regardless if those updates arrived late or happened a while ago in the past); to fetch
events by "arrival time of the event on the homeserver" (`stream_ordering` in Synapse
for example).


## Potential issues

### Undefined terminology

The spec uses undefined terms like `stream ordering` and `topological ordering`, see
[`matrix-org/matrix-spec#1334`](https://github.com/matrix-org/matrix-spec/issues/1334).

The best reference I've found for how to define these is from the original piece of spec
that I pointed out at the beginning of this MSC and is what I based the language off of
in this proposal:

> Events are ordered in this API according to the **arrival time of the event on the
> homeserver**. This can conflict with other APIs which order events based on their
> **partial ordering in the event graph**. This can result in duplicate events being
> received (once per distinct API called). Clients SHOULD de-duplicate events based on
> the event ID when this happens.
>
> *-- https://spec.matrix.org/v1.18/client-server-api/#syncing*

Therefore:

 - `stream_ordering`: Ordered by the "arrival time of the event on the homeserver"
 - `topological_ordering`: Ordered by the "partial ordering in the event graph". This
   corresponds to the baked in [`depth`
   field](https://spec.matrix.org/v1.5/rooms/v10/#event-format-1) but ideally
   homeservers would use some [graph
   linearization](https://github.com/matrix-org/gomatrixserverlib/issues/187) strategy.
   Perhaps some online topological ordering (Katriel–Bodlaender algorithm) where
   `depth`/`topological_ordering` is dynamically updated whenever new events are
   inserted into the DAG.

### Flawed state management

This is more of just a note that this was considered as part of the proposal.

Clients which do flawed state management with `state` + `timeline` (c.f.
[MSC4222](https://github.com/matrix-org/matrix-spec-proposals/pull/4222)), may
accumulate state differently with this change. However, it's arbitrarily flawed either
way and Synapse has behaved as described in this proposal since inception, so this is
not necessarily a change in behavior.


## Alternatives

### Always order by the "arrival time of the event on the homeserver"

The alternative would be to keep the spec'ed status quo and have `/sync` always return
events in the order of "arrival time of the event on the homeserver". I can't think of
any real problems with this besides being inconsistent with the order of how we return
historical events. The order of messages does factor into how read receipts work and is
an area that [MSC4033](https://github.com/matrix-org/matrix-spec-proposals/pull/4033) is
trying to address.

There is also a [spec issue](https://github.com/matrix-org/matrix-spec/issues/852) which
considers changing `/messages` to use stream ordering for events.


## Security considerations

*None surmised so far.*

Changing the order of `timeline` events does not affect history visibility rules, so
there should be no security implications to this change. The same events are still being
sent down, just in a different order.


## Unstable prefix

Clients can rely on the presence of the
`org.matrix.msc4445.initial_sync_timeline_stream_ordering` and
`org.matrix.msc4445.initial_sync_timeline_topological_ordering` flags in
`unstable_features` as an explicit indicator to tell how a homeserver is behaving. If
these flags are absent, the client has to assume the server is behaving as currently
specc'ed but has no guarantee of this.

Synapse already behaves in the way described in this proposal (since inception in 2015)
and is unlikely to change it's behavior until a conclusion is made with this MSC.
Synapse can be updated to advertise
`org.matrix.msc4445.initial_sync_timeline_topological_ordering`.


## Dependencies

Other MSC's which add more sync API's (like
*[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186): Simplified
Sliding Sync*) should use the same ordering heuristics as this proposal.

