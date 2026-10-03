# MSC4104: Auth Lock: Soft-failure-be-gone!

This proposal aims to make soft failure redundant, by introducing
`m.auth_lock` as a mechanism to stop authorising events that are
crafted to reference previous state. All without disrupting the
history of the room for new users.

This MSC introduces a new authorization event, the `m.auth_lock` event.
When a server issues an authorization event that supersedes an existing
event, for example by banning a user, the admin can choose to
canonicalise their version of the room history by issuing an auth-lock.
This can be thought of as a thread lock from forum software applied
to a specific portion of the DAG. The auth-lock event not only
specifies the authorization event to lock, but all forward
extremities that reference the locked authorization event. Thus
canonicalising the history of that part of the DAG.

Any further events that reference an authorization event that has been
*locked* will then be rejected outright during authorization.

## Proposal

### The auth lock event `m.auth_lock`

The `m.auth_lock` event can be issued in scenarios where room admins
or their tooling detect or anticipate events referring to previous
authorization events. This should only be done eagerly when there
is reasonable risk. For example, it would be inappropriate to
issue an `m.auth_lock` event after banning a spammer that
resided on `matrix.org` as it is unlikely for matrix.org
to attempt to maliciously reference old authorization events.
By delaying the application of `m.auth_lock`, room administrators
reduce the risk of divergence. This is something that currently
occurs frequently with [soft failure](https://github.com/element-hq/synapse/issues/9329).

#### Properties
- `content`:
  + `locked_event_id`: The event_id of the authorization event to lock.
    This is protected from redaction.
  + `extremities`: A list of extremities that should be shared to other
   servers representing the canonicalised version of the room history.
   This is protected from redaction.

- `state_key`: A sha256 of the `locked_event_id` concatenated with the
  mxid of the event sender. We do this so that different room admins
  can optionally specify their own versions of the `extremities`
  that will combine to form a complete set to be considered during
  authorization. This also keeps `extremities` conflict free.

### Changes to auth_rules

#### Issuing `m.auth_lock`

If type is `m.auth_lock`:
  1. if `state_key` does not match a sha256 of `locked_event_id` and
     `sender`, reject.

#### Authorizing other events

Considering the event's `auth_events`:
  1. For each `auth_event` all `m.auth_lock` events with a
     `locked_event_id` matching the `event_id` of the `auth_event`
     are found from the room's current state.
     From each `m.auth_lock` event relevant to one `auth_event`, the
     `extremities` fields are combined to form a set of all `extremities`
     relevant to the `auth_event`.
     If the considered auth_event's `event_id` matches any
     `m.auth_lock`'s `locked_event_id` field AND the `event_id` of the
     event being authorized is absent from both the `extremities` set
     AND the `event_id` of any connected event referenced via each
     extremity's `prev_events`, reject.

## Potential issues

### Multiple auth-lock events

Imagine that there are two admins in a room, Alice and Bob.
Imagine that there is a malicious user Chelsea.
Alice and Bob both ban Chelsea.
Alice sees Chelsea send events B -> A.
Bob sees Chelsea send events C -> B -> A.
Alice and Bob both issue auth_lock events for Chelsea's prior membership.
Alice's `extremities` field includes `B`, but excludes `C`.
Bob's `extremities` field includes `C`.

#### Solution

The receiving server must combine the `extremities` from both events
such that the canonical history becomes C -> B -> A.
This is already explicitly written within the authorization rules
in this MSC.

### Diverging `extremities`

Imagine Bob's server receives an `m.auth_lock` event and Bob's server
has authorized events referencing the `locked_event_id` that are not
present within any relevant `m.auth_lock`'s `extremities`.
Bob's server must decide what to do with the events it has already
authorized.

This is a problem that occurs in the following scenarios:

#### Scenario A: Alice deliberately encodes less `extremities` than Bob has
Alice issues an `m.auth_lock` to deliberately encode less or no
extremities, in an attempt permanently to diverge Bob's DAG.
Joining user David would then also not be able to see a large portion
of the history that Bob can, because it wouldn't be authorized in
David's DAG when David backfills.

#### Scenario B: Alice issues a lock quickly after changing an auth event

Imagine that Alice issues an `m.room.power_levels` event P.
Alice revises this event so that it becomes P'.
Alice issues an auth_lock for P, Lock-P.
Imagine that Alice receives an event B from Bob that references P.
Alice and every other server with Lock-P is forced to reject event B.

#### Scenario C: Bob's events are mixed with Chelsea's

Chelsea has sent `X -> A` to Alice, but `Y -> A` to Bob.
Bob has then appended `B -> Y -> A` and in turn Chelsea
has appended `Z -> B -> Y -> A` and sent `Z` to Bob.

Alice has banned Chelsea and locked Chelsea's prior membership.
Only now has Bob received this `m.auth_lock` event, and it only
contains the extremity `X`.

Alice can get `B` if Bob sends it to her,
but new joiner David will probably be unable to by backfilling `B`,
at least if David's server doesn't have special code to account
for the connected events being rejected.

#### Effects on participating servers 

Servers are required to maintain all their existing `extremities`
and their `prev_events`, regardless of whether they are missing from
the `extremities` field of any `m.auth_lock` event.

These servers should still incorporate these diverged `extremities`
into `prev_events` so that they can be discovered and repaired later.

#### Effects on joining servers

Joining servers will no longer be able to authorize large parts of the
room's history.

#### Solution A: Dedicated API for showing diverged events to room admins

A room administrator could be made aware of all the extremities that
are diverged. This can be done because a server can detect when
authorized events contain references to unauthorized events
within `prev_events` of authorized events in the DAG.

A room administrator can then preview the effects of incorporating
diverged extremities and make a decision to do so via the
`extremities` field of `m.auth_lock`.

#### Solution B: Room administrators on other servers issue their own `m.auth_lock`

Room admins residing on different servers with diverged extremities
can issue their own `m.auth_lock` event to include diverged extremities.
When this event is received by other servers, the diverged extremities
can be authorized and the DAG will converge again.

#### Solution C: Unprivileged users propose changes to the `extremities` of `m.auth_lock`

Participants in the room can propose changes to the `extremities`
contained within `m.auth_lock` via a dedicated event. Room administrators
can then review the effects and merge them.

#### Solution D: Recrafting PDUs

Take scenario B. Bob receives Lock-P, and notices that B is absent
from the chain specified in Lock-P's `extremities`.

We would need a new MSC for bob to resend B as B' such that servers who
have accepted B would recognise B' to be a duplicate that references
more recent authorization events.

This would allow Alice to see `B` in Scenario C. But it wouldn't
allow Alice to redact `Z` or `Y`, which Bob my find harmful.

### Locking all current auth events

It would be possible to lock all auth_events and stop any further
developments in the room.

## Alternatives

None recognized.


## Security considerations

See potential issues.


## Unstable prefix

None issued.

## Dependencies

None.
