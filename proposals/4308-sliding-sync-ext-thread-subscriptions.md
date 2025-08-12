MSC4308: Thread Subscriptions extension to Sliding Sync
===

## Background and Summary

Threads were introduced in [version 1.4 of the Matrix Specification](https://spec.matrix.org/v1.13/changelog/v1.4/) as a way to isolate conversations in a room, making it easier for users to track specific conversations that they care about (and ignore those that they do not).

Threads Subscriptions are proposed in [MSC4306](https://github.com/matrix-org/matrix-spec-proposals/blob/rei/msc_thread_subscriptions/proposals/4306-thread-subscriptions.md) as a way for users to efficiently indicate which threads they care about, for the purposes of receiving updates.

Sliding Sync is proposed in [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/blob/erikj/sss/proposals/4186-simplified-sliding-sync.md) as a paginated replacement to `/_matrix/client/v3/sync` with smaller response bodies and lower latency.
The `/_matrix/client/v3/sync` endpoint is notorious in real-world applications of Matrix for producing large response bodies (to the amplified detriment of mobile clients) and the high latency caused by waiting for the server to calculate that full payload.

This MSC proposes an 'extension' to Sliding Sync that allows clients to opt-in to receiving real-time updates to the user's thread subscriptions.

To handle the case in which there have been many updates to the user's thread subscriptions and there are too many to return in
Sliding Sync, a new companion endpoint is proposed to allow backpaginating thread subscriptions on the client's terms.

## Proposal

### Sliding Sync extension

The Sliding Sync request format is extended to include the `thread_subscriptions` extension as follows:

```jsonc
{
  // ...

  "extensions": {
    // ...

    // Used to opt-in to receiving changes to thread subscriptions.
    "thread_subscriptions": {
      // Maximum number of thread subscription changes to receive
      // in the response.
      // Defaults to 100.
      // Servers may impose a smaller limit than what is requested here.
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

    // Returns a limited window of changes to thread subscriptions
    // Only the latest changes are returned in this window.
    "thread_subscriptions": {
      "changed": {
        "!roomId1:example.org": {
          // New subscription
          "$threadId1": {
            "automatic": true
          },
          // New subscription
          // or subscription changed to manual
          "$threadId2": {
            "automatic": false
          },
          // Represents a removed subscription
          "$threadId3": null
        },
        "$roomId2:example.org": {
          // ...
        }
        // ...
      },

      // A pair of tokens that can be used to backpaginate other thread subscription
      // changes that occurred since the last sync, but that were not
      // included in this response.
      //
      // The tokens are to be used with the `/thread_subscriptions` endpoint
      // as `from` and `to` parameters with `dir=b`.
      //
      // Only present when some thread subscriptions have been missed out
      // from the response because there are too many of them.
      "prev": {"from": "OPAQUE_TOKEN", "to": "OPAQUE_TOKEN"}
    }
  }
}
```

If two changes occur to the same subscription, only the latter change ever needs
to be sent to the client. \
Servers do not need to store intermediate subscription states.


### Companion endpoint for backpaginating thread subscription changes

```
GET /_matrix/client/v1/thread_subscriptions
```

URL parameters:

- `dir` (string, required): always `b` (backward), to mirror other pagination
  endpoints. The forward direction is not yet specified to be implemented.

- `from` (string, optional): a token used to continue backpaginating \
  The token is either acquired from a previous `/thread_subscriptions` response,
  or a Sliding Sync response. \
  The token is opaque and has no client-discernible meaning. \
  If this token is not provided, then backpagination starts from the 'end'.

- `to` (string, optional): a token used to limit the backpagination \
  The token can be acquired from a Sliding Sync response.

- `limit` (int, optional; default `100`): a maximum number of thread subscriptions to fetch
  in one response. \
  Must be greater than zero. Servers may impose a smaller limit than requested.

  
Response body:

```jsonc
{
  // Required
  "chunk": {
    "!roomId1:example.org": {
      // New subscription
      "$threadId1": {
        "automatic": true
      },
      // New subscription
      // or subscription changed to manual
      "$threadId2": {
        "automatic": false
      },
      // Represents a removed subscription
      "$threadId3": null
    },
    "$roomId2:example.org": {
      // ...
    }
  },
  // If there are still more thread subscriptions to fetch,
  // a new `from` token the client can use to walk further
  // backwards.
  "end": "OPAQUE_TOKEN"
}
```

If two changes occur to the same subscription, only the latter change ever needs
to be sent to the client. \
Servers do not need to store intermediate subscription states.

The pagination structure of this endpoint matches that of the `/messages` endpoint, but fixed
to the backward direction (`dir=b`).
For simplicity, the `start` response field is removed as it is entirely redundant.

## Potential issues


## Alternatives


## Limitations


## Security considerations

- No particular security issues anticipated.

## Unstable prefix

Whilst this proposal is unstable, a few unstable prefixes must be observed by experimental implementations:

- the Sliding Sync extension is called `io.element.msc4308.thread_subscriptions` instead of `thread_subscriptions`
- the companion endpoint is called `/_matrix/client/unstable/io.element.msc4308/thread_subscriptions` instead of `/_matrix/client/v1/thread_subscriptions`


## Dependencies

- [MSC4186 Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/blob/erikj/sss/proposals/4186-simplified-sliding-sync.md)
- [MSC4306 Threads Subscriptions](https://github.com/matrix-org/matrix-spec-proposals/blob/rei/msc_thread_subscriptions/proposals/4306-thread-subscriptions.md)
