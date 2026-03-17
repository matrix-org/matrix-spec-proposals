# MSC3874 Loading Messages excluding Threads

## Motivation

In Element's beta implementation of threads, it's become a noticeable issue where a room may have activity in a 
long-running thread while the main timeline is inactive. If a user starts their client and tries to paginate through the 
main timeline, loading will feel sluggish, as lots of events have to be loaded that won’t be displayed.

This proposal would allow reducing the number of requests and amount of data transmitted. Especially for mobile usage
this would allow clients significant usability improvements with threads.  

## Proposal

### Allow filtering the `/messages` API by event relation type

This proposal recommends extending the existing [Event filters] are extended with new filters, named `not_rel_types` and
`rel_types`.  If the `rel_types` filter is specified, messages which match any of the given relation types will be
returned. If the `not_rel_types` filter is specified, only messages which match none of the given relation types will be
returned, this includes events without a relation.

If a relation type is present in both of these fields, `not_rel_types` takes precedence and messages with this type will
not be returned.

```
GET /_matrix/client/v3/rooms/!room_id:domain/messages?filter=...
```

The filter string includes the new fields, above. In this example, the URL encoded JSON is presented unencoded and
formatted for legibility:

```jsonc
{
  "types": ["m.room.message"],
  "not_rel_types": ["m.thread"],
  "rel_types": ["m.edit"]
}
```

The newly added filtering parameters return events based on information in the `m.relates_to` field. Consider the following events in a room:

* `A`: a `m.room.message` event sent by `alice`
* `B`: a `m.room.message` event sent by `bob`
* `C`: a `m.room.message` event sent by `charlie` which relates to `A` with type `m.thread`

Using a filter of `"not_rel_types": ["m.thread"]` would return only events `A` and `B` as they do not have a relation of
`m.thread` in them.

## Potential issues

This proposal moves the loading and processing of these hidden events onto the server. Depending on the server’s
architecture, this may have a non-negligible performance impact. 

## Limitations

While the client can effectively filter out noisy threads, it's not as easy to filter out events adjacent to threads
such as reactions. A more performant implementation is best left for a future MSC.

## Unstable prefix and versioning

Relation filters might have sporadic support across servers, to simplify feature detections for clients, a homeserver
must advertise unstable support for these filters as part of the `/versions` API:

```jsonc
{
  "unstable_features": {
    "org.matrix.msc3874": true,
    // ...
  }
}
```

Unstable implementations should prefix the filter attributes with `org.matrix.msc3874`, e.g.,

```http request
GET /_matrix/client/v3/rooms/!room_id:domain/messages?filter=...
```
In this example, the URL encoded JSON is presented unencoded and formatted for legibility:
```jsonc
{
  "types": ["m.room.message"],
  "org.matrix.msc3874.not_rel_types": ["m.thread"]
}
```

## Dependencies

- [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) ✓
- [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) ✓
- [MSC3567](https://github.com/matrix-org/matrix-doc/pull/3567) ✓
- [MSC3676](https://github.com/matrix-org/matrix-doc/pull/3676) ✓
- [MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440) ✓

<!-- inline links -->
[Event filters]: https://spec.matrix.org/v1.2/client-server-api/#filtering
