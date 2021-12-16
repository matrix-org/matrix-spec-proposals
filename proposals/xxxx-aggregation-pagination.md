# MSC0000: Aggregation pagination

MSC 2675 introduced aggregating relations on the server. The goal of bundled aggregations is to be more bandwidth efficient. For relations that aggregate to an array with many entries, we might actually end up sending too much data still when bundling.

This MSC proposes a pagination mechanism for aggregations so we don't need to bundle all entries for array aggregations.

Both MSC 2677 and MSC MSC 3267 would benefit from the pagination mechanism, hence proposing it in a separate MSC rather than including it in either of those.

## Proposal

For relation types that aggregate to an array, only a first few entries of the array are bundled. A pagination token is also provided to fetch subsequent aggregation array entries with a new `/aggregations` endpoint. The pagination tries to follow Matrix's defined pagination idiom where possibly; using `next_batch` and `chunk` - respectively giving a pagination token if there are
more aggregations, and an array of elements in the list.

Only the first page
is bundled; pagination of subsequent pages happens through the `/aggregations`
API that is defined in this MSC. The maximum amount of aggregations bundled
before the list is truncated is determined freely by the server.

Note that the client *can* determine the page size when calling
`/aggregations` through the `limit` request parameter, the offset is solely
determined by the `next_batch` token.

For instance, the below example shows an event with five bundled relations:
one replace, one reference and three thumbsup reaction annotations,
with more aggregated reactions available to paginate in
through `/aggregations` as `next_batch` is present.

These are just non-normative examples of what the aggregation for these
relation types could look like, and their MSCs might end up with
a different shape, so take these with a grain of salt.

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.replace": {
                "event_id": "$edit_event_id",
                "origin_server_ts": 1562763768320,
                "sender": "@bruno1:localhost"
            },
            "m.reference": {
                "chunk": [
                    {
                        "event_id": "$some_event_id"
                    }
                ],
            },
            "m.annotation": {
                "chunk": [
                  {
                      "type": "m.reaction",
                      "key": "👍",
                      "origin_server_ts": 1562763768320,
                      "count": 3
                  }
                  "next_batch": "abc123",
                ]
            }
        }
    }
}
```


### Querying aggregations

The `/aggregations` API lets you iterate over aggregations for the relations
of a given event.

To iterate over the aggregations for an event (optionally filtering by
relation type and relation event type):

```
GET /_matrix/client/v1/rooms/{room_id}/aggregations/{event_id}/{rel_type}[/{event_type}][?from=token][&limit=amount]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "key": "👍",
      "count": 5,
    }
  ],
  "next_batch": "some_token",
}
```

Again, this is a non-normative example of the aggregation for an
`m.annotation` relation type.

Note that endpoint does not have any trailing slashes: `GET /_matrix/client/v1/rooms/{roomID}/aggregations/$abc/m.reaction/`
would return aggregations of relations with an *empty* `event_type`, which is nonsensical.

The `from` and `limit` query parameters are used for pagination, and work
just like described for the `/messages` endpoint.

Trying to iterate over a relation type which does not use an aggregation key
(eg. `m.replace` and `m.reference`) should fail with 400 and error
`M_INVALID_REL_TYPE`.

### Redactions

Redacted relations should not be taken into consideration in
aggregations returned from `/aggregations`.

Requesting `/aggregations` on a redacted event should
still return any existing aggregations.
This is in line with other APIs like `/context` and `/messages`.

## Limitations

### Event type based aggregation and filtering won't work well in encrypted rooms

The `/aggregations` endpoint allows filtering by event type,
which for encrypted rooms will be `m.room.encrypted`, rendering this filtering
less useful for encrypted rooms.

## Prefix

While this MSC is not considered stable, the endpoints become:

 - `GET /_matrix/client/unstable/rooms/{roomID}/aggregations/{eventID}/{relationType}[/{eventType}]`

None of the newly introduced identifiers should use a prefix though, as this MSC
tries to document relation support already being used in
the wider matrix ecosystem.