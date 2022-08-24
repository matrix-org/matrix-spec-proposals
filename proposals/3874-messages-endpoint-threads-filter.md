# MSC3874 Loading Messages excluding Threads

## Motivation

In our beta deployment of threads, it's become a noticeable issue where a room may have activity in a long-running
thread while the main timeline is inactive. If a user starts their client and tries to paginate through the main
timeline, loading will feel sluggish, as lots of events have to be loaded that won’t be displayed.

## Proposal

### Allow filtering the /messages API to not include threaded messages

This proposal recommends extending the existing [Event filters] are extended with a new filter, named
`not_related_by_rel_types`, which acts exactly like the opposite of the existing `related_by_rel_types` filter.

This means, if this filter is specified, only message which match none of the given relation types will be returned.

```
GET /_matrix/client/v3/rooms/!room_id:domain/messages?filter=...
```

The filter string includes the new fields, above. In this example, the URL encoded JSON is presented unencoded and
formatted for legibility:

```jsonc
{
  "types": ["m.room.message"],
  "not_related_by_rel_types": ["m.thread"]
}
```

Note that the newly added filtering parameters return events based on information in related events. Consider the
following events in a room:

* `A`: a `m.room.message` event sent by `alice`
* `B`: a `m.room.message` event sent by `bob`
* `C`: a `m.room.message` event sent by `charlie` which relates to `A` with type `m.thread`

Using a filter of `"not_related_by_rel_types": ["m.thread"]` would return only event `B` as it has no event which
relates to it via `m.thread`.

### Server capabilities

Threads might have sporadic support across servers, to simplify feature detections for clients, a homeserver must
advertise unstable support for threads as part of the `/versions` API:

```jsonc
{
  "unstable_features": {
    "org.matrix.msc3874": true,
    // ...
  }
}
```

## Potential issues

This proposal moves the loading and processing of these hidden events onto the server. Depending on the server’s
architecture, this may have a non-negligible performance impact. 

## Alternatives

- A suitable workaround, depending on the ratio of thread-messages compared to main timeline messages in a room, may be 
  an increase of the page size

## Dependencies

- [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674)
- [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)
- [MSC3567](https://github.com/matrix-org/matrix-doc/pull/3567)
- [MSC3676](https://github.com/matrix-org/matrix-doc/pull/3676)
- [MSC3440](https://github.com/matrix-org/matrix-doc/pull/344ß)

<!-- inline links -->
[Event filters]: https://spec.matrix.org/v1.2/client-server-api/#filtering
