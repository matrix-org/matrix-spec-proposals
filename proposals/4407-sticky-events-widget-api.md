# Sticky Events (widget-api)

With [MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354) a way to sticky events is introduced.
Sticky events are room events with a time limited delivery guarantee. They will be synced by participating clients even with gappy syncs.
(For the duration of the sticky duration `sticky_duration_ms`)

This msc only specifies how the widget api uses this concept. [MSC4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354)
gives more details about the sticky events themselves.

Exposing sticky events to the widget is required for widgets implementing MatrixRTC.
Sticky events are needed for encrypted MatrixRTC memberships that get reliably delivered.

Since ElementCall (EC) is a widget and based on MatrixRTC this widget api proposal is required for EC to work.

## Proposal

### Sending Sticky events

We extend the `"send_event"` request defined by [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762)
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

Two new capabilities will be introduces:

- `m.send.sticky_event`\
  allows to send sticky events by using the optional `sticky_duration_ms` property in a `fromWidget send_event` widget action.
  All other `m.send.*` capabilities still apply. This capability allows sending sticky events of those types.
- `m.receive.sticky_event`\
  If this capability is allowed the client will make sure the widget is aware about events that are currently sticky.
  All events that are currently stikcy of types that are allowed by `m.send.*` capabilities will be included.

### Widget Client Implementation
This has the following behavior impact in the widget client implementation:
 - on widget startup the client will send all sticky events the widget is allowed to see.
 - on capability negotiation where the widget gets granted `m.receive.sticky_event` the client will send all sticky events the widget is allowed to see.

 If the capability `m.send.sticky_event` is granted and the client receives a send event with `sticky_duration_ms` set, the client has to send a sticky event
 as described in the [Sticky Events Widget API 4354](https://github.com/matrix-org/matrix-spec-proposals/pull/4354) using the `sticky_duration_ms`.

## Alternatives

## Unstable prefix

The following strings will have unstable prefixes:

- The send sticky event capability:\
  `m.send.sticky_event` -> `org.matrix.msc4407.send.sticky_event`
- The send sticky event capability:\
  `m.receive.sticky_event` -> `org.matrix.msc4407.receive.sticky_event`
