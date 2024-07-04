# Futures for the widget api

With [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) a way to send Future events is introduced. Futures are events that are send **now** but will
be inserted into the dag (and distributed to all clients and federating servers) a time after **now** (based on timeout or delegation conditions).

This is an extension to the client server api to expose Futures to widgets.
This can be useful for numerous widgets. It is required for widgets implementing MatrixRTC.
Futures are needed for reliable MatrixRTC memberships that get cleaned up when a client looses network connection.

Since ElementCall (EC) is a widget and based on MatrixRTC this widget api proposel is required for EC to work.

## Proposal

We extend the send
`"send_event"` request:

```
{
    state_key?: string;
    type: string;
    content: unknown;
    room_id?: string;

    future_timeout?: number;
    future_group_id?: string;
}
```

and the `"send_event"` response:

```
{
    room_id: string;
    event_id?: string;

    future_group_id?: string;
    send_token?: string;
    cancel_token?: string;
    refresh_token?: string;
}
```

to provide the same properties needed for [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140). The client is responsible to check
for the field `future_timeout` or `future_group_id` of the widget action and send a `/send` or `/send_future` http request
if one of them is present.

Additionally the response is extended with the tokens and the `future_group_id`.

All other details about the future concept can be found in [MSC4140](https://github.com/matrix-org/matrix-spec-proposals/pull/4140) so here we intentionally don't mention
any of the details about futures.
