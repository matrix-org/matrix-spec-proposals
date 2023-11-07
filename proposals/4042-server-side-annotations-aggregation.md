# MSC4042: Server side annotations aggregation
Currently, the specification for [`m.annotation aggregation`](https://spec.matrix.org/v1.8/client-server-api/#server-side-aggregation-of-mannotation-relationships) says that such relations should not be aggregated
on the server side.

This requires servers to deliver clients all annotations they receive. In most cases clients need just a number of annotations of every type. Therefore, delivering aggregated annotations instead of single events could dramatically reduce server-client traffic in
rooms with many reactions.

## Background

Aggregation is a process when client and/or server "summarises" together many events of the same type. 

In early specification versions there was only client-side aggregation and client was solely responsible for receiving and
summarizing all events to make a compact "view" of them.

Later server side aggregation was introduced with idea to:
- decrease client-server traffic for cases when clients do not need
all events of the same type, but can know only their count
- deliver summary of associated children events together with their
parent event given that they can be significantly separated in timeline

Given 1000 users reacted with "👍" annotation to event A,
it is normally sufficient for clients to know that there were 1000
reactions of that type "👍" to event A.

If clients need to get the exact list of users who reacted and additional information about these 1000 reactions, clients can use
existing [`relations (relationships) API`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api)

Servers tried to provide clients with server side generated annotation aggregates before, but these attempts were not successful mainly because both sides (server and client) tried to
aggregate and the same time. That used to lead to the situation when
given the potentially outdated aggregate, clients could not understand which events had already been included into the server provided aggregate and which - not.

## Proposal

Clients will not be responsible for aggregation of relations of "m.annotation" relation type anymore. Such relations will always be aggregated by the server.

Client API will always deliver annotations aggregates, including both
local and known federation events. Homeserver will be responsible for counting annotations correctly.

Whenever requested, server will always provide up-to-date (or nearly up-to-date) aggregates of "m.annotation" via [`messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages),
[`relations`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api), [`get event by id`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomideventeventid) and similar client api endpoints.

For server-server API, homeserver should provide aggregates, including only local events (events created and signed by self).

Servers are allowed to limit maximum number of different "m.annotation" keys they aggregate to a single event by a reasonable value (that corresponds to a limited number of different reaction kinds, e.g. "👍", "👎"). This is needed to avoid the situation when malicious users may attack server creating jumbo-events (events with arbitrary high count of different reaction kinds). Servers may configure this threshold on their discretion, but
this number should not be lower than 16. When annotation key limit
is reached, no new keys should be added to the aggregate, but older
keys would continue to be aggregated (change their count). Annotations beyond that threshold should still be available via [`relations`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api) endpoints.

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
          "current_user_participated": true,
        },
        {
          "key": "👎",
          "origin_server_ts": 1562763768320,
          "count": 1,
          "current_user_participated": false,
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
  "type": "m.reaction",
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation",
      "event_id": "$parent_event_id",
      "key": "👍"
      "current_user_participated": true,
      "origin_server_ts": 1562763768320,
    }
  },
  "unsigned": {
    "annotation_count": 1234,
  }
}
```

## Aggregate updates

All client api endpoints but [`/sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync) should deliver events enriched with updated aggregates whenever requested (as part of their regular response)

[`/sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync) should behave the following way:
- when initial sync (sync without position) is queried, events should contain up-to-date aggregates
- when sync with a token is called and there are no aggregate updates "prior" to the token, new events (after the token) with up-to-date aggregates should be delivered
- given the current time Tn, when sync with a token T is called and there are aggregate updates of event E with stream position T-1 happened between T and Tn, sync should a. re-deliver event E with updated aggregates OR b. deliver EDU of the particular annotation key updated with the up-to-date count
- given the same as above, but with limited sync response, aggregate updates should be sent to client with higher priorities than the rest of the sync response (normal timeline events)
- whenever receiving an event with full "m.annotation" aggregate, clients should overwrite their annotation aggregate they have at the time of receiving. whenever receiving a partial (EDU) aggregate update for a certain annotation key, clients should overwrite (replace) aggregate state for that particular annotation key.
- if there are no other sync updates than aggregate updates at the time of sync request, aggregate updates should not trigger immediate sync response
- given the client is waiting for updates on long polling, aggregate updates should not interrupt long polling. aggregate updates should only be included into sync response, whenever long polling timeout is reached

Servers should filter out events with relation of type "m.annotation" from the main and thread timelines by default. These events should only be delivered in their full form whenever requested explicitly via client API ([`relations`](https://spec.matrix.org/v1.8/client-server-api/#relationships-api), [`get event by id`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomideventeventid), [`context`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)) or via server-server API (federation API)


## Benefits of the proposal

- Room timeline would be cleared from many barely meaningful events in hot rooms
- Traffic would potentially be saved on mobile devices
- Client devices would not need to have such a big local storage (event ids + some metadata for every annotation)
- When closing "gaps" for limited [`/sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync) response and paginating over [`/messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages), clients would not need to load many annotations page-by-page which only end up showing one number somewhere (e.g. iterating many pages of content just to show "👍: 1000")
- Pagination "forward" using [`/messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages) would provide correct annotation count together with every event (no need to go to the end of the timeline to aggregate everything to show correct annotation count for a certain event). This is a solution of the problem that given page cannot potentially contain all reactions to a given event, which happened in the "future" (would belong to the "next" pages otherwise).


## Potential issues

1. Older client SDK used a custom not described in the specification aggregate format introduced in Synapse implementation with "chunked" annotation aggregates. This aggregate format is incompatible with the proposed format.
2. Existing client behavior is client-side aggregation of "m.annotation" relations.
In order not to silently break clients with the new server side aggregation, new aggregation behaviour should only be introduced with a new room version. Older (existing) rooms should be left intact.

## Alternatives

1. Not to aggregate annotations on the server side (as of now)
This limits room scalability for large rooms, where people potentially react more frequently than produce content. There are also use case scenarios like read-only rooms with many users, where users can read, react on events created by room admins (e.g.)
2. Use the former "chunked" format, which was previously used by synapse and later obsoleted. This format provides extra "prev" and "next" tokens, "chunk" of annotations and largely duplicates new "relations" endpoints which had not existed when the format was introduced. with the current specification version this extra functionality seems redundant and would just overcomplicate server side aggregation implementation. Whenever clients need, they can always iterate over annotations explicitly requesting /relations endpoints to get non-aggregates view of relations they are interested in.

### Client opt-in

Given the new room version introduction, no additional feature switches seem to be needed.

## Security considerations

None foreseen.

## Unstable prefix

No new identifiers are proposed; it is proposed that servers implementing this
proposal simply do so on the existing endpoints.

## Dependencies

None.
