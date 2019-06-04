# Olm unwedging

Olm sessions sometimes get out of sync, resulting in undecryptable messages.
This can happen for several reasons.  For example, if a user restores their
client state from a backup, the client will be using an old ratchet state
([riot-web#3822](https://github.com/vector-im/riot-web/issues/3822)).  Or a
client might expire a one-time key that another client is trying to use
([riot-web#3309](https://github.com/vector-im/riot-web/issues/3309)).  This
proposal documents a method for devices to create a new session to replace the
broken session.

## Proposal

When a device receives an olm-encrypted message that it cannot decrypt, it
should assume that the olm session has become corrupted and create a new olm
session to replace it.  It should then send a dummy message, using that
session, to the other party in order to inform them of the new session.  To
send a dummy message, clients may send an event with type `m.dummy`, and with
empty contents.

In order to avoid creating too many extra sessions, a client should rate-limit
the number of new sessions it creates per device that it receives a message
from; the client should not create a new session with another device if it has
already created one for that given device in the past 1 hour.

Clients may wish to take steps to mitigate the loss of the undecryptable
messages.  For example, megolm sessions that were sent using the old session
would have been lost, so the client can send
[`m.room_key_request`](https://matrix.org/docs/spec/client_server/latest.html#m-room-key-request)
messages to re-request any megolm sessions that it is unable to decrypt.

The spec currently says, "If a client has multiple sessions established with
another device, it should use the session from which it last received a
message." (the last paragraph of the [`m.olm.v1.curve25519-aes-sha2`
section](https://matrix.org/docs/spec/client_server/r0.4.0.html#m-olm-v1-curve25519-aes-sha2)).
When comparing the time of the last received message for each session, the
client should only consider messages that were successfully decrypted,
and for sessions that have never received a message, it should use the creation
time of the session.  The spec will be changed to read:

> If a client has multiple sessions established with another device, it should
> use the session from which it last received and successfully decrypted a
> message.  For these purposes, a session that has not received any messages
> should use its creation time as the time that it last received a message.

## Tradeoffs

## Potential issues

## Security considerations

An attacker could use this to create a new session on a device that they are
able to read. However, this would require the attacker to have compromised the
device's keys.

## Conclusion

This proposal outlines how wedged olm sessions can be replaced by a new
session.
