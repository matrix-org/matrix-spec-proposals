# Delayed Events (widget-api)

With [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) a way to send Delayed events is introduced.
Delayed events are events that will be inserted into the dag (and distributed to all clients and federating
servers) a time after **now** (based on a delay that can be refreshed).

Those events are useful to implement scheduled messages or a "last will" mechanism. Since the delayed events are refreshable,
it is possible to send an event with a short timeout and send restarts to that timeout. This behaves like a heartbeat and
the event is sent once the heartbeat stops: As a last will.

This MSC only specifies how the widget api uses this concept.
[MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) gives more details about the delayed events themselves.

Exposing delayed events to the widget is required for widgets implementing MatrixRTC.
Delayed events are needed for reliable MatrixRTC memberships that get cleaned up when a client looses network connection.

Since Element Call (EC) is a widget and based on MatrixRTC this widget api proposal is required for EC to work.

## Proposal

### Sending delayed events

To schedule a delayed event, widgets use a new `fromWidget` request with action `send_delayed_event`:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestId": "generated-id-1234",
  "action": "send_delayed_event",
  "data": {
    "state_key": "",
    "type": "m.room.topic",
    "content": {
      "topic": "Hello world!"
    },
    "delay_ms": 60000
  }
}
```

`data` takes the same properties as the `send_event` request defined by
[MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762), plus a required `delay_ms`: the number of
milliseconds the homeserver should wait before sending the event.

If the widget did not get approved for the capabilities required to send the event as a delayed event, the client MUST
send an error response (as required currently by the capabilities system for widgets).

Otherwise, the client handles the request like a `send_event` request, except that it schedules the event with the
`PUT /_matrix/client/v3/rooms/{roomId}/delayed_event/{eventType}/{txnId}` endpoint of
[MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140), and responds with the `delay_id` returned by
the homeserver:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestId": "generated-id-1234",
  "action": "send_delayed_event",
  "data": {
    "state_key": "",
    "type": "m.room.topic",
    "content": {
      "topic": "Hello world!"
    },
    "delay_ms": 60000
  },
  "response": {
    "room_id": "!room:example.org",
    "delay_id": "1234567890"
  }
}
```

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

### Getting the delayed event limits

[MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) lets the homeserver limit the delay of a delayed
event and the number of delayed events a user can have scheduled. The homeserver advertises these limits in the
`m.delayed_events`
[capability](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4140-delayed-events-futures.md#delayed-event-limits-as-a-capability).
A widget cannot call `GET /_matrix/client/v3/capabilities` itself, so the client exposes the capability through a new
`fromWidget` action, `get_delayed_events_capability`:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestId": "generated-id-1234",
  "action": "get_delayed_events_capability",
  "data": {}
}
```

If the widget did not get approved for the `m.send.delayed_event` capability, the client MUST send an error response
(as required currently by the capabilities system for widgets).

Otherwise, the client responds with the capability as advertised by its homeserver:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestId": "generated-id-1234",
  "action": "get_delayed_events_capability",
  "data": {},
  "response": {
    "m.delayed_events": {
      "max_delay_ms": 86400000,
      "max_scheduled": 10
    }
  }
}
```

The `response` mirrors the `capabilities` object of `GET /_matrix/client/v3/capabilities`, limited to
`m.delayed_events`. `m.delayed_events` is absent if the homeserver does not advertise the capability, in which case the
widget SHOULD assume that delayed events are disabled, as described in MSC4140.

If the client cannot get the capabilities from the homeserver, it responds with a widget error response. The client
SHOULD include the homeserver's error as `matrix_api_error`
([MSC2813](https://github.com/matrix-org/matrix-spec-proposals/pull/2813)), so that the widget can tell a transient
failure from an unsupported homeserver.

### Capabilities

Two new capabilities will be introduces:

- `m.send.delayed_event`\
  allows to send delayed events using the `fromWidget send_delayed_event` widget action.
- `m.update_delayed_event`\
  allows to update delayed events using the `fromWidget update_delayed_event` widget action.

Receiving events does not require a special permission since delayed events are not distinguishable from normal events
from the receiver side.

For sending a delayed event two capabilities are required. One for sending the event type itself and the `m.send.delayed_event`
capability to send it as a delayed event.

The `get_delayed_events_capability` action does not get its own capability. It requires the `m.send.delayed_event`
capability, since the limits only matter to a widget that sends delayed events.

## Alternatives

A more granular capability configuration for sending delayed events can be imagined. Where
each event type gets its own capability to sent this type with a delay. Since we always need the capability for the
event type itself it might be sufficient to ask for delayed event sending in general.

But it is then possible to send any of the events the widget can sent as delayed events.

## Unstable prefix

The following strings will have unstable prefixes:

- The send delayed event widget action:\
  `send_delayed_event` -> `org.matrix.msc4157.send_delayed_event`
- The update delayed event widget action:\
  `update_delayed_event` -> `org.matrix.msc4157.update_delayed_event`
- The send delayed event capability:\
  `m.send.delayed_event` -> `org.matrix.msc4157.send.delayed_event`
- The update delayed event capability:\
  `m.update_delayed_event` -> `org.matrix.msc4157.update_delayed_event`
- The get delayed events capability widget action:\
  `get_delayed_events_capability` -> `org.matrix.msc4157.get_delayed_events_capability`

Only call/support the `send_delayed_event` action if an API version of `org.matrix.msc4157_send_delayed_event` is
advertised.
