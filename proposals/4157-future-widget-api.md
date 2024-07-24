# Futures for the widget api

With [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) a way to send Future events is introduced.
Futures are events that are send **now** but will be inserted into the dag (and distributed to all clients and federating
servers) a time after **now** (based on timeout or delegation conditions).

This is an extension to the client server api to expose Futures to widgets.
This can be useful for numerous widgets. It is required for widgets implementing MatrixRTC.
Futures are needed for reliable MatrixRTC memberships that get cleaned up when a client looses network connection.

Since ElementCall (EC) is a widget and based on MatrixRTC this widget api proposel is required for EC to work.

## Proposal

### Sending Future events

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

to provide the same properties needed for [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140).
The client is responsible to check
for the field `delay` of the widget action and send the correct http request
if one of it is present.

All other details about the future concept can be found in [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140)
so here we intentionally don't mention any of the details about futures.

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

- `m.send.delay_events`\
  allows to send delayed events by using the optional `delay` property in a `fromWidget send_event` widget action.
- `m.update_delayed_event`\
  allows to update delayed events using the `fromWidget update_delayed_event` widget action.

## Unstable prefix

- `update_delayed_event` -> `org.matrix.msc4157.update_delayed_event`
- `m.send.delayed_event` -> `org.matrix.msc4157.send.delayed_event`
- `m.update_delayed_event` -> `org.matrix.msc4157.update.delayed_event`
