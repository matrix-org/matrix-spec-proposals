# Delayed Events (widget-api)

With [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) a way to send Delayed events is introduced.
Delayed events are events that will be inserted into the dag (and distributed to all clients and federating
servers) a time after **now** (based on a delay that can be refreshed).

Those events are useful to implement scheduled messages or a last will mechanisms. Since the delayed events are refreshable,
it is possible to send an event with a short timeout and send restarts to that timeout. This behaves like a heartbeat and
the event is sent once the heartbeat stops: As a last will.

This msc only specifies how the widget api uses this concept. [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140)
gives more details about the delayed events themselves.

Exposing delayed events to the widget is required for widgets implementing MatrixRTC.
Delayed events are needed for reliable MatrixRTC memberships that get cleaned up when a client looses network connection.

Since ElementCall (EC) is a widget and based on MatrixRTC this widget api proposel is required for EC to work.

## Proposal

### Sending delayed events

We extend the `"send_event"` request defined by [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762)
as follows:

```jsonc
{
    state_key?: string;
    type: string;
    content: unknown;
    room_id?: string;
    delay?: number; // new field
}
```

and the `"send_event"` response:

```jsonc
{
    room_id: string;
    event_id?: string; // now optional
    delay_id?: string; // new field
}
```

To provide the same properties needed for [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140).
The client is responsible to check for the `delay` field of the widget action and send the correct http request if it
is present.

### Sending `update_delayed_event` actions

```jsonc
{
    "direction": "fromWidget",
    "action":"update_delayed_event",
    "data":{
        "delay_id": string,
        "action":"cancel"|"send"|"refresh"
    }
}
```

The response is empty on success or otherwise a widget error response.

### Capabilities

Two new capabilities will be introduces:

- `m.send.delayed_event`\
  allows to send delayed events by using the optional `delay` property in a `fromWidget send_event` widget action.
- `m.update_delayed_event`\
  allows to update delayed events using the `fromWidget update_delayed_event` widget action.

Receiving events does not require a special permission since delayed events are not distinguishable from normal events
from the receiver side.

For sending a delayed event two capabilities are required. One for sending the event type itself and the `m.send.delayed_event`
capability to send it as a delayed event.

## Alternatives

A more granular capability configuration for sending delayed events can be imagined. Where
each event type gets its own capability to sent this type with a delay. Since we always need the capability for the
event type itself it might be sufficient to ask for delayed event sending in general.

But it is then possible to send any of the events the widget can sent as delayed events.

## Unstable prefix

The following strings will have unstable prefixes:

- The widget action:\
  `update_delayed_event` -> `org.matrix.msc4157.update_delayed_event`
- The send delayed event capability:\
  `m.send.delayed_event` -> `org.matrix.msc4157.send.delayed_event`
- The update delayed event capability:\
  `m.update_delayed_event` -> `org.matrix.msc4157.update_delayed_event`
