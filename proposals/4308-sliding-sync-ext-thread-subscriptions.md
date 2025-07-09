MSC4308: Thread Subscriptions extension to Sliding Sync
===

## Background and Summary

Threads were introduced in [version 1.4 of the Matrix Specification](https://spec.matrix.org/v1.13/changelog/v1.4/) as a way to isolate conversations in a room, making it easier for users to track specific conversations that they care about (and ignore those that they do not).

Threads Subscriptions are proposed in [MSC4306](https://github.com/matrix-org/matrix-spec-proposals/blob/rei/msc_thread_subscriptions/proposals/4306-thread-subscriptions.md) as a way for users to efficiently indicate which threads they care about, for the purposes of receiving updates.

Sliding Sync is proposed in [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/blob/erikj/sss/proposals/4186-simplified-sliding-sync.md) as a paginated replacement to `/_matrix/client/v3/sync` with smaller response bodies and lower latency.
The `/_matrix/client/v3/sync` endpoint is notorious in real-world applications of Matrix for producing large response bodies (to the amplified detriment of mobile clients) and the high latency caused by waiting for the server to calculate that full payload.

This MSC proposes an 'extension' to Sliding Sync that allows clients to opt-in to receiving updates to the user's thread subscriptions.

## Proposal

The Sliding Sync request format is extended to include the `thread_subscriptions` extension as follows:

```jsonc
{
  // ...
  
  "extensions": {
    // ...
    
    // Used to opt-in to receiving updates to thread subscriptions.
    "thread_subscriptions": {
      // Maximum number of thread subscription changes to receive.
      // Defaults to 100.
      "limit": 100,
    }
  }
}
```

The response format is then extended to compensate:

```jsonc
{
  // ...
  
  "extensions": {
    // ...
    
    // Returns a limited window of updates to thread subscriptions
    "thread_subscriptions": {
      "changed": [
        {
          "room_id": "!roomid:example.org",
          "root_event_id": "$abc123",
          
          "subscribed": true,
          
          // must be present when subscribed is true,
          // but must be absent when subscribed is false
          "automatic": true
        },
        {
          "room_id": "!roomid:example.org",
          "root_event_id": "$def456",
          
          "subscribed": false
        },
        ...
      ]
    }
  }
}
```

## Potential issues

When clients start a fresh sync with no initial state, it may be the case that there is a backlog of many thread_subscriptions to send down to the client.

Servers MAY choose to return Thread Subscription Settings in an order that is more heuristically-useful to the client, such as 'most recently updated' or 'threads with most recent activity first', instead of 'oldest first'. This could be either for all Thread Subscriptions, or only the backlogged ones.

## Alternatives


## Limitations


## Security considerations

- No particular security issues anticipated.

## Unstable prefix

TODO

## Dependencies

- [MSC4186 Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/blob/erikj/sss/proposals/4186-simplified-sliding-sync.md)
- [MSC4306 Threads Subscriptions](https://github.com/matrix-org/matrix-spec-proposals/blob/rei/msc_thread_subscriptions/proposals/4306-thread-subscriptions.md)
