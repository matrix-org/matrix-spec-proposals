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
      // Must be specified and true to enable the extension.
      "enabled": true,
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
      // Threads that have been subscribed, or had their subscription
      // changed.
      //
      // Optional. If omitted, has the same semantics as an empty map.
      "subscribed": {
        "!roomId1:example.org": {
          // New subscription
          "$threadId1": {
            "automatic": true,
            "bump_stamp": 4000
          },
          // New subscription
          // or subscription changed to manual
          "$threadId2": {
            "automatic": false,
            "bump_stamp": 4210
          }
        },
        "$roomId2:example.org": {
          // ...
        }
      },
      // Threads that have been unsubscribed.
      //
      // Optional. If omitted, has the same semantics as an empty map.
      "unsubscribed": {
        "!roomId3:example.org": {
          // Represents a removed subscription
          "$threadId3": {
            "bump_stamp": 4242
          }
        },
        // ...
      },

      // A token that can be used to backpaginate other thread subscription
      // changes that occurred since the last sync, but that were not
      // included in this response.
      //
      // The token is to be used with the `/thread_subscriptions` endpoint
      // as `from`, with `dir`=`b`.
      // The `pos` parameter in the **request** would be used for the `to`
      // parameter.
      //
      // Optional. Only present when some thread subscriptions have been
      // missed out from the response because there are too many of them.
      "prev_batch": "OPAQUE_TOKEN"
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
  or the `prev_batch` in a Sliding Sync response. \
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
  "subscribed": {
    "!roomId1:example.org": {
      // New subscription
      "$threadId1": {
        "automatic": true,
        "bump_stamp": 4000
      },
      // New subscription
      // or subscription changed to manual
      "$threadId2": {
        "automatic": false,
        "bump_stamp": 4210
      }
    },
    "$roomId2:example.org": {
      // ...
    }
  },
  "unsubscribed": {
    "!roomId3:example.org": {
      // Represents a removed subscription
      "$threadId3": {
        "bump_stamp": 4242
      }
    },
    // ...
  },
  // If there are still more thread subscriptions to fetch,
  // a new `from` token the client can use to walk further
  // backwards. (The `to` token, if used, should be reused.)
  "end": "OPAQUE_TOKEN"
}
```

If two changes occur to the same subscription, only the latter change ever needs
to be sent to the client. \
Servers MUST not send intermediate subscription states to clients.

The pagination structure of this endpoint matches that of the `/messages` endpoint, but fixed
to the backward direction (`dir=b`).
For simplicity, the `start` response field is removed as it is entirely redundant.

### Use of `bump_stamp`

The `bump_stamp`s within each thread subscription can be used for determining which
state is latest, for example when a concurrent `/thread_subscriptions` backpagination request
and `/sync` request both return information about the same thread subscription.

The semantics of the `bump_stamp` are that for two updates about the same thread,
the update with the higher `bump_stamp` is later and renders the update with the lower
`bump_stamp` obsolete.

Clients MUST NOT interpret any other semantics of the `bump_stamp`; other than the semantics
above they do not have any special meaning.
Notably, `bump_stamp`s MUST NOT be compared between different threads, because servers MAY
treat `bump_stamp`s as per-thread.

`bump_stamp` MUST be an ECMAScript-compatible (Canonical JSON-compatible) integer.

`bump_stamp`s are independent of the sliding sync session and remain valid for comparison
even if the sliding sync connection is reset, or if the device is changed.
Servers do not need to make `bump_stamp`s consistent across different users.

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
