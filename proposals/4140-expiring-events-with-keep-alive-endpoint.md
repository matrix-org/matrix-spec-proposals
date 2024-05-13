# MSC4140: Expiring events with keep alive endpoint

Currently there is no mechanism for a client to provide a reliable way of
communicating that an event is still valid. The best expiration method is to post
another event that is stores that it is expired.
In some situations the client just looses connection or fails to sent the expired
version of the event.
A generic way is desired in which the event gets marked as expired by the homeserver.

Clients can then perform custom logic based on if the event is in valid or
expired state.

This is particularly interesting in the context of matrixRTC where we want
to ignore expired state events of users who left the call without sending a new
state empty `m.call.member` event.

We would like the homeserver to mark this event as expired in a reasonable
time window after a user disconnected.

## Proposal

The proposed solution is to allow sending multiple presigned events and delegate
the control of when to actually send these events to an external services.

We call those events `Futures`.

A new endpoint is introduced:
`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}/future`
and
`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}/future`
It behaves exactly like the normal send endpoint except that that it allows
to send a list of event contents. The body looks as following:

```json
{
  "m.timeout": 10,
  "m.send_on_timeout": {...sendEventBody},
  
  "m.send_on_action:${actionName}": {...sendEventBody},

  // optional
  "m.send_now": {...sendEventBody},
}
```

Each of the `sendEventBody` objects are exactly the same as sending a normal
event.

There can be an arbitrary amount of `actionName`s.

All of the fields are optional except the `timeout` and the `send_on_timeout`.
This guarantees that all tokens will expire eventually.

The homeserver can set a limit to the timeout and return an error if the limit
is exceeded.

The response will mimic the request:

```json
{

  "m.send_on_timeout": {
    "eventId": "id_hash"
  },
  "m.send_on_action:${actionName}": {
    "eventId": "id_hash"
  },
  
  "future_token": "token",
  
  // optional
  "m.send_now": { "eventId": "id_hash"},
}
```

The `token` can be used to call another future related endpoint:
`PUT /_matrix/client/v3/futures/refresh` and `PUT /_matrix/client/v3/futures/action/${actionName}`.
where the body is:

```json
{
  "future_token":"token"
}
```

The information required to call this endpoint is very limited so that almost
no metadata is leaked. This allows to share a refresh link to a different
service (an SFU for instance) that can track the current client connection state,
and pings the HS to refresh and call a dedicated action to communicate
that the user has intentionally left the conference.

The homeserver does the following when receiving a Future.

- It sends the optional `m.send_now` event.
- It generates a `future_token` and stores it alongside with the time
of retrieval, the event list and the timeout duration.
- Starts a timer for the stored `future_token`.
  - If a `PUT /_matrix/client/v3/futures/refresh` is received, the
  timer is restarted with the stored timeout duration.
  - If a `PUT /_matrix/client/v3/futures/action/${actionName}` is received, one of
  the associated `m.action:${actionName}`
  event will be send.
  - If the timer times out, the one of the `m.send_timeout` event will be sent.
  - If the future
    - is a state event (`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}/future`)
    - and includes a `m.send_now` event

    the future is only valid while the `m.send_now`
    is still the current state. This means, if the homeserver receives
    a new state event for the same state key, the `future_token`
    gets invalidated and the associated timer is stopped.
    - There is no race condition here since a possible race between timeout and
    new event will always converge to the new event:
      - Timeout -> new event: the room state will be updated twice. once by
      the content of the `m.send_on_timeout` event but later with the new event.
      - new event -> timeout: the new event will invalidate the future. No
- When a timeout or action future is sent, the homeserver stops the associated
timer and invalidates (deletes) the `future_token`.

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

## Potential issues

## Alternatives

[MSC4018](https://github.com/matrix-org/matrix-spec-proposals/pull/4018) also
proposes a way to make call memberships reliable. It uses the client sync loop as
an indicator to determine if the event is expired. Instead of letting the SFU
inform about the call termination or using the call app ping loop like we propose
here.

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

## Dependencies

