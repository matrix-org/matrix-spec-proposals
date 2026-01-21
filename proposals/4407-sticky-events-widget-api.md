# Sticky Events (Widget API)

With [MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354), a way to send sticky events is introduced.
Sticky events are room events with a time-limited delivery guarantee. They will be synced by participating clients even across gappy syncs, for the duration specified by `sticky_duration_ms`.

This MSC only specifies how the Widget API uses this concept. [MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354)
gives more details about sticky events themselves.

Exposing sticky events to widgets is required for widgets implementing MatrixRTC.
Sticky events are needed for encrypted MatrixRTC membership events to be reliably delivered.

Since ElementCall (EC) is a widget and is based on MatrixRTC, this Widget API proposal is required for EC to work.

## Proposal

### Sending sticky events

We extend the "send_event" request defined by [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762)
as follows:

```jsonc
{
    // new
    sticky_duration_ms?: number;
    // other fields
    state_key?: string;
    type: string;
    content: unknown;
    room_id?: string;
    delay?: number; // from https://github.com/matrix-org/matrix-spec-proposals/pull/4157
}
```

### Capabilities

Two new capabilities will be introduced:

- `m.send.sticky_event`\
  Allows sending sticky events by using the optional `sticky_duration_ms` property in a `fromWidget send_event` widget action.
  All other `m.send.*` capabilities still apply. This capability allows sending sticky events for those types.
- `m.receive.sticky_event`\
  If this capability is allowed, the client will make sure the widget is aware of events that are currently sticky.
  All events that are currently sticky, of types that are allowed by `m.send.*` capabilities, will be included.

### Widget Client Implementation

This has the following behavioral impact on the widget client implementation:
- On widget startup, the client will send all sticky events that the widget is allowed to see.
- After capability re-negotiation, when the widget is granted `m.receive.sticky_event`, the client will send all currently sticky events that the widget is allowed to see.

If the capability `m.send.sticky_event` is granted and the client receives a send event with `sticky_duration_ms` set, the client must send a sticky event
as described in [MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354), using the `sticky_duration_ms`.

## Alternatives

## Unstable prefix

The following strings will have unstable prefixes:

- The send sticky event capability:\
  `m.send.sticky_event` -> `org.matrix.msc4407.send.sticky_event`
- The receive sticky event capability:\
  `m.receive.sticky_event` -> `org.matrix.msc4407.receive.sticky_event`
