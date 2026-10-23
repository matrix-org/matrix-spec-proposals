# MSC4359: "Do not Disturb" notification settings

"Do not Disturb" (DnD) is a common feature of notification settings on various chat platforms. It
may act globally but also on a per-room or per-device basis and involves inhibiting prominent visual
or audible notifications without stopping to track them. This makes it possible for users to consume
these notifications later once DnD is disabled. It is important to differentiate DnD from "Muting"
where notifications are lost entirely and cannot be picked up on later.

In Matrix, notifications for new and unread content are configured via [push rules]. Push rules
currently don't support DnD. Rules can either notify or not but the notification state is entangled
with the unread state. This means push rules only support muting but not DnD.

As evidenced in [MSC3768] extending the push rule system to support DnD isn't trivial. This
proposal, therefore, takes a different approach by introducing an overlay configuration that allows
controlling DnD separately from push rules.

## Proposal

A new global account data event `m.do_not_disturb` is introduced. Its `content` contains a single
property `rooms` that is a mapping from room ID to empty object (for future extensibility).

``` json5
{
  "type": "m.do_not_disturb",
  "content": {
    "rooms": {
        "!foo:bar.baz" {}, // Don't notify about new content in this room
        ...
    }
  }
}
```

Instead of a valid room ID, `*` is also allowed and will match any room. Otherwise, globbing is not
permitted.

For any room matched by `m.do_not_disturb`, clients MUST suppress system-level notifications such as
sounds or notification pop-ups. Clients SHOULD also render unread state and counters less
prominently for matched rooms.

`m.do_not_disturb` applies to all devices in a user's account. It MAY be overridden on a per-device
basis using account data events of type `m.do_not_disturb.<DEVICE_ID>`.

``` json5
{
  "type": "m.do_not_disturb.ABCDEFG",
  "content": {
    "rooms": {
        "*" {}, // Don't notify at all on this device
    }
  }
}
```

To avoid flooding account data with per-device configurations, home servers SHOULD delete any
`m.do_not_disturb.<DEVICE_ID>` event when the given device is removed.

## Potential issues

This proposal creates another configuration system on top of push rules thereby complicating the
overall system further.

For clients that depend on remote notifications, the dispatch and delivery of these notifications is
not paused when in DnD mode. This might waste a certain amount of resources on both servers and
clients.

## Alternatives

[MSC3768] integrates DnD into the existing push rule system. This significantly increases the
complexity of managing push rules, however.

[MSC3881] allows clients to toggle pushers on and off without unregistering them. This makes it
possible to pause the delivery of remote notifications but only works on clients that use pushers
such as mobile apps. Additionally, it doesn't allow pausing notifications on a per-room level.

[MSC3890] is similar to this proposal but explicitly excludes clients that rely on pushers. Similar
to [MSC3881], it also doesn't work on a per-room level.

Clients could also use custom local settings to store DnD configurations without any changes to the
specification. This would require each client to invent its own system for storage and matching,
however. Additionally, custom client settings would make it impossible to centrally control DnD for
all devices at once.

## Security considerations

None.

## Unstable prefix

While this MSC is not considered stable, `m.do_not_disturb` should be referred to as
`dm.filament.do_not_disturb`.

## Dependencies

None.

  [push rules]: https://spec.matrix.org/v1.15/client-server-api/#push-rules
  [MSC3768]: https://github.com/matrix-org/matrix-spec-proposals/pull/3768
  [MSC3881]: https://github.com/matrix-org/matrix-spec-proposals/pull/3881
  [MSC3890]: https://github.com/matrix-org/matrix-spec-proposals/pull/3890
