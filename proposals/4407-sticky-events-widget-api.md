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
    state_key?: string;
    type: string;
    content: unknown;
    room_id?: string;
    delay?: number; // from https://github.com/matrix-org/matrix-spec-proposals/pull/4157
    sticky_duration_ms?: number;
}
```


### Capabilities

Two new capabilities will be introduces:

- `m.send_receive_sticky_events`\
  allows to send sticky events by using the optional `sticky_duration_ms` property in a `fromWidget send_event` widget action.
  All other `m.send.*` capabilities still apply. This capability allows sending sticky events of those types.


## Alternatives

## Unstable prefix

The following strings will have unstable prefixes:

- The send delayed event capability:\
  `m.send_receive_sticky_events` -> `org.matrix.msc4407.send_receive_sticky_events`
