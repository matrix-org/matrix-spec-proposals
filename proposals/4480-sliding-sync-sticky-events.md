# MSC4480: Sliding Sync Extension: Sticky Events

[MSC4354] introduces Sticky Events using the existing [`/sync`] API. The present MSC adds support
for Sticky Events in Simplified Sliding Sync as per [MSC4186]. This proposal was originally part of
[MSC4354] itself and was split out to break the dependency on [MSC4186].

## Proposal

Over Simplified Sliding Sync, Sticky Events have their own extension `sticky_events`, which has the
following request extension shape:

``` js
{
  "enabled": true,
  "limit": 100, // optional (default 100, min 1): max number of events to return, server can override to a lower number
  "since": "some_token" // optional: can be omitted on initial sync / when extension is only just enabled
}
```

and, when enabled, the following response extension shape:

``` js
{
  "next_batch": "some_token", // REQUIRED when there are changes
  "rooms": {
      "!726s6s6q:example.com": {
          "events": [{
              "sender": "@bob:example.com",
              "type": "m.foo",
              "sticky": {
                "duration_ms": 300000
              },
              "origin_server_ts": 1757920344000,
              "content": { ... }
          }]
      }
  }
}
```

As with regular `/sync`, if a sticky event appears in the `timeline_events` section of the sync
response, it MUST NOT be included in the Sticky Events extension response.

Sticky events are expected to be encrypted and so there is no [state filter] equivalent provided for
sticky events e.g to filter sticky events by event type. As with normal events, sticky events sent
by ignored users MUST NOT be delivered to clients.

The server MUST include sticky events across all rooms that would be matched by at least one
subscription list (i.e. all rooms that the client is interested in), even if the room does not
appear in top-N window for that subscription list at this time. Rooms that would not be matched by a
list are not included, as this means the client is not interested in those rooms.

As with regular `/sync`, when a user joins a room, the server MUST include all unexpired sticky
events for that room in their subsequent sync responses. The server MAY spread them across multiple
sync responses or the server MAY ignore the `limit` specified in the request extension for this
case, depending on implementation preference.

### Pagination

Because sticky events and to-device messages are alike in the way that they should be *reliably*
delivered to clients, without any gaps in the pagination, they follow the [MSC3885: Sliding Sync
Extension: To-Device messages] model for pagination in sliding sync.

In short: when there are too many sticky events to return in one response, the server returns a
limited number of the oldest sticky events that have not yet been delivered.

At every response, the server returns a `next_batch` token which the client MUST persist and send as
a `since` token in the next Sliding Sync request (in the extension), if the client wishes to advance
in the sticky events stream.

However, we don’t require `next_batch` to be provided in the response when there are no changes,
because that seems like a mistake, which would lead to unnecessarily high quiescent bandwidth usage
if many extensions follow this pattern. \[There is a comment thread open on MSC3885\].

One concern is that [MSC3885][MSC3885: Sliding Sync Extension: To-Device messages] has not yet been
updated to account for [MSC4186 ‘Simplified’ Sliding Sync][MSC4186], the ‘modern-day’ dialect of
Sliding Sync, so it is unknown whether this pattern will remain in use. Whatever happens, this MSC
should likely follow the same evolution as that one.

Another concern is a potential problem that we are calling ‘flickering’. This is where due to
oldest-first pagination, a client might briefly display stale data before near-immediately updating
it with later data, despite that later data already having been ‘available’ on the server.

With that said, given this is an edge case that requires a substantial number of sticky events to
trigger, we don’t currently consider it worthwhile to add complexity to avoid.

## Potential issues

Nothing beyond what’s included in [MSC4354].

## Alternatives

Nothing beyond what’s included in [MSC4354].

## Security considerations

Nothing beyond what’s included in [MSC4354].

## Unstable prefix

While this proposal is not considered stable, the extension name `sticky_events` should be referred
to as `org.matrix.msc4354.sticky_events`. Note that this is using the original prefix from [MSC4354]
for historic reasons.

## Dependencies

This MSC builds on [MSC4354] and [MSC4186].

  [MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354
  [`/sync`]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3sync
  [MSC4186]: https://github.com/matrix-org/matrix-spec-proposals/pull/4186
  [state filter]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3useruseridfilter_request_roomeventfilter
  [MSC3885: Sliding Sync Extension: To-Device messages]: https://github.com/matrix-org/matrix-spec-proposals/pull/3885
