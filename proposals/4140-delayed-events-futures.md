# MSC4140: Delayed events (Futures)

Allowing to schdule/delay events would solve numerous issues in
matrix.

- Updating call member events after the user disconnected.
- Sending scheduled messages (send at a specific time)
- Creating self destructing events (By sending a delayed redact)

Currently there is no mechanism for a client to reliably that an event is still valid.
The only way to update an event is to post a new one.
In some situations the client just looses connection or fails to sent the expired
version of the event. This proposal also includes a expiration/timeout
system so that those scenarios are also covered.

We want to send an event in advance
to the homeserver but let the homeserver decide the time when its actually added to the
DAG.
The condition for actually sending the delayed event would could be a timeout or a external trigger via a synapse endpoint.

## Proposal

To make this as generic as possible, the proposed solution is to allow sending
multiple presigned events and delegate the control of when to actually send these
events to an external services. This allows to a very flexible way to mark events as expired,
since the sender can choose what event will be sent once expired.

We call those delayed events `Futures`.

A new endpoint is introduced:
`PUT /_matrix/client/v3/rooms/{roomId}/send/future/{txnId}`
It behaves exactly like the normal send endpoint except that that it allows
to send a list of event contents. The body looks as following:

```json
{
  "m.timeout": 10,
  "m.send_on_timeout": {
    "content": sendEventBody0,
    "type": "m.room.message",
  },

  "m.send_on_action:${actionName}": {
    "content": sendEventBody1,
    "type": "m.room.message"
  },

  // optional
  "m.send_now": {
    "content": sendEventBody2,
    "type": "m.room.message"
    },
}
```

Each of the `sendEventBody` objects are exactly the same as sending a normal
event.

There can be an arbitrary amount of `actionName`s.

All of the fields are optional except the `timeout` and the `send_on_timeout`.
This guarantees that all tokens will expire eventually.

The homeserver can set a limit to the timeout and return an error if the limit
is exceeded.

### Response

The response will mimic the request:

```json
{
  "m.send_on_timeout": { "eventId": "id_hash" },
  "m.send_on_action:${actionName}": { "eventId": "id_hash" },

  "future_token": "token",

  // optional
  "m.send_now": { "eventId": "id_hash" }
}
```

### Delegating futures

The `token` can be used to call another future related endpoint:
`POST /_matrix/client/v3/futures/refresh` and `POST /_matrix/client/v3/futures/action/${actionName}`.
where the body is:

```json
{
  "future_token": "token"
}
```

The information required to call this endpoint is very limited so that almost
no metadata is leaked. This allows to share a refresh link to a different
service. This allows to delegate the send time. An SFU for instance, that tracks the current client connection state,
and pings the HS to refresh and call a dedicated action to communicate
that the user has intentionally left the conference.

The homeserver does the following when receiving a Future.

- It **sends** the optional `m.send_now` event.
- It **generates** a `future_token` and stores it alongside with the time
  of retrieval, the event list and the timeout duration.
- **Starts a timer** for the stored `future_token`.

  - If a `PUT /_matrix/client/v3/futures/refresh` is received, it
    **restarts the timer** with the stored timeout duration.
  - If a `PUT /_matrix/client/v3/futures/action/${actionName}` is received, it **sends the associated action event**
    `m.action:${actionName}`.
  - If the timer times out, **it sends the timeout event** `m.send_timeout`.
  - If the future is a state event and includes a `m.send_now` event
    the future is only valid while the `m.send_now`
    is still the current state:

    - This means, if the homeserver receives
      a new state event for the same state key, the **`future_token`**
      **gets invalidated and the associated timer is stopped**.

    - There is no race condition here since a possible race between timeout and
      new event will always converge to the new event:
      - Timeout -> new event: the room state will be updated twice. once by
        the content of the `m.send_on_timeout` event but later with the new event.
      - new event -> timeout: the new event will invalidate the future. No

- After the homeservers sends a timeout or action future event, the associated
  timer and `future_token` is canceled/invalidated.

So for each Future the client sends, the homeserver will send one event
conditionally at an unknown time that can trigger logic on the client.
This allows for any generic timeout logic.

Timed messages/reminders or ephemeral events could be implemented using this where
clients send a redact as a future or a room event with intentional mentions.

In some scenarios it is important to allow to send an event with an associated
future at the same time.

- One example would be redacting an event. It only makes sense to redact the event
  if it exists.
  It might be important to have the guarantee, that the redact is received
  by the server at the time where the original message is sent.
- In the case of a state event we might want to set the state to `A` and after a
  timeout reset it to `{}`. If we have two separate request sending `A` could work
  but the event with content `{}` could fail. The state would not automatically
  reset to `{}`.

For this usecase an optional `m.send_now` field can be added to the body.

### Getting running futures

Using `GET /_matrix/client/v3/futures` it is possible to get the list of all running futures.
This is an authenticated endpoint. It sends back the json
of the final events how they will end up in the DAG with the associated `future_token`.

```json
[
  {
    "m.send_now": finalEvent_0,
    "m.send_on_timeout": finalEvent_1,
    ...,

    "future_token":"token"
  },
]
```

This can be used so clients can optionally display events
that will be send in the future.
For self destructing messages it is recommanded to include
this information in the event itself so that the usage of
this endpoint can be minimized.

## Usecase specific considerations

### MatrixRTC

We want can use the actions and the timeout for matrix rtc for the following situations

- If the client takes care of its membership, we use a short timeout value (around 5-20 seconds)
  The client will have to ping the refresh endpoint approx every 2-19 seconds.
- When the SFU is capable of taking care of managing our connection state and we trust the SFU to
  not disconnect a really long value can be chosen (approx. 2-10hours). The SFU will then only send
  an action once the user disconnects or looses connection (it could even be a different action for both cases
  handling them differently on the client)
  This significantly reduces the amount of calls for the `/future` endpoint since the sfu only needs to ping
  once per session (per user) and every 2-5hours (instead of every `X` seconds.)

### Self destructing messages

This MSC also allows to implement self destructing messages:

`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`

```json
{
  "m.text": "my msg"
}
```

`PUT /_matrix/client/v3/rooms/{roomId}/send/future/{txnId}`

```json
{
  "m.timeout": 10*60,
  "m.send_on_timeout": {
    "type":"m.room.readact",
    "content":{
      "redacts": "EvId"
    }
  }
}
```

## EventId template variable

It would be useful to be able to send redactions and edits as one http request.
This would make sure that the client cannot loose connection after sending the first event.
For instance sending a self destructing message without the redaction.

The optional proposal is to introduce template variables that are only valid in `Future` events.
`$m.send_now.event_id` in the content of one of the `m.send_on_action:${actionName}` and
`m.send_on_timeout` contents this template variable can be used.
The **Self destructing messages** example would simplify to:

`PUT /_matrix/client/v3/rooms/{roomId}/send/future/{txnId}`

```json
{
  "m.send_now":{
    "type":"m.room.message",
    "content":{
      "m.text": "my msg"
    }
  },
  "m.timeout": 10*60,
  "m.send_on_timeout": {
    "type":"m.room.readact",
    "content":{
      "redacts": "$m.send_now.event_id"
    }
  }
}
```

## Potential issues

## Alternatives

[MSC4018](https://github.com/matrix-org/matrix-spec-proposals/pull/4018) also
proposes a way to make call memberships reliable. It uses the client sync loop as
an indicator to determine if the event is expired. Instead of letting the SFU
inform about the call termination or using the call app ping loop like we propose
here.

---

The following names for the endpoint are considered

- Future
- DelayedEvents
- RetardedEvents

---

The `m.send_now` field could not be part of the future. This would also
mitigate the need for the `$m.send_now.event_id` template variable.

It would come with the cost that there is no way to guarantee, taht the current state and the future are recieved by the homeserver.
The client would need to send the events in sequence, so the
connection could be lost between the now event and the future.
It is expected that this is a very rare case.

Sequence wise it might make sense to not include the `m.send_now` in this
msc and solve the topic by a good and flexible batch sending solution
independent of this PR. (then the future and the event could be sent in one batch giving the same result as the `m.send_now` field)

## Security considerations

We are using an unauthenticated endpoint to refresh the expirations. Since we use
the token it is hard to guess a correct request and force one of the actions
events of the Future.

It is an intentional decision to not provide an endpoint like
`PUT /_matrix/client/v3/futures/room/{roomId}/event/{eventId}`
where any client with access to the room could also `end` or `refresh`
the expiration. With the token the client sending the event has ownership
over the expiration and only intentional delegation of that ownership
(sharing the token) is possible.

On the other hand the token makes sure that the instance gets as little
information about the matrix metadata of the associated `future` event. It cannot
even tell with which room or user it is interacting.

## Unstable prefix

use `io.element.` instead of `m.` as long as the msc is not stable.

## Dependencies
