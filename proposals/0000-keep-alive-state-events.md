# MSC0000: Expiring events with keep alive functionality

Currently there is not mechanism for a client to provide a reliable way of
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
  "content": {
    "m.will_expire": 10,
    "other_content": "hello"
  }
}
```

If the homeserver detects a `m.expired` field it will store and distribute the
event as:

```json
{
  "content": {
    "m.will_expire": "running",
    "other_content": "hello"
  }
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

The information of this endpoint is very limited so that almost no metadata is
leaked when using this endpoint. This allows to share a refresh link to a different
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

## Security considerations

## Unstable prefix

## Dependencies
