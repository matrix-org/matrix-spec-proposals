# MSC4385: Allowing `m.secret.send` without a prior `m.secret.request`

[MSC1946](https://github.com/matrix-org/matrix-spec-proposals/pull/1946)
introduced the `m.secret.request` and `m.secret.send` events, which allow a
device to request a secret from another device, and for the other device to send
the secret to the first device.  In that MSC, an `m.secret.send` must only be
sent as a response to `m.secret.request`; unsolicited `m.secret.send` events
were to be ignored.

However, there are situations in which a device may want to send a secret to
other devices, without the secret being requested.  For example, if a device
changes the private key for key backup, it can share the key with other devices
so that they can access the key backup.

## Proposal

The `request_id` property of an `m.secret.send` event is optional.
`m.secret.send` events may be sent without a corresponding `m.secret.request`
event, and if so, MUST be sent without an `request_id` property, but MUST
include a `name` property, which contains the name of the secret being shared.
`m.secret.send` events with a `request_id` property are handled as before.

`m.secret.send` events without a `request_id` must only be accepted from
cross-signed devices belonging to the same user.  In addition, the client MAY
prompt the user before accepting the `m.secret.send` event.  The client MAY also
only accept certain secrets.  For example, the client could accept the key
backup secret, but could require re-verification rather than accepting the
cross-signing secrets.

## Potential issues

Clients that do not implement this proposal will not accept `m.secret.send`
events without the `request_id` property, and so the event will have been sent
needlessly.  However, having such events sent to old clients should not cause
any issues for the clients, as they should simply discard them as invalid, so it
will be as if the events were not sent at all.

If a client is offline while a secret is changed multiple times, it will receive
multiple `m.secret.send` events, and will have to determine which one is the
current one.  For the existing secrets, there are easy ways of determining which
secret "works".

## Alternatives

Rather than preemptively sending out a secret when it is changed, the user's
other clients could try to notice when a secret is changed, and then broadcast
an `m.secret.request` to all the user's other devices.  However, this could
result in delays in obtaining the secret if the device that changed the secret
is not online when the request is sent out.  As well, it could result in many
extra events being sent, since the requesting device does not know which device
it needs to request from, and so must broadcast `m.secret.request` events to all
the user's other devices.

## Security considerations

An attacker who takes control of a device could send out a secret that is
controlled by the attacker.  For example, the attacker could create a new key
backup and send out the private key so that other clients will use the new
backup, allowing the attacker to read new keys uploaded to the key backup.
However, if the attacker has taken control of a device, it is likely that they
would have access to the existing secret, and so would not gain anything by
sending out a new secret.  For this reason, `m.secret.send` events without a
`request_id` property MUST only be accepted from cross-signed devices, so that
the attacker cannot just create a new device and send out secrets.  Clients can
also apply other mitigations such as prompting the user when a new secret is
received.

## Unstable prefix

None, since no new names are introduced.

## Dependencies

None.
