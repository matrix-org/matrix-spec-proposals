# MSC3666: Bundled aggregations for server side search

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines a way for
homeservers to include events related to a requested event via "bundled aggregations".
These bundled aggregations help a client render a requested event without needing
to fetch additional information from the server.

As part of MSC2675 the following APIs should include bundled aggregations:

* `GET /rooms/{roomId}/messages`
* `GET /rooms/{roomId}/context/{eventId}`
* `GET /rooms/{roomId}/event/{eventId}`
* `GET /sync`, only for room sections in the response where limited field is true;
  this amounts to all rooms in the response if the since request parameter was
  not passed, also known as an initial sync.
* `GET /rooms/{roomId}/relations/{eventId}`

A noticeable missing API from here is the server side search feature (`POST /search`)
where it is common for a client to not have the full timeline of a room when
receiving results. This would benefit from having the bundled aggregations.


## Proposal

The server side search API ([`POST /search`](https://spec.matrix.org/v1.2/client-server-api/#post_matrixclientv3search))
for the `room_events` category will
include bundled aggregations for any matching events returned to the client.
As in [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675), the `unsigned`
field of the results would include `m.relations` where appropriate. This applies to
any events themselves, as well as contextual events returned; these appear as the
following fields:

* The event itself: `results["search_categories"]["room_events"]["results"]["result"]`
* Each contextual event in:
  * `results["search_categories"]["room_events"]["results"]["context"]["events_before"]`
  * `results["search_categories"]["room_events"]["results"]["context"]["events_after"]`


## Potential issues

The `/search` API is already fairly complicated and can be slow for large rooms.
Returning more data from it could cause performance issues.


## Alternatives

The status quo is that a client can call `/rooms/{roomId}/relations/{eventId}` for
each event in the search results in order to fully render each event. This is
expensive, slow, and bandwidth heavy since clients generally need the aggregated
relations, not each related event.

Older versions of [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)
included an `/rooms/{roomId}/aggregations/{eventId}` API to fetch the bundled
aggregations for an event directly. This would save on bandwidth and simplify
the work that clients need to achieve, but would still result in needless
roundtrips as it would have to be  called per event.


## Security considerations

None.


## Unstable prefix

N/A


## Dependencies

This MSC builds on [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674)
and [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675), which have
been accepted, but are not yet in a released version of the spec at the time of
writing.
