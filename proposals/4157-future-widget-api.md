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
    future_timeout?: number; // new field
    parent_future_id?: string; // new field
}
```

and the `"send_event"` response:

```jsonc
{
    room_id: string;
    event_id?: string; // now optional
    parent_future_id?: string; // new field
}
```

to provide the same properties needed for [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140).
The client is responsible to check
for the field `future_timeout` or `parent_future_id` of the widget action and send a `/send` or `/send_future` http request
if one of them is present.

Additionally the response is extended with the tokens and the `parent_future_id`.

All other details about the future concept can be found in [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140)
so here we intentionally don't mention any of the details about futures.

### Sending `update_future` actions

```jsonc
{
    "direction": "fromWidget",
    "action":"update_future",
    "data":{
        "future_id":,
        "action":"cancel"|"send"|"refresh"
    }
}
```

response

```jsonc
{}
```

or an error response if an error occurred.