# MSC3871: Gappy timeline

`/messages` returns a linearized version of the event DAG. From any given
homeservers perspective of the room, the DAG can have gaps where they're missing
events. This could be because the homeserver hasn't fetched them yet or because
it failed to fetch the events because those homeservers are unreachable and no
one else knows about the event.

Currently, there is an unwritten rule between the server and client that the
server will always return all contiguous events in that part of the timeline.
But the server has to break this rule sometimes when it doesn't have the event
and is unable to get the event from anyone else. This MSC aims to change the
dynamic so the server can give the client feedback and an indication of where
the gaps are.

This way, clients know where they are missing events and can even retry fetching
by perhaps adding some UI to the timeline like "We failed to get some messages
in this gap, try again."

This can also make servers faster to respond to `/messages`. For example,
currently, Synapse always tries to backfill and fill in the gap (even when it
has enough messages locally to respond). In big rooms like `#matrix:matrix.org`
(Matrix HQ), almost every place you ask for has gaps in it (thousands of
backwards extremities) and lots of those events are unreachable so we try the
same thing over and over hoping the response will be different this time but
instead, we just make the `/messages` response time slow. With this MSC, we can
instead be more intelligent about backfilling in the background and just tell
the client about the gap that they can retry fetching a little later.


## Proposal

Add a `gaps` field to the response of [`GET
/_matrix/client/v3/rooms/{roomId}/messages`](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3roomsroomidmessages).
This field is an array of `GapEntry` indicating where missing events in the
timeline are as defined below.


### 200 response

Thid describes the new `gaps` response field being added to the `200 response`
of `/messages`:

Name | Type | Description | required
--- | --- | --- | ---
`gaps` | `[GapEntry]` | A list of gaps indicating where events are missing in the `chunk` | no


#### `GapEntry`

key | type | value | description | required
--- | --- | --- | --- | ---
`next_to_event_id` | string | Event ID | The event ID that the homeserver is missing where the gap begins | yes
`pagination_token` | string | Pagination token | A pagination token that represents the spot in the DAG after the missing `gap_start_event_id`. Useful when retrying to fetch the missing part of the timeline again via `/messages?dir=b&from=<pagination_token>` | yes

Pagination tokens are positions between events. This already an established
concept but to illustrate this better, see the following diagram:
```
                                                     pagination_token
                                                     |
<oldest-in-time> [0]<--[1] <gap> [gap_start_event_id]▼<--[4]<--[5]<--[6] <newest-in-time>
```


### `/messages` response examples

`/messages?dir=f` response example with a gap (`chunk` has events in
chronoligcal order):

```json5
{
  "chunk": [
    {
      "event_id": "$foo",
      "type": "m.room.message",
      "content": {
        "body": "foo",
      }
    },
    // <the `GapEntry` indicates a gap here>
    {
      "event_id": "$baz",
      "type": "m.room.message",
      "content": {
        "body": "baz",
      }
    },
  ]
  "gaps": [
        {
          "next_to_event_id": "$foo",
          "pagination_token": "t47402-4357353_219380_26003_2265",
        }
  ]
}
```


`/messages?dir=b` response example with a gap (`chunk` has events in
reverse-chronoligcal order):

```json5
{
  "chunk": [
    {
      "event_id": "$baz",
      "type": "m.room.message",
      "content": {
        "body": "baz",
      }
    },
    // <the `GapEntry` indicates a gap here>
    {
      "event_id": "$foo",
      "type": "m.room.message",
      "content": {
        "body": "foo",
      }
    }
  ]
  "gaps": [
        {
          "next_to_event_id": "$baz",
          "pagination_token": "t47403-4357353_219380_26003_2265",
        }
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


### Synthetic `m.timeline.gap` event alternative

Another alternative is using synthetic events (thing that looks like an event
without an `event_id`) which the server inserts alongside other events in the
`chunk` to indicate where the gap is. But this has detractors since it's harder
to implement in strongly typed SDK's and easy for a client to naively display
every "event" in the `chunk`.

`/messages` response example with a gap:

```json
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
        "gap_start_event_id": "$12345",
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


## Security considerations

Only your own homeserver controls whether a gap is added to the `/messages`
response so there shouldn't be any weird edge case where someone else can
control whether you to fetch something.


## Unstable prefix

Servers will indicate support for this MSC via a `true` value for feature
flag `org.matrix.msc3871` in `unstable_features` in the response to `GET
/_matrix/client/versions`.

While this feature is in development, the `gaps` field can be used as
`org.matrix.msc3871.gaps`


