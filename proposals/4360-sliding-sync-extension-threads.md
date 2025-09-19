MSC4360: Threads extension to Sliding Sync
===

## Background and Summary

Threads were introduced in [version 1.4 of the Matrix Specification](https://spec.matrix.org/v1.13/changelog/v1.4/) as a way to isolate conversations in a room, making it easier for users to track specific conversations that they care about (and ignore those that they do not).

Sliding Sync is proposed in [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/blob/erikj/sss/proposals/4186-simplified-sliding-sync.md) as a paginated replacement to `/_matrix/client/v3/sync` with smaller response bodies and lower latency.

It is currently a hassle, or nearly impossible, to be able to determine which threads in a user's joined rooms contain
updates. This is especially true when a client returns after having been offline for a period of time. The full set of
events in the timeline has to be paginated through to attempt discovery of any thread events that may have been missed.
This is both cumbersome for the client and slow.

This MSC proposes an 'extension' to Sliding Sync that allows clients to opt-in to receiving real-time updates to threads
in the user's joined rooms. The new `extension` provides a mechanism for clients to quickly and easily "catch up" to any
missed thread updates.

To handle the case in which there have been many thread updates and there are too many to return in
Sliding Sync, a new companion endpoint is proposed to allow backpaginating thread updates across all
of the user's joined rooms on the client's terms.


## Proposal

The `threads` Sliding Sync extension adds additional output to the `/sync` response as well as a new `/thread_updates` companion endpoint
that can be used to paginate thread updates across all of a user's joined rooms. A client's homeserver will track which threads
have had updates since the last time `/sync` was called and present a list of threads containing updates to
the client the next time `/sync` is called. 
The presented list of threads containing updates can cover a larger portion of the timeline than
just the normal sync response would be able to handle, thus allowing clients to quickly gather information on which
threads have updates without having to paginate through the entire timeline of events. 


### Sliding Sync extension

The new Sliding Sync `threads` extension is an optional addition that provides a list of updated threads to a client.
If the client hasn't missed any thread updates, then this whole section of the response is omitted.

When generating the content of the `threads` extension response, if a particular thread contains more than one
update for the client, a `prev_batch` token is provided for that thread. This `prev_batch` token can be used
with the `/relations` endpoint as the `from` parameter, with `dir`=`b`, to obtain other missed updates in that thread.

If there are more threads containing updates than can be included in the response, a `prev_batch` token is provided
with the list of threads. This `prev_batch` token can be used with the new `/thread_updates` companion endpoint as the
`from` parameter, with `dir`=`b`, to obtain other missed thread updates across all of the user's joined rooms.

There are a number of cases to consider when generating the `threads` extension response to a `/sync`:


##### `include_roots` is set to `false`

When `include_roots` is `false` the `thread_root` fields are always omitted from the thread updates.
If a client receives the event/s in the normal response section of `/sync` that would result
in a thread being considered updated, then that thread is omitted from list of updated threads in the extension response.
> ie. When `include_roots` is `false`, only threads with updates that haven't otherwise been presented to
the client via the normal `/sync` response are included in the extension response.

Under normal client operation where a client is online and continually syncing, this has the desirable
effect of making the `threads` extension zero overhead for the client. This assumes that the client is
receiving small, untruncated, batches of new events down `/sync` such that any event/s which would result
in a thread being considered updated are already being passed down to the client and can be omitted from the
`threads` extension. It is only in the case of events being omitted from the normal `/sync` response or a
client falling behind that updates would be included in the `threads` extension.


##### `include_roots` is set to `true`

When `include_roots` is `true` the `thread_root` fields are always included in the thread updates, and thread
updates that would have been otherwise omitted are included in the extension response.
This is true even in the case where the thread update event/s are included in the normal response section
of `/sync`. This may result in some amount of duplicate data in the `/sync` response since the `thread_root`
event contains a copy of the `latest_event` of the thread in it's `unsigned` fields.

Setting `include_roots` to `true` can be useful to ensure thread root changes, such as edits to the thread root, are captured
and passed down in a useful way to the client. The thread root events also include a copy of the latest event in that
thread to make it extremely easy for a client to present a view of threads, whether there are updates, and a preview of
the latest content in each thread.


#### Extension Format

The Sliding Sync request format is extended to include the `threads` extension as follows:

```jsonc
{
  // ...

  "extensions": {
    // ...
    
    // Used to opt-in to receiving changes to threads in joined rooms.
    "threads": {
      // Whether to enable this extension.
      "enabled": true,

      // Whether to include thread root events in the extension response.
      "include_roots": true | false,

      // Optional. Maximum number of thread updates to receive
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

    // Returns a limited window of changes to updated threads.
    // Only the latest changes are returned in this window.
    // If the client hasn't missed anything, then this whole section of the response is omitted.
    "threads": {
      "updates": {
        "!roomid:example.org": {
          "$threadrootid:example.org": {
            // Only included if the request contains `include_roots: true`.
            // A `BundledThreadEvent` (as outlined in https://spec.matrix.org/v1.15/client-server-api/#server-side-aggregation-of-mthread-relationships)
            // is a thread root event which contains the `m.thread` aggregation included under the
            // `m.relations` property in the `unsigned` field of the event.
            "thread_root": BundledThreadEvent,

            // A token that can be used to backpaginate other thread updates,
            // in this thread, that occurred since the last sync but that were not
            // included in this response.
            //
            // The token is to be used with the `/relations` endpoint
            // as `from`, with `dir`=`b`.
            //
            // Optional. Only present in the response if the client missed some events, i.e. there
            // was at least one other event in the thread, in addition to the latest event.
            // In other words, the `prev_batch` points to the prior-to-latest event.
            "prev_batch": "OPAQUE_TOKEN",
          },

          // ...
        }
      },

      // A token that can be used to backpaginate other thread updates
      // that occurred in any thread, in any room, since the last sync but that were not
      // included in this response.
      //
      // The token is to be used with the new `/thread_updates` endpoint
      // as `from`, with `dir`=`b`.
      // The `pos` parameter in the **request** would be used for the `to`
      // parameter.
      //
      // Optional. Only present when some thread updates have been
      // missed out from the response because there are too many of them.
      "prev_batch": "OPAQUE_TOKEN"
    }
  }
}
```

### Companion endpoint for backpaginating thread updates across all rooms

A new `/thread_updates` endpoint is added to allow a client to obtain missing thread updates for a client.
The new endpoint operates as a bulk fetch endpoint, operating across all of a user's joined rooms, allowing
a client to obtain only relevant information with minimal amounts of network requests.
There is an existing `/threads`  endpoint, but it returns all thread roots for a room, not just threads
which contain updates relevant for a client. The existing endpoint also operates on a per-room basis which
means a client would need to perform at least one network request per-room that the user is joined to.

```
GET /_matrix/client/v1/thread_updates
```

URL parameters:

- `dir` (string, required): always `b` (backward), to mirror other pagination
  endpoints. The forward direction is not yet specified to be implemented.

- `from` (string, optional): a token used to continue backpaginating \
  The token is either acquired from a previous `/thread_updates` response,
  or the `prev_batch` in a Sliding Sync response. \
  The token is opaque and has no client-discernible meaning. \
  If this token is not provided, then backpagination starts from the 'end'.

- `to` (string, optional): a token used to limit the backpagination \
  The token can be acquired from a Sliding Sync response.

- `limit` (int, optional; default `100`): a maximum number of thread updates to fetch
  in one response. \
  Must be greater than zero. Servers may impose a smaller limit than requested.
  

Response body:

```jsonc
{
  "chunk": {
    "!roomid:example.org": {
      "$threadrootid:example.org": {
        // A `BundledThreadEvent` (as outlined in https://spec.matrix.org/v1.15/client-server-api/#server-side-aggregation-of-mthread-relationships)
        // is a thread root event which contains the `m.thread` aggregation included under the
        // `m.relations` property in the `unsigned` field of the event.
        "thread_root": BundledThreadEvent,

        // A token that can be used to backpaginate other thread updates,
        // in this thread, that occurred since the last sync but that were not
        // included in this response.
        //
        // The token is to be used with the `/relations` endpoint
        // as `from`, with `dir`=`b`.
        //
        // Optional. Only present in the response if the client missed some events, i.e. there
        // was at least one other event in the thread, in addition to the latest event.
        // In other words, the `prev_batch` points to the prior-to-latest event.
        "prev_batch": "OPAQUE_TOKEN",
      },

      // ...
    }
  },

  // A token to supply to `from` to keep paginating the responses. Not present when there are no further results.
  "next_batch": "OPAQUE_TOKEN"
}
```

No matter how many events were missed in a thread, only one update must be sent to the client per-thread.
If the client is interested in exploring the other missed thread updates further, the `/relations` endpoint
should be used to paginate the events.

The pagination structure of this endpoint matches that of the `/threads` endpoint with the addition of a `to`
parameter to be able to further limit the the scope of the response.


## Expected client behavior

The following outlines how a client would be expected to utilize this new Sliding Sync extension.

When restarting a device, `/sync` would be called with the threads extension enabled and the `include_roots` parameter set to true.
The homeserver would respond to the `/sync` request and give a list of all the threads that have been updated since the last time the client performed a `/sync`.
The homeserver responds with a list of N updated threads and a `prev_batch` token if there were any thread updates
omitted from the list. If there were thread updates omitted, the client keeps on paginating `/thread_updates` with the
`from={prev_batch}&to={pos}` (similar to the usage in [MSC4308](https://github.com/matrix-org/matrix-spec-proposals/pull/4308) until it
exhausts the list of thread updates since the previous time, ie. when pagination has reached `pos`).
The client then sets `include_roots` to `false` to limit the amount of duplicate data being sent down `/sync`.
Further updates to threads will come down the normal `/sync` response, and not be included in the `threads` extension
unless there are too many events in the normal `/sync` response, in which case, any thread update events not included
in the normal `/sync` response will be included in the `threads` extension

If a client is actively in some sort of thread activity monitoring view, a client should set `include_roots` to true to capture the case
of the thread roots having been edited and the client not receiving the edit event (because of timeline gaps).
The edit information (and other aggregations) would be available from the bundled aggregations section in the thread root event provided
in the `threads` extension response.


## Potential issues


## Alternatives


## Limitations


## Security considerations

- No particular security issues anticipated.


## Unstable prefix

Whilst this proposal is unstable, a few unstable prefixes must be observed by experimental implementations:

- the Sliding Sync extension is called `io.element.msc4360.threads` instead of `threads`
- the companion endpoint is called `/_matrix/client/unstable/io.element.msc4360/thread_updates` instead of `/_matrix/client/v1/thread_updates`


## Dependencies

- [MSC4186 Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/blob/erikj/sss/proposals/4186-simplified-sliding-sync.md)

