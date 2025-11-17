# MSC4297: State Resolution v2.1

This MSC proposes two modifications to the existing state resolution algorithm which will improve
security by reducing the frequency of "state resets". This proposal bases its changes on
room version 11.

## Background

Matrix is decentralised. This means there is no central entity which orders events. Ordering
is critical to enforce access control. For example, in order for Bob to change the room name
he needs to be a moderator/admin _first_. To model this, rooms are represented as a
directed acyclic graph (DAG) of events. State events are operations like "Bob changing the room name" or
"Bob gaining admin privileges". These events "point" to the most recent events that the server that created the event has
seen in that room. In order for Bob to change the room name, his room name event MUST point either
directly or indirectly to the event which gave him the right to change the room name. As Matrix is
decentralised, Alice could independently demote Bob without him being aware of it at the same time
he tries to change the room name. This is concurrent behaviour, and how this is managed is up to the
state resolution algorithm. The algorithm:

 - selects which events are in conflict,
 - determines how to order these events,
 - filters out unauthorised events based on this ordering

For example, Alice's demotion may be applied first so Bob cannot change the room name.

<img width="1115" src="/proposals/images/4297-msc-1.png" />


However, the algorithm can cause surprising behaviour. If Alice cannot communicate Bob's demotion to Bob's
server quickly, then Bob may perform many more privileged operations over minutes or hours. Eventually,
Alice's demotion will arrive on Bob's server, which would cause all the operations Bob did to be
"rolled back" or reverted. This can be unexpected to users on Bob's server, but is an _expected_
consequence of Matrix being decentralised. A "state reset" is very similar to this in that it causes
unexpected behaviour. However, the defining characteristic of a state reset is that this happens
_even when there is no revocation event_ such as a demotion.

Concurrent events can occur at any point in the room DAG. This means when the DAG is put into a
total order from "oldest" to "newest", previously unseen events may appear at the "older" end of the
ordering. These unseen events could affect whether later events are authorised or not, so we need to
"replay" events from the unseen events to the latest events. To avoid replaying too many events,
the algorithm intelligently calculates the difference between the sets of concurrent events to only replay what is necessary. It is desirable to prevent
servers from adding concurrent events from an obviously long time ago, but since servers never
coordinate (e.g via a consensus algorithm) they can never be sure that they have seen all concurrent
events. The idea of making it impossible to add concurrent events to some sections of the graph is
referred to as "causal stability" or "finality".

Matrix allows servers to partially synchronise the DAG. This allows servers that have been offline for
a long time to quickly resynchronise without being forced to pull in the entire room history. To ensure
authorisation events are applied correctly, events have another DAG formed of `auth_events`, called
the "auth chain". These chains only consist of authorisation events and _are_ fully synchronised.
The `auth_events` cite all the historical events which authorise the event in question. Authorisation
events are the following state events: `m.room.create`, `m.room.member`, `m.room.power_levels` and
`m.room.join_rules`. A subset of authorisation events are [power events](https://spec.matrix.org/v1.14/rooms/v11/#definitions).

>[!NOTE]
> As a reminder, State Resolution v2.0 works by merging together sets of state across branches of
> the room DAG.  State events common to both branches are called 'unconflicted'; state events which
> only exist on one branch or another or have different values are called 'conflicted'.  The
> resolved state is calculated:
>  * Start with the unconflicted state as our "base layer"
>  * Consider the conflicted power events (PLs, kicks, bans, join_rules) and any conflicted authorisation
>    events that are required to authorise said power events, use reverse topological ordering to
>    provide a consistent ordering and then layer those by replaying them on top, incrementally
>    authorising as you go.
>  * Work out the sequence of the conflicted normal state events using mainline ordering (the
>    'backbone' of power level events through the conflicted set) and then similarly replay those
>    on top too.
>  * Reapply any unconflicted state keys which may have been overwritten in the previous steps.

## Problems with the existing algorithm

The algorithm relies on two pieces of ordering information, from `prev_events` and `auth_events`.
The `prev_events` ordering controls the input state sets to the algorithm. These state sets aren't
guaranteed to map correctly onto the auth chain ordering induced by `auth_events` due to partial
synchronisation. If these orderings disagree, the algorithm can select older state.
This can happen due to federation outages or due to faulty implementations. The scenarios below
require this to have happened, and are represented by "incorrect" state. This typically manifests
as _older state_ existing in a state set. State resets happen because the algorithm fails to determine
all the events that need to be replayed when _older state_ exists in a state set.

Problem A focuses on the "initial state" of the room, before the conflicted events are replayed.
This is currently set to the "unconflicted" state of the room. The core idea is that if both forks
agree on the exact event IDs for 99 members, but disagree on the exact event ID for the 100th member,
we do not need to replay all 99 member events. The problem is that there is more than one way to
"agree on the exact event IDs", which can cause state to reset under certain circumstances.

Problem B focuses on selecting _which events_ are in conflict. The core idea is that we do
not want to replay the entire history of the room every time there is a conflict, but only the
differences between each fork (the _auth difference_). These differences don't include enough events
under certain circumstances, causing state to reset.

>[!NOTE]
> The following scenarios present rooms in two ways: via the familiar `prev_events` ordering which
> represents concurrent behaviour and the more unfamiliar `auth_events` ordering which represents
> "is authorised by" relationships. The `auth_events` graph contains many redundant edges (e.g every event
> references the create event), so we will only present the _transitive reduction_ of this graph, which
> removes these edges. This helps illustrate the problems better.
>
> <img width="201" src="/proposals/images/4297-msc-2.png" />
>
> The scenarios also use coloured diamond symbols to indicate the state of the room at a particular
> edge on the `prev_events` graph. Servers may incorrectly calculate this e.g due to partial synchronisation,
> which is indicated by a dashed arrow pointing from the correct state to the incorrect state. The colour
> of the diamond only serves to distinguish between other state sets, it has no other meaning, despite similar
> colours being used to indicate the sender of an event.
>
> <img width="632" src="/proposals/images/4297-msc-3.png" />


### Problem A: Conflicting events can be unauthorised by the unconflicted state

Events can be conflicted in _two_ ways: via room state's `prev_events` and via the auth chain's `auth_events`.
The room state determines what the inputs to the state resolution algorithm are and hence what is in
the unconflicted state. The auth chains determine which extra events are pulled in and the ordering
between events. Room state can unexpectedly reset if these two orderings disagree, as outlined in
the following example[^1]:

<img width="426" src="/proposals/images/4297-msc-problem-a-1.png" />
<img width="618" src="/proposals/images/4297-msc-problem-a-2.png" />


In this scenario, the state of the room at the blue diamond is obtained via partial synchronisation,
e.g `/state{_ids}`. This response contains an outdated join rules event, meaning both join rules events
are now in conflict, even though all events on both forks agree
on what the latest join rule event is via their auth chains. This causes the join rules to be
replayed. However, both forks also agreed that Alice had left the room. As such, the unconflicted
state starts with Alice not being a member in the room. When the join rules events get replayed,
both fail since Alice (who set them) is not in the room. This causes the room to have no join
rules event.

<img width="573" src="/proposals/images/4297-msc-problem-a-3.png" />

### Problem B: Conflicting events need extra unconflicted events in order to be authorised

Similarly to Problem A, this occurs when the ordering between `prev_events` and `auth_events` differs.
In this scenario, one fork can reference newer events via the auth chain whilst claiming the room
state is an older event. When this happens, the auth difference does not include all relevant events
between the old and new events as both sides have seen the events in-between via their auth chains. Most
of the time this will not cause a state reset, but when there are chains of events which are dependent
on one another, this can cause a state reset.

<img width="432" src="/proposals/images/4297-msc-problem-b-1.png" />
<img width="554" src="/proposals/images/4297-msc-problem-b-2.png" />

Note that the state of the room at the red diamond is obtained via partial synchronisation, e.g
`/state{_ids}`. This response contains an outdated power levels event, meaning the power levels events
are now in conflict.

In this example[^1], Alice is an Admin who promotes Bob. Bob then promotes Charlie. It is critical that
Bob's promotion is applied before Charlie's promotion, or else it will be unauthorised. However, the
auth difference calculation fails to include this event, leading to a state reset.

<img width="446" src="/proposals/images/4297-msc-problem-b-3.png" />

## Proposal

Two modifications are made to the algorithm which are described below. Both changes relate to
which events are selected for replaying. They do not modify how conflicted events are sorted
nor do they modify the iterative auth checks.

### Modification 1: Begin the first phase of iterative auth checks with an empty state map

This aims to fix problem A by disregarding the `prev_events` ordering entirely for determining the
initial state. It does this by starting with an empty state map. This causes the iterative auth
checks algorithm to load the auth chains, per the [iterative auth checks definition](https://spec.matrix.org/v1.14/rooms/v11/#definitions):

> If a (event_type, state_key) key that is required for checking the authorization rules is not
present in the state, then the appropriate state event from the event’s `auth_events` is used if the
auth event is not rejected.

This ensures that the algorithm replays events on top of the `auth_events` histories, rather than some unrelated
history.

Step 2 of the state resolution algorithm is amended to state:

> Apply the _iterative auth checks algorithm_, starting from ~~the unconflicted state map~~
__an empty state map__, to the list of events from the previous step to get a partially resolved state.

<img width="593" src="/proposals/images/4297-msc-sol-1.png" />

Note that even though we no longer insert the unconflicted state into the partially resolved state,
Step 5 of the algorithm ensures that the unconflicted state is still in the final merged
output, even though it may not have been during the resolution process:

> Update the result by replacing any event with the event with the same key from the unconflicted
> state map, if such an event exists, to get the final resolved state.

### Modification 2: Add events _between_ the conflicted state set to the full conflicted set

This aims to fix problem B by including relevant intermediate events when performing state resolution.
This modifies the definition of the "full conflicted set" to include _all events_ which are a _descendant_
of one conflicted event and an _ancestor_ of another conflicted event. This forms a "conflicted subgraph"
which is then replayed by the algorithm.

This means the full conflicted set contains:
 - the conflicted state events themselves AND
 - the auth difference AND
 - the events between the conflicted state events

The purpose of the auth difference is to replay the relevant auth history from each input state set.
Most of the time it does this, but when the input state sets are derived from a partial sync response
there's no guarantee that this will include the relevant history because the response may include
erroneous older events. By including the conflicted state subgraph we ensure that input state sets
with _old events_ have the auth history from those old events replayed.

<img width="549" src="/proposals/images/4297-msc-sol-2.png" />

A new term is added in the state resolution algorithm:

> **Conflicted state subgraph.** Starting from an event in the _conflicted
> state set_ and following `auth_events` edges may lead to another event in the
> conflicted state set. The union of all such paths between any pair of events
> in the conflicted state set (including endpoints) forms a subgraph of the
> original `auth_event` graph, called the _conflicted state subgraph_.

And the following modification is made to the definition of "Full conflicted set":

> **Full conflicted set.** The full conflicted set is the union of the conflicted state set,
> <ins>the conflicted state subgraph</ins> and the auth difference.


## Potential issues

### Performance

These modifications may impact performance in two ways:
 - more work is done on every state resolution to calculate the conflicted state subgraph.
 - potentially more events are replayed during resolution.

The data required to calculate the auth difference is also the same information required to
calculate the conflicted state subgraph, so no extra database requests are needed with these
changes. However, more CPU work needs to be performed to walk the auth chain to look for
conflicted events on every resolution.

In the common case, the conflicted state subgraph overlaps entirely with the auth difference,
meaning no extra events need to be replayed. This has been confirmed via
[partition/fault tolerance testing](https://github.com/element-hq/chaos) which tests extreme
cases with large numbers of membership changes and federation outages, producing resolutions such as:
```
additional events replayed=0 num_conflicts=17 conflicted_subgraph=271 auth_difference=263
```

## Further work

More changes are required in order to fix all cases of state resets. The changes proposed here
are based on real world scenarios where state resolution has produced undesirable results.
The underlying causes of these state resets is mismatched orderings. If the protocol had a single
ordering then this would remove this entire class of issues. This will be explored in a future MSC.

## Security considerations

The state resolution algorithm is a critical component in the overall security of a room. This proposal
is modifying the algorithm so there are inevitable risks associated with it. These risks are mitigated
because the proposal is _not_ changing how events are ordered nor how events are authorised. It is
purely _adding_ events to be replayed and relying on the auth chains as the authoritative source
to rebase changes onto.

## Unstable prefix

This algorithm is in use for room version `org.matrix.hydra.11`.

## Dependencies

This MSC has no dependencies.


[^1]: When used in conjunction with [MSC4289](https://github.com/matrix-org/matrix-spec-proposals/pull/4289)
Alice should not be present in the `m.room.power_levels` event. The examples function in the same way.