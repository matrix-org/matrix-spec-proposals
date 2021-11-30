# MSC2675: Serverside aggregations of message relationships

It's common to want to send events in Matrix which relate to existing events -
for instance, reactions, edits and even replies/threads.

Clients typically need to track the related events alongside the original
event they relate to, in order to correctly display them.  For instance,
reaction events need to be aggregated together by summing and be shown next to
the event they react to; edits need to be aggregated together by replacing the
original event and subsequent edits; replies need to be indented after the
message they respond to, etc.

It is possible to treat relations as normal events and aggregate them
clientside, but to do so comprehensively could be very resource intensive, as
the client would need to spider all possible events in a room to find
relationships and maintain a correct view.

Instead, this proposal seeks to solve this problem by defining APIs to let the
server calculate the aggregations on behalf of the client, and so bundle the
related events with the original event where appropriate. It also proposes an
API to let clients paginate through all relations of an event.

This proposal is one in a series of proposals that defines a mechanism for
events to relate to each other.  Together, these proposals replace
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

* [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) defines a
  standard shape for indicating events which relate to other events.
* This proposal defines APIs to let the server calculate the aggregations on
  behalf of the client, and so bundle the related events with the original
  event where appropriate.
* [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676) defines how
  users can edit messages using this mechanism.
* [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) defines how
  users can annotate events, such as reacting to events with emoji, using this
  mechanism.

## Proposal

### Aggregations

Relation events can be aggregated per `rel_type` by the server.
The format of the aggregated value (hereafter called "aggregation")
in the bundle depends on the relation type.

Some `rel_type`s might additionally group the aggregations by the `key` property
in the relation and aggregate to an array,
others might aggregate to a single object or any other value really.

#### Bundled aggregations

Other than during non-gappy incremental syncs, events that have other events
relate to it should bundle the aggregation of those related events
in the `m.relations` property of their unsigned data.  These are called
bundled aggregations, and by sending a summary of the relations,
avoids us having to always send lots of individual relation events
to the client.

Here's an example of what that can look like for some ficticious `rel_type`s:

```json
{
  "event_id": "abc",
  "unsigned": {
    "m.relations": {
      "some_rel_type": { "some_prop": true }, // aggregation for some_rel_type
      "other_rel_type": { "other_prop": false }, // aggregation for other_rel_type
    }
  }
}
```

The following client-server APIs should bundle aggregations
with events they return:

  - `GET /rooms/{roomId}/messages`
  - `GET /rooms/{roomId}/context`
  - `GET /rooms/{roomId}/event/{eventId}`
  - `GET /sync`, only for room sections in the response where `limited` field
    is `true`; this amounts to all rooms in the response if 
    the `since` request parameter was not passed, also known as an initial sync.
  - `GET /relations`, as proposed in this MSC.

Deprecated APIs like `/initialSync` and `/events/{eventId}` are *not* required
to bundle aggregations.

The bundled aggregations are grouped according to their `rel_type`.

For relation types that aggregate to an array, future MSCs could opt to 
paginate within each group using Matrix's defined pagination idiom of
`next_batch` and `chunk` - respectively giving a pagination token if there are
more aggregations, and an array of elements in the list. Only the first page
is bundled, pagination of subsequent pages happens through the `/aggregations`
API that is defined in this MSC. The maximum amount of aggregations bundled
before the list is truncated is determined freely by the server.

For instance, the below example shows an event with five bundled relations:
three thumbsup reaction annotations, one replace, and one reference.

These are just non-normative examples of what the aggregation for these
relation types could look like, but their MSCs might end up with
a different shape, take these with a grain of salt.

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.annotation": {
                "chunk": [
                  {
                      "type": "m.reaction",
                      "key": "👍",
                      "origin_server_ts": 1562763768320,
                      "count": 3
                  }
                ]
            },
            "m.reference": {
                "chunk": [
                    {
                        "event_id": "$some_event_id"
                    }
                ],
                "next_batch": "abc123",
            },
            "m.replace": {
                "event_id": "$edit_event_id",
                "origin_server_ts": 1562763768320,
                "sender": "@bruno1:localhost"
            }
        }
    }
}
```

### Querying aggregations

The `/aggregations` API lets you iterate over aggregations for the relations
of a given event.

To iterate over the aggregations for an event (optionally filtering by
relation type and target event type):

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}[/{relationType}][/{eventType}][?from=token][&to=token][&limit=amount]
```

This is just non-normative example of what the aggregation for this
relation types could look like, but its MSCs might end up with
a different shape, take this with a grain of salt.

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
  "prev_batch": "some_token"
}
```

The endpoint does not have any trailing slashes.

The `from`, `to` and `limit` query parameters are used for pagination, and work
just like described for the `/messages` endpoint.

Trying to iterate over an relation type which does not use an aggregation key
(i.e. `m.replace` and `m.reference`) should fail with 400 and error
`M_INVALID_REL_TYPE`.

### Querying relations

A single event can have lots of associated relations, and we do not want to
overload the client by including them all bundled with the related-to event
like we do for aggregations. Instead, we provide a new `/relations` API in
order to paginate over the relations, which behaves in a similar way to
`/messages`, except using `next_batch` and `prev_batch` names
(in line with `/sync` API).

The `/relations` API returns the discrete relation events
associated with an event that the server is aware of
in standard topological order. Note that events may be missing,
see [limitations](#servers-might-not-be-aware-of-all-relations-of-an-event).  You can optionally
filter by a given type of relation and event type:

```
GET /_matrix/client/r0/rooms/{roomID}/relations/{eventID}[/{relationType}[/{eventType}]][?from=token][&to=token][&limit=amount]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

The endpoint does not have any trailing slashes.

The `from`, `to` and `limit` query parameters are used for pagination, and work
just like described for the `/messages` endpoint.

Note that [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676)
adds the related-to event in `original_event` property of the response.
This way the full history (e.g. also the first, original event) of the event
is obtained without further requests. See that MSC for further details.

### End to end encryption

Since the server has to be able to aggregate relation events, structural
information about relations must be visible to the server, and so the
`m.relates_to` field must be included in the plaintext.

The `/relations` and `/aggregations` endpoint allow filtering by event type,
which for encrypted rooms will be `m.room.encrypted`, rendering this filtering
less useful for encrypted rooms. Aggregations that take the event type into
account of the relation will suffer from the same limitation.

A future MSC may define a method for encrypting certain parts of the
`m.relates_to` field that may contain sensitive information.

### Redactions

Redacted relations should not be taken into consideration in
bundled aggregations or aggregations returned from `/aggregations`,
nor should they be returned from `/relations`.

Requesting `/relations` or `/aggregations` on a redacted event should
still return any existing relation events, and aggregations respectively.
This is in line with other APIs like `/context` and `/messages`.

### Local echo

As clients only receive discrete relation events through `/sync`,
they need to locally aggregate these relation events for their parent event,
on top of any server-side aggregation that might have already happened,
to get a complete picture of the aggregations for a given parent event,
as a client might not be aware of all relations for an event. Local aggregation
should thus also take the `m.relation` data in the `unsigned` of the parent
event into account if it has been sent already. The aggregation algorithm is the
same as the one described here for the server.

For the best possible user experience, clients should also include unsent
relations into the local aggregation. When adding a relation to the send
queue, clients should locally aggregate it into the relations of the parent
event, ideally regardless of the parent event having an `event_id` already or
still being pending. If the client gives up on sending the relation for some
reason, the relation should be de-aggregated from the relations of the parent
event. If the client offers the user a possibility of manually retrying to
send the relation, it should be re-aggregated when the user does so.

De-aggregating a relation refers to rerunning the aggregation for a given
parent event while not considering the de-aggregated event any more.

Upon receiving the remote echo for any relations, a client is likely to remove
the pending event from the send queue. Here, it should also de-aggregate the
pending event from the parent event's relations, and re-aggregate the received
remote event from `/sync` to make sure the local aggregation happens with the
same event data as on the server.

When adding a redaction for a relation to the send queue, the relation
referred to should be de-aggregated from the relations of the target of the
relation.  Similar to a relation, when the sending of the redaction fails or
is cancelled, the relation should be aggregated again.

Clients can locally relate pending events by their `transaction_id`.
When the target event receives its `event_id` (either receives the remote echo,
or receives the `event_id` from the `/send` response,
whichever comes first), the target event id (`m.relates_to`.`event_id`) of
any relations in the send queue will
need to be set the newly received `event_id`.

Particularly, please remember to let users edit unsent messages (as this is a
common case for rapidly fixing a typo in a msg which is still in flight!)

## Edge cases

### How do you handle ignored users?

 * Information about relations sent from ignored users must never be sent to
   the client, either in aggregations or discrete relation events.
   This is to let you block someone from harassing you with emoji reactions
   (or using edits as a side-channel to harass you).

## Limitations

### Servers might not be aware of all relations of an event

The response of `/relations` might be incomplete because the homeserver
potentially doesn't have the full DAG of the room. The federation API doens't
have an equivalent of the `/relations` API, so has no way but to fetch the
full DAG over federation to assure itself that it is aware of all relations.

[MSC2836](https://github.com/matrix-org/matrix-doc/blob/kegan/msc/threading/proposals/2836-threading.md#making-relationships) also makes mention of this issue.

## Future extensions

### Handling limited (gappy) syncs

For the special case of a gappy incremental sync, many relations (particularly
reactions) may have occurred during the gap. It would be inefficient to send
each one individually to the client, but it would also be inefficient to send
all possible bundled aggregations to the client.

The server could tell the client the event IDs of events which
predate the gap which received relations during the gap. This means that the
client could invalidate its copy of those events (if any) and then requery them
(including their bundled relations) from the server if/when needed,
for example using an extension of the `/event` API for batch requests.

The server could do this with a new `stale_events` field of each room object
in the sync response. The `stale_events` field would list all the event IDs
prior to the gap which had updated relations during the gap. The event IDs
would be grouped by relation type,
and paginated as per the normal Matrix pagination model.

This was originally part of this MSC but left out to limit the scope
to what is implemented at the time of writing.