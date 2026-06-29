# Filter state events by type in /state endpoint

Currently, the `GET /_matrix/client/v3/rooms/{roomId}/state` endpoint returns all state events in a
room. For rooms with many state events, this can be inefficient when a client only needs events of
specific types.

This proposal adds an optional `types` query parameter to the `/state` endpoint, allowing clients to
request only state events matching the specified event types.


## Proposal

Add an optional `types` query parameter to the `GET /_matrix/client/v3/rooms/{roomId}/state` endpoint.

### Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `types` | `[string]` | A JSON-encoded array of event types to include. If this list is absent then all event types are included. A `*` can be used as a wildcard to match any sequence of characters. |

This follows the same semantics as the `types` field in `RoomEventFilter`:

> A list of event types to include. If this list is absent then all event types are included. 
> A `*` can be used as a wildcard to match any sequence of characters.

### Examples

Request all space child events:

```
GET /_matrix/client/v3/rooms/!roomid:example.org/state?types=%5B%22m.space.child%22%5D
```

Request multiple event types:

```
GET /_matrix/client/v3/rooms/!roomid:example.org/state?types=%5B%22m.room.name%22%2C%22m.room.topic%22%2C%22m.room.avatar%22%5D
```
As `m.room.name`, `m.room.topic` and `m.room.avatar` are all states that typically only have one key, they could have
been fetched using the existing `GET /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}` endpoint. Using
the types query parameter makes this task not require separate requests.

Request all events in a namespace using wildcard:

```
GET /_matrix/client/v3/rooms/!roomid:example.org/state?types=%5B%22org.example.*%22%5D
```

### Behavior

- When `types` is not provided, the endpoint behaves exactly as it does now, returning all state events.
- When `types` is an empty array `[]`, no state events are returned.
- Following `RoomEventFilter`, wildcard matching uses `*` to match any sequence of characters.


## Potential issues

JSON-encoded arrays in query parameters are awkward to work with. They require URL encoding, and
some HTTP client libraries don't handle this well out of the box. However, this approach maintains
consistency with `RoomEventFilter` semantics and avoids inventing a new format for the same
filtering concept.


## Alternatives

### Use /sync with a filter

Clients could use `/sync` with a `RoomFilter` that specifies the desired `rooms` and a `StateFilter`
with the desired `types`. However, the `/sync` response structure is significantly more complex than
`/state`, and filtering to a single room requires either listing it explicitly or using a filter ID
created via `POST /filter`.

### Accept a full StateFilter

Instead of just `types`, the endpoint could accept a full `StateFilter` object (with `types`,
`not_types`, `senders`, `not_senders`, etc.). However, for most usecases `StateFilter` provides
a lot more than what is needed to read state.

### Add individual query parameters per type

Instead of a JSON array, we could use repeated query parameters like
`type=m.room.power_levels&type=m.room.name`. This would be simpler to construct but wouldn't
support wildcards as elegantly and deviates from the established `RoomEventFilter` pattern.


## Security considerations

None.

## Unstable prefix

While this MSC is not yet part of the spec, implementations should use `cc.koja.types` as the query
parameter name. Once this MSC is merged, implementations can use `types`.

Clients can detect server support by checking for the presence of the `cc.koja.types` flag in the
`unstable_features` section of the `/versions` response.

## Dependencies

None.
