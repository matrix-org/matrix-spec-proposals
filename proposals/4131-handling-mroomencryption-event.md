# MSC4131: Handling `m.room.encryption` events

The `m.room.encryption` event type indications whether encryption is enabled in
a room, and if so, what encryption algorithm to use and what parameters to use
for the encryption algorithm.  However, the spec does not specify how to handle
various situations that clients may encounter, such as unknown algorithms, or
changing algorithms.  Clients have been left to themselves to determine how to
handle such situations.

This MSC defines how clients should handle `m.room.encryption` events, so that
different clients behave consistently and securely.

The behaviours defined in this MSC are intended to ensure that the security of
a room cannot be reduced, only increased.  It tries to guard against a
malicious homeserver (since state events are not authenticated, and so a
homeserver could forge events), or against a malicious admin.


## Proposal

Clients must keep track of the "current encryption state" for a room.
Initially, the current encryption state is the first valid `m.room.encryption`
state event that the client encounters for a room, where an `m.room.encryption`
event is considered "valid" if it is not redacted, and contains a non-empty
`algorithm` property.  The current encryption state may change as more
`m.room.encryption` events are encountered.

*Redactions:* If an `m.room.encryption` event is redacted, the current
encryption state does not change.

*Algorithm changes:* Unless specified otherwise for a given algorithm, if an
`m.room.encryption` specifies an `algorithm` different from the current
encryption state for a room, the client must either warn the user that the
algorithm has changed and allow the user to continue to send events using the
old algorithm, or prevent events from being sent to the room.  However, the
client should not allow the user to send events to the room without first
warning them about the change.  This is to prevent the encryption from being
downgraded in a room.

In the future, some algorithms may allow a room to change algorithms without
notifying users in the room.  For example, a hypothetical Megolm v2 may specify
that changes from Megolm v1 to Megolm v2 are allowed.  In this case, if the
current encryption state specifies the Megolm v1 algorithm, and a new
`m.room.encryption` state event is encountered with Megolm v2 as the algorithm,
the current encryption state will be changed to specify Megolm v2.  When an
algorithm allows such upgrades, it should also specify how encryption
parameters (such as key rotation) are handled in the upgrade.

*Unknown and unsupported algorithms:* If a client encounters an
`m.room.encryption` state event that specifies an unknown or unsupported
algorithm, the current encryption state should still be set to that state event
if it is the first valid `m.room.encryption` event that the client encounters
for that room.  In this case, the client must either warn the user that the
algorithm is not supported and allow the user to send unencrypted events, or
prevent events from being sent at all.  However, the client should not allow
the user to send events to the room without first warning them that the
encryption algorithm is not supported.  This includes clients that do not
support encryption at all: clients that do not support encryption must warn
users before allowing them to send unencrypted events to an encrypted room.

When a client encounters an `m.room.encryption` state event that specifies an
unknown or unsupported algorithm, the client should remember this state event
so that it can use the encryption algorithm if a future version of the client
supports it.

If the current encryption state indicates using an unknown or unsupported
algorithm, and the client encounters an `m.room.encryption` state event that
specifies a supported algorithm, the client must either warn the user that the
original, unsupported algorithm is not supported and allow the user to send
events encrypted using the new, supported algorithm, or the client may prevent
events from being sent at all.

*Events encrypted with a different algorithm:* If a client receives an event
encrypted with an algorithm that is different from the algorithm given by the
current encryption state, the client should warn the user.  This includes
receiving an encrypted event in a room that does not have encryption enabled.

Likewise, an unencrypted event received in a room with encryption enabled
should be presented to the user with a warning.

*Back-paginating:* When a client back-paginates events in a room and encounters
an `m.room.encryption` state event, it may re-calculate the current encryption
state, taking into account the new `m.room.encryption` event, and playing back
the subsequent `m.room.encryption` events.

### `m.megolm.v1.aes-sha2` algorithm

The `m.megolm.v1.aes-sha2` algorithm allows key rotation parameters to be
specified in the `m.room.encryption` state event.  Clients should define
acceptable maximum values for these parameters: if an `m.room.encryption` event
specifies a value larger than the this value, the acceptable maximum value will
be used instead.

Clients must not allow these parameters to be increased.  If an
`m.room.encryption` state event specifies a value that is larger than the value
that is in the current encryption state, the value from the current encryption
state must be used instead of the new value.  Note that the parameters are
handled separately.  For example, if the `m.room.encryption` state event
specifies a larger `rotation_period_ms`, but a smaller `rotation_period_msgs`,
then the current encryption state will retain the existing
`rotation_period_ms`, but be updated to use the new `rotation_period_msgs`.

If the parameters are not present in an `m.room.encryption` state event, then
they should be handled as if they were specified to be the default values
chosen by the client.  For example, if the client uses the default values
recommended by the spec (604,800,000 for `rotation_period_ms` and 100 for
`rotation_period_msgs`), and the current encryption state does not specify
values for either parameter, and the client sees an `m.room.encryption` event
with `rotation_period_ms: 302400000` and `rotation_period_msgs: 200`, the
client should set `rotation_period_ms` to 302,400,000, but continue to use 100
for `rotation_period_msgs`.  On the other hand, if the current encryption state
has `rotation_period_ms` set to 800,000,000, and `rotation_period_msgs` set to
50, and the client receives an `m.room.encryption` state event that does not
specify the rotation parameters, the client will treat it as if the event
specified the default values, and update the current encryption state to use
the default of 604,800,000 for `rotation_period_ms`, but continue to use 50 for
`rotation_period_msgs`.

## Potential issues



## Alternatives

Rather than give guidance, we could just leave clients to their own devices.

We could authenticate state events to ensure that a malicious homeserver cannot
forge state events.  This should be done eventually, but it is complicated so
it will take time to do correctly.  This also does not protect against a
malicious admin.

## Security considerations

This proposal only considers state events that the client sees.  A malicious
homeserver could hide events from users.  In addition, events sent before the
first `m.room.encryption` state event that the client sees may not be
considered.  To guard against a malicious admin who simply sends new
`m.room.encryption` events, a client could search through all previous
`m.room.encryption` events by using the `replaces_state` property (if
`replaces_state` is standardised: see
https://github.com/matrix-org/matrix-spec/issues/274) when it first encounters
a room with encryption enabled.  However, this does not guard against a
malicious admin who redacts events, and does not guard against a malicious
homeserver, so its effectiveness is questionable.

## Unstable prefix

No new identifiers are introduced, so an unstable prefix is not needed.

## Dependencies

None
