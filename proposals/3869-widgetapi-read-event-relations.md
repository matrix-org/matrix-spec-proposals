# MSC3869: Read event relations with the Widget API

[MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762) specifies a Widget API that
is able to receive events from the client. It supports reading state events from a room and room
events from a room timeline. It is also possible to provide a filter to only receive selected events.

While the existing APIs are a good fit for receiving live updates and getting state events, it has
some limitations regarding room events. The client only provides events that it already loaded until
a request. But for some use cases, the widget needs to have a reliable way to query _all relevant_
events from a room (ex: have a certain type; belong to a certain application defined grouping).

The polls feature ([MSC3381](https://github.com/matrix-org/matrix-spec-proposals/pull/3381)) uses
serverside aggregation of message relationships
([MSC2675](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2675-aggregations-server.md))
to solve this use case. Related events reference each other by a `rel_type` and the client-server API
provides an endpoint to receive server-aggregated relations.

Having this API available to widgets, it could (1) access existing events to e.g. show an enhanced view
of the polls feature or (2) read own events for a custom use case such as a whiteboard application.

## Proposal

We will add a new interface to the widget API to get all relations of an event with a known event id.
We won't introduce new capabilities but instead rely on the capabilities that were introduced by
[MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762).

The following rules apply:

1. The list of related events only include events that the widget has the respective
   `m.receive.event:<event type>` or `m.receive.state_event:<event type>` capability for. Other
   events are silently dropped.

To trigger the read, widgets will use a new `fromWidget` request with the action `read_relations`
which takes the following shape:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "read_relations",
  "data": {
    "room_id": "!room-id",
    "event_id": "$event-id",
    "rel_type": "m.reference",
    "event_type": "m.room.message",
    "limit": 50,
    "from": "from_token",
    "to": "to_token",
    "direction": "b"
  }
}
```

Under `data`, all keys are a representation of the
`_matrix/client/v1/rooms/{roomID}/relations/{event_id}[/{rel_type}[/{event_type}]]` API that was
introduced by
([MSC2675](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2675-aggregations-server.md)).
This also includes the paging parameters.

The `event_id` parameter is a required parameter that represents the parent event to be read.

The `room_id` parameter specifies the room to look within. When undefined, the client should look in
the user's currently viewed room.

The `rel_type` parameter specifies the relationship type of child events to search for. If not
defined, all types will be returned.

The `event_type` parameter specifies the type of child events to search for. If not defined, all
types will be returned.

The `limit`, `from`, and `to` parameters work like described in
([MSC2675](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2675-aggregations-server.md)).

The `direction` parameter is used to specify the direction to search for relations. It has the same
semantic as defined by ([MSC3715](https://github.com/matrix-org/matrix-spec-proposals/pull/3715)).

This is an example of a minimal request to get an event from the current room:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "read_relations",
  "data": {
    "event_id": "$event-id"
  }
}
```

If the widget doesn't have appropriate permission, or an error occurs anywhere along the send path,
a standardized widget error response is returned.

If the request was successful, the client sends the following response:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "create_room",
  "data": {
    "event_id": "$event-id"
  },
  "response": {
    "chunk": [
      {
        "type": "m.room.message",
        "..."
      },
      { "..." }
    ],
    "next_batch": "next_batch_token",
    "prev_batch": "prev_batch_token"
  }
}
```

The `chunk` field contains an array of events that are related to the parent event and matches the
filters and the capabilities. This list might include less events than the specified `limit` due to
the filter operations.

The `next_batch` field is a cursor that can be used in the `from` or `to` fields to get the next page
of events. If undefined, there are no more events to receive.

The `prev_batch` field is a cursor that can be used in the `from` or `to` fields to get the previous
page of events. If undefined, there are no more events to receive.

## Potential issues

In an e2ee room, all the events must be decrypted in the client prior to applying the filters or
providing them to the widget. This can take a considerable amount of time. The widget should take
care that it selects a reasonable `limit` to not run into timeouts in the widget transport layer.

## Alternatives

We could also add features to let the client "scroll up the room", i.e. trigger the pagination for a
room timeline and stick with the original read interfaces. However, this would potentially load a
lot of unrelated events which slows the read process down. In addition, the client must potentially
decrypt all the messages in the room before being able to filter them accordingly. Using the relations
feature, the decryption problem is still present, but the set of events that must be decrypted and
searched is minimized.

The same limitations would apply if we would consider to provide direct access to the
`GET /_matrix/client/v3/rooms/{roomId}/messages` endpoint.

## Security considerations

The same considerations as in [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762)
apply. The widget will be able to receive the same set of events, but can just use a different
approach to request them.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

- Use `org.matrix.msc3869.` in place of `m.` in all new identifiers of this MSC.
- Use `org.matrix.msc3869.read_relations` in place of `read_relations` for the action type in the
  `fromWidget` requests.
- Only call/support the `action`s if an API version of `org.matrix.msc3869` is advertised.
