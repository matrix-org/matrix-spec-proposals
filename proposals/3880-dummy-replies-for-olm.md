# MSC3880: Dummy replies for olm

Olm is a [double ratchet
algorithm](https://en.wikipedia.org/wiki/Double_Ratchet_Algorithm).  When Alice
and Bob communicate over Olm, it creates a new hash ratchet when the
conversation changes directions.  That is, if Alice was the last person to send
an Olm message, and then Bob sends a message, a new hash ratchet is created.
Thus if an attacker had managed to obtain the state of the previous hash
ratchet used by Bob, the attacker will not be able to decrypt future messages.

However in some cases, only one person may be sending messages.  Or one party
may be quiet for a long time.  In such a case, a large segment of the
conversation may be exposed to an attacker who is able to obtain the state of
the hash ratchet.

We propose that clients should periodically send dummy events over Olm to
ensure that a new hash ratchet is created.

## Proposal

If a client receives some events over Olm that are not of the type
[`m.dummy`](https://spec.matrix.org/unstable/client-server-api/#mdummy), it
should send an event over Olm to the other party.  If it does not have any
meaningful event to send, it should send an `m.dummy` event.

It is up to the client to decide whether and when to send the event.  One
possibility is: if the client receives an event over Olm, it waits 2 minutes.
If it has not sent any other event over Olm within those 2 minutes, it will
send an `m.dummy` event.  Clients may want to take measures to ensure that
sending the dummy events does not interfere with the normal functioning of
the client.  For example, a client may delay sending dummy events while it is
sending other events.

The definition of the `m.dummy` event in the spec will be updated to indicate
the more general nature of the event: it is an event that should be ignored by
the recipient, aside from the effect that it has on the communication channel.

## Potential issues

This proposal doesn't help in the situation where one client is simply offline
for a long time.

If clients do not disregard `m.dummy` events, this could cause an infinite loop
between two clients.

## Alternatives

None

## Security considerations

None

## Unstable prefix

No unstable prefix is needed since no new event is used.

## Dependencies

None
