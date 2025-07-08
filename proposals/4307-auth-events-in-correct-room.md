# MSC4307: Validate that `auth_events` are in the correct room

Each event in Matrix specifies a list of [auth events](https://spec.matrix.org/v1.14/server-server-api/#auth-events-selection), which are used during [event authorisation](https://spec.matrix.org/v1.14/server-server-api/#checks-performed-on-receipt-of-a-pdu) to ensure that the event should be permitted.

Currently, the Matrix specification does not make explicit that these auth events must be in the same room as the event itself.

This was the cause of a security vulnerability in Synapse 1.7 and earlier.

## Proposal

Within the [auth rules](https://spec.matrix.org/v1.14/rooms/v11/#authorization-rules), for all room versions, add a new rule 2.5 reading:

> 2.5. If any `auth_event` has a `room_id` which does not match that of the event being authorised, reject.

In practice, Synapse already
[implements](https://github.com/element-hq/synapse/blob/9d43bec/synapse/event_auth.py#L234)
this check, and we would expect that any other server does likewise. It is also
[enforced](https://github.com/matrix-org/sytest/blob/bb83c6f0cbec5f822dcaecd22533ac3e7ffde0ef/tests/50federation/31room-send.pl#L201)
by the SyTest homeserver test suite. It seems a clear omission in the text of
the auth rules.

## Potential issues

If there exist implementations which do not already enforce this rule, then
introducing it retrospectively could lead to split-brain situations where
different servers accept different events into the DAG. However:

 1. Since Synapse already implements this rule, the possibility of a split-brain already exists.
 2. The security implications of *not* doing this check are prohibitive (ultimately, an attacker with the ability to send messages to a room can subvert the event auth system to take over the room).

## Alternatives

We could leave the auth rules for existing room versions unchanged (and make
either this or some other change in a future room version). Again though, given
we believe all current implementations must implement this rule in practice,
this seems futile.

## Security considerations

Auth rules are a very delicate area of the Matrix spec. Homeserver maintainers should be particularly careful when implementing them.

## Unstable prefix

N/A

## Dependencies

None.
