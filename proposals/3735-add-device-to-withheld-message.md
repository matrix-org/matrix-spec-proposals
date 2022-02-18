# MSC3735: Add device information to m.room_key.withheld message

[MSC2399](https://github.com/matrix-org/matrix-doc/pull/2399) introduced a
message that could be used to inform message recipients about the reason that a
megolm session was not sent to it.

While it appears to be working well for the initial key share, additional
information is needed for the situation where it is used for responding to key
requests so that the requester can track the responses that it receives in
response to their request.  If a device requests a key from multiple other
devices, and one of them responds with an `m.room_key.withheld` message, the
first device currently is unable to determine which device responded with the
`m.room_key.withheld` message.

## Proposal

One new field is added to the `m.room_key.withheld` message when sent in
response to a key request:

- `from_device`: the device ID of the device sending the `m.room_key.withheld`
  message (this is the same field name used in key verification)

No changes are made when the withheld message is not sent in response to a key
request.

## Potential issues

None

## Alternatives

Rather than including the device ID, the `m.room_key.withheld` message could be
encrypted, allowing the key requester to infer the device ID.  However, there
is no other advantage to encrypting the message.

## Security considerations

None

## Unstable prefix

Until this proposal is accepted, the field used should be called
`org.matrix.msc3735.from_device`.

## Dependencies

None
