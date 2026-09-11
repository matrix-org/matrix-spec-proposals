# MSC4074: Server side annotations aggregation
Currently, the specification for [`m.annotation aggregation`](https://spec.matrix.org/v1.8/client-server-api/#server-side-aggregation-of-mannotation-relationships) says that such relations should not be aggregated
on the server side.

This requires servers to deliver clients all annotations they
receive. In most cases clients need just a number of annotations of
every type. Therefore, delivering aggregated annotations instead of
single events could dramatically reduce server-client traffic in
rooms with many reactions.

The change proposal outlined here addresses the mentioned annotation
issue and also designed in a way that can be similarly extended to other
aggregated relations.

## Background

Aggregation is a process when client and/or server "summarises"
together many events of the same type. 

In early specification versions there was only client-side
aggregation and client was solely responsible for receiving and
summarizing all events to make a compact "view" of them.

Later server side aggregation was introduced with idea to:
- decrease client-server traffic for cases when clients do not need
all events of the same type, but can know only their count
- deliver summary of associated children events together with their
parent event given that they can be significantly separated in
timeline

Given 1000 users reacted with "👍" annotation to event A,
it is normally sufficient for clients to know that there were 1000
reactions of that type "👍" to event A.

If clients need to get the exact list of users who reacted and
additional information about these 1000 reactions, clients can use
existing [`relations (relationships) API`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api)

Servers tried to provide clients with server side generated
annotation aggregates before, but these attempts were not successful
mainly because both sides (server and client) tried to
aggregate at the same time. That used to lead to the situation when
given the potentially outdated aggregate, clients could not
understand which events had already been included into the server
provided aggregate and which - not.

## Proposal

Clients will not be responsible for aggregation of non-encrypted relations of
"m.annotation" relation type anymore. Such relations will always be
aggregated by the server. The E2E encrypted events should still be solely
aggregated by the client.

When there is a mix of encrypted and non-encrypted events, client
should merge its encrypted annotations aggregate with the unencrypted
provided by the server. Given the two sets of events (encrypted,
unencrypted) do not overlap, no events will be counted twice.

Client API will always deliver annotations aggregates, including both
local and known federation events. Homeserver will be responsible
for counting annotations correctly.

Whenever requested, server will always provide up-to-date (or nearly
up-to-date) aggregates of "m.annotation" via [`messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages),
[`relations`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api), [`get event by id`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomideventeventid) and
similar client api endpoints.

For server-server API, homeserver should provide parent events with aggregates,
including only local non E2E encrypted relations (events created and signed by
self). This is needed to ensure that every federation server can merge aggregates
correctly not counting same events multiple times (no overlapping sets).

## Aggregate formats

Full aggregate format (with parent ClientEvent/PDU):
```
{
  "event_id": "$my_event",
  ...
  "unsigned": {
    "m.relations": {
      "m.annotation": [
        {
          "key": "👍",
          "origin_server_ts": 1562763768320,
          "count": 3,
          "current_user_annotation_event_id": "$bar", // if current user reacted
        },
        {
          "key": "👎",
          "origin_server_ts": 1562763768320,
          "count": 1,
          "current_user_annotation_event_id": "$foo", // if current user reacted
        }
      ],
      ...
    }
  }
}
```

Partial aggregate format (EDU):
```
{
  "type": "msc4074.m.reaction",
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation",
      "event_id": "$parent_event_id",
      "key": "👍"
      "current_user_annotation_event_id": "$foo", // if current user reacted
      "origin_server_ts": 1562763768320,
    }
  },
  "unsigned": {
    "annotation_count": 1234,
  }
}
```

## Filtering out aggregated annotations

`RoomEventsFilter` format should be extended to include new filter param
`msc4074.not_aggregated_relations` ([]string).
Server should filter out events having relation types to their parents
specified in this array if these events are aggregated by the server.
Filtering should work for the main and thread timelines.
Such filtered events should only be delivered in their full form
whenever requested explicitly via client API ([`relations`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api),
[`get event by id`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomideventeventid) or via server-server API
(federation API)

## Aggregate updates

Given that aggregated events may be filtered out, it becomes necessary to
provide a way for clients to update their aggregate representations (e.g.
reactions count) when an older event receives updates. It is done via the
proposed `updates` mechanism.

All client api endpoints should deliver events
enriched with updated aggregates whenever requested (as part of their
regular responses)

In addition to that, [`/sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync) and [`/messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages)
endpoints receive `msc4072.updates` API extension as described below.

### /sync endpoint extension

[`/sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync) should behave the following
way:
- when initial sync (sync without position) is queried, events should
  contain up-to-date aggregates
- when sync with a token is called and there are no aggregate updates
  "prior" to the token, new events (after the token) with up-to-date
  aggregates should be delivered
- given the current time Tn, when sync with a token T is called and there
  are aggregate updates of event E with stream position T-1 happened
  between T and Tn, sync should a. re-deliver event E with updated
  aggregates OR b. deliver EDU of the particular annotation key updated
  with the up-to-date count
- given the same as above, but with limited sync response, aggregate
  updates should be sent to client with higher priorities than the
  rest of the sync response (normal timeline events)
- whenever receiving an event with full "m.annotation" aggregate, clients
  should overwrite their annotation aggregate they have at the time of
  receiving. whenever receiving a partial (EDU) aggregate update for a
  certain annotation key, clients should overwrite (replace) aggregate
  state for that particular annotation key.
- if there are no other sync updates than aggregate updates at the time
  of sync request, aggregate updates should not trigger immediate sync
  response
- given the client is waiting for updates on long polling, aggregate
  updates should not interrupt long polling. aggregate updates should only
  be included into sync response, whenever long polling timeout is reached

`
{
    "rooms": {
        "join": {
            "timeline": {
                "msc4072.updates": {
                    // client events with updated aggregates (full view)
                    "full": [..],
                    // EDUs with particular aggregates updated, format
                    // depends on the particular aggregate type
                    "partial": [..]
                },
                // ...
                // irrelevant fields excluded
            },
            // ...
            // irrelevant fields excluded
        },
        // ...
        // irrelevant fields excluded
        }
    // ...
    // irrelevant fields excluded
}
`

### /messages endpoint extension

[`/messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages) endpoint should behave the following way then client passes not empty relations filter:

- If the last known to the server update of a parent event happened in the
  topological interval (page) currently requested by the client and this
  relation type is filtered, server should include the updated parent event
  with the up-to-date aggregates representation in `msc4072.updates` response
  field (either full or partial).

In order to simplify server side implementation it is allowed to deliver `at least` the last known to the server update, but possible to deliver it more
frequently (e.g. if periodical cache flushes into the DB happen on server,
'last update' may 'belong' to few different pages and this should be correctly
handled by the client). Server should every time deliver the most up-to-date
value though.

`
{
    "chunk": [
        {}
    ],
    "msc4074.updates": {
        // client events with updated aggregates (full view)
        "full": [..],
        // EDUs with particular aggregates updated, format
        // depends on the particular aggregate type
        "partial": [..]
    },
    "end": "t47409-4357353_219380_26003_2265",
    "start": "t47429-4392820_219380_26003_2265"
}
`

### /context endpoint extension

[`/context`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidcontexteventid) endpoint will
now support aggregated events filtering via the new filtering param

no `updates` mechanism is needed here since this is endpoint is not supposed to
be used to resolve limiter /sync responses and the history gap closure problem

## Benefits of the proposal

- Room timeline would be cleared from many barely meaningful events in
 hot rooms
- Traffic would potentially be saved on mobile (and desktop) devices
- Client devices would not need to have such a big local storage (event
 ids + some metadata for every annotation)
- When closing "gaps" for limited [`/sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync) response and paginating
 over [`/messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages), clients
 would not need to load many annotations page-by-page which only end up
 showing one number somewhere (e.g. iterating many pages of content just
 to show "👍: 1000")
- Pagination "forward" using [`/messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages) would
 provide correct annotation count together with every event (no need to
 go to the end of the timeline to aggregate everything to show correct
 annotation count for a certain event). This is a solution of the problem
 that given page cannot potentially contain all reactions to a given
 event, which happened in the "future" (would belong to the "next" pages
 otherwise).

Although E2E encrypted annotations are still aggregated by the client
in this proposal, massive scale public rooms will unlikely have
strict security requirements and reactions could be left unencrypted
there. Smaller rooms in their turn where stricter security might be
needed can still use E2E encrypted annotations, but performance and
scalability will not be a concern in this case.

An advantage of the proposed approach, among others, is that clients
can decide what security levels they want.

## Potential issues

1. Older client SDK used a custom not described in the specification
 aggregate format introduced in Synapse implementation with "chunked"
 annotation aggregates. This aggregate format is incompatible with the
 proposed format.
2. Existing client behavior is client-side aggregation of "m.annotation"
 relations.

In order not to silently break clients with the new server side
aggregation, new annotation filtering behaviour should be explicitly
requested by clients via the added
`msc4074.not_aggregated_relations` filtering param.
This filtering param can later be reused for the same purpose
to hide other server aggregated events as soon as more relation type
aggregates are supported.

## Alternatives

1. Not to aggregate annotations on the server side (as of now)
This limits room scalability for large rooms, where people potentially
 react more frequently than produce content. There are also use case
 scenarios like read-only rooms with many users, where users can read,
 react on events created by room admins (e.g.)
2. Use the former "chunked" format, which was previously used by synapse
 and later obsoleted. This format provides extra "prev" and "next"
 tokens, "chunk" of annotations and largely duplicates new "relations"
 endpoints which had not existed when the format was introduced. With the
 current specification version this extra functionality seems redundant
 and would just overcomplicate server side aggregation implementation.
 Whenever clients need, they can always iterate over annotations
 explicitly requesting /relations endpoints to get non-aggregates view of
 relations they are interested in.

### Client opt-in

The proposed change is fully backwards compatible. Clients supporting the
change will be able to opt-in and pass 
`filter_server_aggregated_relation_types` param via `RoomEventsFilter`

## Security considerations

Server cannot aggregate E2E encrypted annotations. In order to make
annotation aggregation work in E2E rooms, such annotations should
be sent unencrypted.
Annotations do not normally contain security sensitive data, and this
limitation should not be significant for most of the cases.

In order to provide a workaround for cases when stricter security is
important, encrypted annotations should be aggregated by the client.

To make this process work, server would not filter out encrypted
annotations from the main and thread timelines by default and deliver
them to clients. Clients aggregate only encrypted annotations and
apply their aggregate on top (in addition) of the aggregate server
may already provide to event. Such aggregates would never overlap
as server never aggregates encrypted events and simple deterministic
logic to merge server and client aggregates exists in this case.

## Unstable prefix

No new identifiers are proposed; it is proposed that servers implementing
this
proposal simply do so on the existing endpoints.

## Dependencies

None.
