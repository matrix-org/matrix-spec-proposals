# MSC0000: Gappy timeline

`/messages` returns a linearized version of the event DAG. From any given
homeservers perspective of the room, the DAG can have gaps where they're missing
events. This could be because the homeserver hasn't fetched them yet or because
it failed to fetch the events because those homeservers are unreachable and no
one else knows about the event.

Currently, there is an unwritten expectation(TODO: better word) between the
server and client that the server will always return all contiguous events in
that part of the timeline. But the server has to break this promise(TODO: match
word above) sometimes when it doesn't have the event and is unable to get the
event from anyone else and the client is unaware. This MSC aims to change the
dynamic so the server can give the client feedback and an indication of where
the gaps are.

This way clients know where they are missing events and can even retry fetching
by perhaps adding some UI to the timeline like "We failed to get some messages
in this gap, try again."

This can also make servers faster to respond to `/messages`. For example,
currently, Synapse always tries to backfill and fill in the gap (even when it
has enough messages locally to respond). In big rooms like `#matrix:matrix.org`
(Matrix HQ), almost every place you ask for has gaps in it (thousands of
backwards extremities) and lots are unreachable so we try the same thing over
and over hoping the response will be different this time but instead, we just
make the `/messages` response time slow. With this MSC, we can instead be more
intelligent about backfilling in the background and just tell the client about
the gap that they can retry fetching a little later.


## Proposal

Add a `m.timeline.gap` indicator, that can be used in the `chunk` list of events
from a `GET /_matrix/client/v3/rooms/{roomId}/messages` response. There can be
multiple gaps per response.


### `m.timeline.gap`

key | type | value | description | required
--- | --- | --- | --- | ---
`gap_start_event_id` | string | Event ID | The event ID that the homeserver is missing where the gap begins | yes
`pagination_token` | string | Pagination token | A pagination token that represents the spot in the DAG after the missing `gap_start_event_id`. Useful when retrying to fetch the missing part of the timeline again via `/messages?dir=b&from=<pagination_token>` | yes

Pagination tokens are positions between events. This already an established
concept but to illustrate this better, see the following diagram:
```
                                                     pagination_token
                                                     |
<oldest-in-time> [0]<--[1] <gap> [gap_start_event_id]▼<--[4]<--[5]<--[6] <newest-in-time>
```

`m.timeline.gap` has a similar shape to a normal event so it's still easy to
iterate over the `/messages` response and process but has no `event_id` itself
so it should not be mistaken as a real event in the room.

A full example of the `m.timeline.gap` indicator:

```json5
{
  "type": "m.timeline.gap",
  "content": {
    "gap_start_event_id": "$12345",
    "pagination_token": "t47409-4357353_219380_26003_2265",
  }
},
```

`/messages` response example with a gap:

```json5
{
  "chunk": [
    {
      "type": "m.room.message",
      "content": {
        "body": "foo",
      }
    },
    {
      "type": "m.timeline.gap",
      "content": {
        "gap_start_event": "$12345",
        "pagination_token": "t47409-4357353_219380_26003_2265",
      }
    },
    {
      "type": "m.room.message",
      "content": {
        "body": "baz",
      }
    },
  ]
}
```


## Potential issues

Lots of gaps/extremities are generated when a spam attack occurs and federation
falls behind. If clients start showing gaps with retry links, we might just be
exposing the spam more.


## Alternatives

As an alternative, we can continue to do nothing as we do today and not worry
about the occasional missing events. People seem not to notice any missing
messages anyway but they do probably see our slow `/messages` pagination.



## Security considerations

Only your own homeserver controls whether a `m.timeline.gap` indicator is added to the
message response and it isn't an event of the room so there shouldn't be any weird
edge case where the gap is trying to get you to fetch spam or something.


## Unstable prefix

The `m.timeline.gap` indicator can be used in the `org.matrix.mscXXXX` room version.


