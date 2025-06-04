# MSC4296: Mentions for device IDs

The [`m.mentions`] content property on events allows senders to include an indicator about whether
the event should trigger a specialised notification for some or all room members. Among others,
this can be used to direct events at a certain recipient group within the room. It is, however,
not currently possible to direct events at a certain subset of devices within a room. This can
be helpful, for instance, in cases where devices with different capabilities are participating
in the room and the sender wants to provide a hint on which devices the recipient should pick up
the message. This proposal makes it possible to mention specific devices via the existing
[`m.mentions`] mechanism.

## Proposal

A new optional property `device_ids` is introduced in [`m.mentions`] to allow specifying an array
of device IDs to be mentioned by the message.

```json5
"m.mentions": {
  "device_ids": ["ABC1234"]
}
```

It is legal for `room` and `user_ids` to be present within `m.mentions` simultaneously to `device_ids`.

## Potential issues

None.

## Alternatives

None.

## Security considerations

Device IDs are already disclosed when sending messages in encrypted rooms. Allowing their use within
`m.mentions` does, therefore, not present an additional metadata leak.

## Unstable prefix

Until this proposal is accepted into the spec, implementations should refer to `device_ids` as
`de.gematik.msc4296.device_ids`.

## Dependencies

None.

[`m.mentions`]: https://spec.matrix.org/v1.14/client-server-api/#definition-mmentions
