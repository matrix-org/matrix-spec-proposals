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

Events can contain a `m.will_expire: "running" | "expired" | "ended"` field.
This is an enum marking the event as
expired `m.will_expire: "expired" | "ended"` or still alive `m.will_expire: "running"`.
This field lives outside the ciphertext content (hence it also works for encrypted
events) and is set via the usual `PUT` request if the content contains the additional
`m.will_expire: 10` field (similar how it is done with relations), with the desired
timeout duration in seconds.

Request

```json
{
    "m.will_expire": 10,
    "body": "hello"
}
```

If the homeserver detects a `m.expired` field it will store and distribute the
event as hiding the timeout duration:

```json
{
  "content":{
    "m.will_expire": "running",
    "body": "hello",
  },
  "other_fields":"sender, origin_server_ts ..."
}
```

The response to the client will be:

```json
{
  "eventId": "hash_id",
  "expire_refresh_token": "hash_refresh",
}
```

The default response is extended with the `expire_refresh_token` which
can be used to reset the expiration timeout (in this example 10 seconds).
A new unauthenticated endpoint is introduced:
`PUT /_matrix/client/v3/expiration/{refresh_method}`
where the `refresh_method` is either: `refresh`, `end`
The body contains the refresh token so the homeserver knows what to refresh.

```json
{
  "expire_refresh_token": "hash_refresh",
}
```

The information required to call this endpoint is very limited so that almost
no metadata is leaked when. This allows to share a refresh link to a different
service (an SFU for instance) that can track the current client connection state,
and pings the HS to refresh and informs the HS about a disconnect.

The homeserver does the following when receiving an event with `m.expired`

- It generates a token and stores it alongside with the time of retrieval,
the eventId and the expire duration.
- Starts a counter for the stored expiation token.
  - If a `PUT /_matrix/client/v3/expiration/refresh` is received, the
  timer is restarted with the stored expire duration.
  - If a `PUT /_matrix/client/v3/expiration/end` is received, the
  event _gets ended_.
  - If the timer times out, the event _gets expired_.
  - If the event is a state event only the latest/current state is considered. If
  the homeserver receives a new state event without `m.expires` but with the same
  state key, the expire_refresh_token gets invalidated and the associated timer is
  stopped.

The event _gets expired_/_gets ended_ means:

- The homeserver **sends a new event** that is a copy of the previous event but:
  - If it gets _expired_ the event will include: `"m.will_expire": "expired"`
  - If it gets _ended_ the event will include: `"m.will_expire": "ended"`.
  - Additionally it includes a relation to the original event with `rel_type: "m.expire.relationship"`
  
    ```json
    "m.relates_to": {
      "event_id": "$original_event",
      "rel_type": "m.expire.relationship"
    },
    "m.will_expire": "ended" | "expired",
    ```

- The homeserver stops the associated timer and invalidates (deletes) the `expire_refresh_token`

So for each event that is sent with `m.will_expire: X` where X is duration in
seconds > 0. The homeserver will sent another event which can be used to trigger
logic on the client. This allows for any generic timeout logic.

Timed messages/reminders could also be implemented using this where clients ignore
the `"will_expire":"running"` events for a specific event type but render the
`"will_expire":"expired"` events.

## Potential issues

## Alternatives

[MSC4018](https://github.com/matrix-org/matrix-spec-proposals/pull/4018) also
proposes a way to make call memberships reliable. It uses the client sync loop as
an indicator to determine if the event is expired. Instead of letting the SFU
inform about the call termination or using the call app ping loop like we propose
here.

---
It might not be necessary to change the value of `"m.will_expire" = 10` to
`"m.will_expire" = "running"` it makes it easier to understand and also
hides more potential metadata but it is questionable if that bring any benefit.

---
The name `m.will_expire` has been chosen since it communicates that it becomes
invalid. And that it is an event that automatically changes state
(`will_expire` vs `expired`). But it does not imply what expired vs non expired
means, it is flexible in how can be used.
Alternatives could by:

- `m.alive`
  - pro: communicates it might change (alive is always temporal)
  - con: ver strong bias on how to use it `valid/invalid`
- `m.timeout`
  - pro: very unbiased in how its used - timeout over can also mean the client
  will show a reminder.
  - pro: clear that it has something to do with time.
  - con: not so clear the homeserver will automatically do sth.
  - con: not so clear that this timeout can be refreshed?

## Security considerations

We are using unauthenticated endpoint to refresh the expirations. Since we use
the token it is hard to guess a correct endpoint and randomly end `will_expire`
events.

It is an intentional decision to not provide an endpoint like
`PUT /_matrix/client/v3/expiration/room/{roomId}/event/{eventId}`
where any client with access to the room could also `end` or `refresh`
the expiration. With the token the client sending the event has ownership
over the expiration and only intentional delegation of that ownership
(sharing the token) is possible.

On the other hand the token makes sure that the instance gets as little
information about the matrix metadata of the associated `will_expire` event.

## Unstable prefix

## Dependencies

