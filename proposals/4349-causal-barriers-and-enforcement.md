# MSC4349: Causal barriers and enforcement

_Note: This MSC exists because
[MSC4345](https://github.com/matrix-org/matrix-spec-proposals/pull/4345)
described an informal version of the deferred authorization causal
enforcement model discussed in this MSC. Which uncovered the problem
of causal barrier conflicts._

Matrix currently uses _causal barriers_ enforced locally by soft
failure to exclude concurrent events. A _causal barrier_ works in
Matrix because `prev_events` and `auth_events` specify the _causal
predecessors_ of the event. And with a full synchronisation, it is
possible to determine which events are concurrent. So therefore a
_causal barrier_ is an event which excludes all concurrent events from
_consideration_. Where consideration usually means what is shown to an
end user.

The `m.room.member` event with a _membership_ of `ban` is a causal
barrier that prevents the sender from adding concurrent events to the
ban event's causal predecessors. And this is enforced locally to each
server through soft-failure.

In distributed systems, _vector clocks_ are used to provide reasoning
about causal order. Causal history is already encoded in PDUs in
Matrix through the `prev_events` and `auth_events` of each PDU, and so
a complete DAG would provide us with an implicit vector clock.

Further, once a server has all of the causal predecessors for a given
event, a precise vector clock frontier for the sender of the event can
be constructed by walking the DAG.

## Soft failure as causal enforcement

Soft failure provides local enforcement of _causal barriers_ that is
necessary while knowledge of causal predecessors is incomplete. Soft
failure allows servers to make an immediate decision about concurrent
events without a full synchronisation of the DAG.

We identify two major problems with soft failure:

1. Unbounded DAG growth: Soft-failed events are still accepted into
   the DAG, and there is no in-DAG solution to prevent this.

2. Hidden causal barrier conflicts: Soft-failure hides cases where
   causal barriers conflict with a sender's previously acknowledged
   history.

## Hidden causal barrier conflicts

The problem of hidden causal barrier conflicts does not seem to be
widely known or explored. To illustrate the problem we ask you to
imagine Matrix had a different enforcement model for causal
barriers. We name this causal enforcement system _deferred
authorization_.

### Deferred authorization as causal enforcement

When a server recieves an event which is concurrent with a _causal
barrier_ the receiving server should determine whether it has complete
knowledge of all of the _causal barrier_ event's causal predecessors.

If knowledge is incomplete, the server makes an immediate decision to
soft fail the concurrent event (which is what happens currently in
Matrix).

However once the server has all of the _causal predecessors_ for a
_causal barrier_ it can infact revist the decision, and make a final
decision.

To do this, the server consults the predecessors of the causal barrier
event to form a vector clock frontier for the sender of the
conflicting event.

The server can then either accept events that were soft-failed or
reject them. Effectively resolving soft-failure.

Such a _causal barrier enforcement model_ uncovers a side-effect of
soft-failure which is less obvious.

If the sender of a ban event was to deliberately ignore the history of
the target, they now have the power to erase the target's history for
all room participants. Unfortunately, this already can happen today,
it's just room participants with a more complete synchronisation are
unable to notice. And anyone with a partial synchronisation, such as a
new joiner, can.

### Soft-failure hides causal barrier conflicts

- Soft-failure currently obscures the fact that Matrix allows causal
  barriers to conflict with a sender’s previously acknowledged
  history. This can result in parts of a room’s history effectively
  disappearing for any room participant that did not have the same
  causal frontier at the time of the event.

- In practice, this means that malicious or careless use of barriers
  can erase history for new joiners or for any server in the room that
  had only a partial view of the DAG upon receipt of the
  event. Servers with more complete history retain the missing events,
  but these are hidden by soft-failure. In other words, the behaviour
  is not theoretical, it is possible today and its impact depends on
  how complete a server's DAG synchronisation is at the time of the
  event.

- As a community, this has been accepted by relying on full-sync
  assumptions and by prioritising the continuity of existing
  participants’ views over the consistency of new joiners.

- If soft-failure is to be reframed as enforcement of causal barriers,
  then this issue must be acknowledged and addressed. It is not
  sufficient to treat the current behaviour as sound; we need to
  recognise the limitations of the existing model and decide
  explicitly how much power barriers should have to override history.

- In other words soft-failure provides an illusion that Matrix is
  sound.

## Proposal

We propose that the terminology for causal barriers from this MSC is
adopted so that the problem space can be discussed. There are a couple of
solutions that can be explored:

- Policy servers as causal authorities: Policy servers can act as
  causal authorities. They could do this by performing a
  full-synchronisation on each event they recieve. And then only
  signing events that are consistent with the policy server's vector
  clock frontier.

- Deferred authorization as causal enforcement (described in the MSC
  introduction), combined with a system that allows distrust to be
  expressed in senders in order to provide a manual resolvation to
  forks that would constitute a politcal problem.

This would allow us to immediately begin to use consistent terminology
within the context of [MSC4345: Server key identity and room
membership](https://github.com/matrix-org/matrix-spec-proposals/pull/4345#discussion_r2336627872)
and other MSC's which may have security concerns that cannot be
expressed without this understanding.

## Potential issues

- None considered

## Alternatives

- None considered

## Security considerations

- None considered

## Unstable prefix

- Not applicable

## Dependencies

- None
