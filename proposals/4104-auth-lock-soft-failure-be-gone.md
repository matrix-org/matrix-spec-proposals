# MSC4104: Auth Lock: Soft-failure-be-gone!

This MSC introduces a new authorization event, the auth-lock.
When a server issues an authorization event that supersedes an existing
event, for example by banning a user, the admin can can choose to
canonicalise their version of the room history by issuing an auth-lock.
This can be thought of as a thread lock from forum software applied
to a specific portion of the DAG. The auth-lock event not only
specifies the authorization event to lock, but all forward
extremities that reference the locked authorization event. Thus
canonicalising the history of that part  of the DAG.

Any further events that reference an authorization event that has been
*locked* will then be rejected outright during authorization.

## Proposal

### The auth lock event `m.auth_lock`

#### Properties
- content:
  + `locked_event_id`: The event_id of the authorization event to lock.
  + `extremities`: A list of extremities that should be shared to other
   servers representing the canonicalised version of the room history.

- state_key: A sha256 of the `locked_event_id` concatenated with the
  mxid of the event sender.

### Changes to auth_rules

#### Issuing `m.auth_lock`

If type is `m.auth_lock`:
  1. if `state_key` does not match a sha256 of `locked_event_id` and
     `sender`, reject.

#### Authorizing other events

Considering the event's `auth_events`:
  1. if the considered auth_event's `event_id` matches a
	 `locked_event_id` AND the `event_id` of the event is abscent
     from any `extremities` field AND the chain of `prev_events`
     from any event referenced by any `extremities` field, reject.

## Potential issues

### Conflicting auth-lock events

Imagine that there are two admins in a room, Alice and Bob.
Imagine that there is a malicious user Chelsea.
Alice and Bob both ban chelsea.
Alice sees Chelsea send events B -> A.
Bob sees Chelsea send events C -> B -> A.
Alice and Bob both issue auth_lock events for Chelsea's prior membership.
Alice's `extremities` field includes `B`, but excludes `C`.
Bob's `extremities` field includes `C`.

The receiving server must combine the `extremities` from both events
such that the canonical history becomes C -> B -> A.

### Issuing auth-lock to deliberately encode less or no extremities

#### Effects on participating servers 

We counteract this issue by requiring that servers maintain all
existing `extremities` and their `prev_events`, regardless of
whether they are missing from the `extremities` field of
an `m.auth_lock` event.

#### Effects on joining servers

Joining servers will no longer be able to authorize large parts of the
room's history.

### Revising auth-lock to deliberatly encode less or no extremities

We counteract this issue by encoding that only one auth_rule can exist
for the same `state_key` in the room's history.

### Split history for unprivileged users on unprivileged servers

Imagine that Alice issues an `m.room.power_levels` event P.
Alice revises this event so that it becomes P'.
Alice issues an auth_lock for P, Lock-P.
Imagine that Alice receives an event B from Bob that references P.
Alice is forced to reject event B.

### Resolution

Bob receives Lock-P, and notices that B is abscent from the chain
specified in Lock-P's `extremities`.

We would need a new MSC for bob to resend B as B' such that servers who
have accepted B would recognise B' to be a duplicate that references
more recent authorization events.

### Redaction of the lock

We probably do want the lock to be redactable.
But how can you be sure that you're not opening pandora's box by
allowing hidden malicious events residing on participating servers
to suddenly be incorporated into the DAG?

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
