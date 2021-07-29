# MSC2716: Batch send historical messages

For the full problem statement, considerations, see the other `proposals/2716-importing-history-into-existing-rooms.md` document. Happy to merge the two, once we get more feedback on it.

## Alternative batch send proposal


### Expectation

Historical messages that we insert should appear in the timeline just like they would if they were sent back at that time.

Here is what scrollback is expected to look like in Element:

![](https://user-images.githubusercontent.com/558581/119064795-cae7e380-b9a1-11eb-9366-5e1f5e6370a8.png)



### New batch send approach

Add a new endpoint, `POST /_matrix/client/unstable/org.matrix.msc2716/rooms/<roomID>/batch_send?prev_event=<eventID>&chunk_id=<chunkID>`, which can insert a chunk of events historically back in time next to the given `prev_event`. This endpoint can only be used by application services. `chunk_id` comes from `next_chunk_id` in the response of the batch send endpoint and is derived from the "insertion" events added to each chunk. It's not required for the first batch send.
```
# Body
{
    "events": [ ... ],
    "state_events_at_start": [ ... ]
}

# Response
{
  "state_events": [...list of state event ID's we inserted],
  "events": [...list of historical event ID's we inserted],
  "next_chunk_id": "random-unique-string",
}
```

`state_events_at_start` is used to define the historical state events needed to auth the `events` like join events. These events can float outside of the normal DAG. In Synapse, these are called floating `outlier`'s and won't be visible in the chat history which also allows us to insert multiple chunks without having a bunch of `@mxid joined the room` noise between each chunk. The state will not be resolved into the current state of the room.

`events` is chronological chunk/list of events you want to insert. For Synapse, there is a reverse-chronological constraint on chunks so once you insert one chunk of messages, you can only insert older an older chunk after that. tldr; Insert from your most recent chunk of history -> oldest history.

The `state_events`/`events` payload is in **chronological** order (`[0, 1, 2]`) and is processed it in that order so the `prev_events` point to it's older-in-time previous message which is more sane in the DAG. **Depth discussion:** For Synapse, when persisting, we **reverse the list (to make it reverse-chronological)** so we can still get the correct `(topological_ordering, stream_ordering)` so it sorts between A and B as we expect. Why?  `depth` is not re-calculated when historical messages are inserted into the DAG. This means we have to take care to insert in the right order. Events are sorted by `(topological_ordering, stream_ordering)` where `topological_ordering` is just `depth`. Normally, `stream_ordering` is an auto incrementing integer but for `backfilled=true` events, it decrements. Historical messages are inserted all at the same `depth`, and marked as backfilled so the `stream_ordering` decrements and each event is sorted behind the next. (from https://github.com/matrix-org/synapse/pull/9247#discussion_r588479201)

All of the events in the chunk get a content field, `"m.historical": true`, to indicate that they are historical at the point of being added to a room.

With the new process, the DAG will look like:

![](https://user-images.githubusercontent.com/558581/126577416-68f1a5b0-2818-48c1-b046-21e504a0fe83.png)


[Mermaid live editor playground link](https://mermaid-js.github.io/mermaid-live-editor/edit/#eyJjb2RlIjoiZmxvd2NoYXJ0IEJUXG4gICAgc3ViZ3JhcGggbGl2ZVxuICAgICAgICBCIC0tLS0tLS0tLS0tLS0-IEFcbiAgICBlbmRcbiAgICBcbiAgICBzdWJncmFwaCBjaHVuazBcbiAgICAgICAgY2h1bmswLTIoKFwiMlwiKSkgLS0-IGNodW5rMC0xKCgxKSkgLS0-IGNodW5rMC0wKCgwKSlcbiAgICBlbmRcblxuICAgIHN1YmdyYXBoIGNodW5rMVxuICAgICAgICBjaHVuazEtMigoXCIyXCIpKSAtLT4gY2h1bmsxLTEoKDEpKSAtLT4gY2h1bmsxLTAoKDApKVxuICAgIGVuZFxuICAgIFxuICAgIHN1YmdyYXBoIGNodW5rMlxuICAgICAgICBjaHVuazItMigoXCIyXCIpKSAtLT4gY2h1bmsyLTEoKDEpKSAtLT4gY2h1bmsyLTAoKDApKVxuICAgIGVuZFxuXG4gICAgXG4gICAgY2h1bmswLTAgLS0tLS0tLT4gQVxuICAgIGNodW5rMS0wIC0tPiBBXG4gICAgY2h1bmsyLTAgLS0-IEFcbiAgICBcbiAgICAlJSBhbGlnbm1lbnQgbGlua3MgXG4gICAgY2h1bmswLTAgLS0tIGNodW5rMS0yXG4gICAgY2h1bmsxLTAgLS0tIGNodW5rMi0yXG4gICAgJSUgbWFrZSB0aGUgbGlua3MgaW52aXNpYmxlIFxuICAgIGxpbmtTdHlsZSAxMCBzdHJva2Utd2lkdGg6MnB4LGZpbGw6bm9uZSxzdHJva2U6bm9uZTtcbiAgICBsaW5rU3R5bGUgMTEgc3Ryb2tlLXdpZHRoOjJweCxmaWxsOm5vbmUsc3Ryb2tlOm5vbmU7IiwibWVybWFpZCI6Int9IiwidXBkYXRlRWRpdG9yIjpmYWxzZSwiYXV0b1N5bmMiOnRydWUsInVwZGF0ZURpYWdyYW0iOmZhbHNlfQ)


<details>
<summary>mermaid graph syntax</summary>

```mermaid
flowchart BT
    subgraph live
        B -------------> A
    end
    
    subgraph chunk0
        chunk0-2(("2")) --> chunk0-1((1)) --> chunk0-0((0))
    end

    subgraph chunk1
        chunk1-2(("2")) --> chunk1-1((1)) --> chunk1-0((0))
    end
    
    subgraph chunk2
        chunk2-2(("2")) --> chunk2-1((1)) --> chunk2-0((0))
    end

    
    chunk0-0 -------> A
    chunk1-0 --> A
    chunk2-0 --> A
    
    %% alignment links 
    chunk0-0 --- chunk1-2
    chunk1-0 --- chunk2-2
    %% make the links invisible 
    linkStyle 10 stroke-width:2px,fill:none,stroke:none;
    linkStyle 11 stroke-width:2px,fill:none,stroke:none;
```

</details>



### New approach with "insertion" events

Next we add "insertion" and "chunk" events so it's more presriptive on how each historical chunk should connect to each other and how the homeserver can navigate the DAG.

 - With "insertion" events, we just add them to the start of each chronological chunk (where the oldest message in the chunk is). The next older-in-time chunk can connect to that "insertion" point from the previous chunk.
 - The initial "insertion" event could be from the main DAG or we can create it ad-hoc in the first chunk so the homeserver can start traversing up the chunk from there after a "marker" event points to it.
 - We use "chunk" events to point to the "insertion" event by referencing the "next_chunk_id" from the "insertion" event.
 - Consideration: the "insertion"/"chunk" events add a new way for an application service to tie the chunk reconciliation in knots(similar to the DAG knots that can happen).


![](https://user-images.githubusercontent.com/558581/127040602-e95ac36a-5e64-4176-904d-6abae2c95ae9.png)

[Mermaid live editor playground link](https://mermaid-js.github.io/mermaid-live-editor/edit/#eyJjb2RlIjoiZmxvd2NoYXJ0IEJUXG4gICAgc3ViZ3JhcGggbGl2ZVxuICAgICAgICBCIC0tLS0tLS0tLS0tLS0tLS0tPiBBXG4gICAgZW5kXG4gICAgXG4gICAgc3ViZ3JhcGggY2h1bmswXG4gICAgICAgIGNodW5rMC1jaHVua1tbXCJjaHVua1wiXV0gLS0-IGNodW5rMC0yKChcIjJcIikpIC0tPiBjaHVuazAtMSgoMSkpIC0tPiBjaHVuazAtMCgoMCkpIC0tPiBjaHVuazAtaW5zZXJ0aW9uWy9pbnNlcnRpb25cXF1cbiAgICBlbmRcblxuICAgIHN1YmdyYXBoIGNodW5rMVxuICAgICAgICBjaHVuazEtY2h1bmtbW1wiY2h1bmtcIl1dIC0tPiBjaHVuazEtMigoXCIyXCIpKSAtLT4gY2h1bmsxLTEoKDEpKSAtLT4gY2h1bmsxLTAoKDApKSAtLT4gY2h1bmsxLWluc2VydGlvblsvaW5zZXJ0aW9uXFxdXG4gICAgZW5kXG4gICAgXG4gICAgc3ViZ3JhcGggY2h1bmsyXG4gICAgICAgIGNodW5rMi1jaHVua1tbXCJjaHVua1wiXV0gLS0-IGNodW5rMi0yKChcIjJcIikpIC0tPiBjaHVuazItMSgoMSkpIC0tPiBjaHVuazItMCgoMCkpIC0tPiBjaHVuazItaW5zZXJ0aW9uWy9pbnNlcnRpb25cXF1cbiAgICBlbmRcblxuICAgIFxuICAgIGNodW5rMC1pbnNlcnRpb25CYXNlWy9pbnNlcnRpb25cXF0gLS0tLS0tLS0tLS0tLT4gQVxuICAgIGNodW5rMC1jaHVuayAtLi0-IGNodW5rMC1pbnNlcnRpb25CYXNlWy9pbnNlcnRpb25cXF1cbiAgICBjaHVuazEtY2h1bmsgLS4tPiBjaHVuazAtaW5zZXJ0aW9uXG4gICAgY2h1bmsyLWNodW5rIC0uLT4gY2h1bmsxLWluc2VydGlvblxuIiwibWVybWFpZCI6Int9IiwidXBkYXRlRWRpdG9yIjpmYWxzZSwiYXV0b1N5bmMiOnRydWUsInVwZGF0ZURpYWdyYW0iOmZhbHNlfQ)

<details>
<summary>mermaid graph syntax</summary>

```mermaid
flowchart BT
    subgraph live
        B -----------------> A
    end
    
    subgraph chunk0
        chunk0-chunk[["chunk"]] --> chunk0-2(("2")) --> chunk0-1((1)) --> chunk0-0((0)) --> chunk0-insertion[/insertion\]
    end

    subgraph chunk1
        chunk1-chunk[["chunk"]] --> chunk1-2(("2")) --> chunk1-1((1)) --> chunk1-0((0)) --> chunk1-insertion[/insertion\]
    end
    
    subgraph chunk2
        chunk2-chunk[["chunk"]] --> chunk2-2(("2")) --> chunk2-1((1)) --> chunk2-0((0)) --> chunk2-insertion[/insertion\]
    end

    
    chunk0-insertionBase[/insertion\] -------------> A
    chunk0-chunk -.-> chunk0-insertionBase[/insertion\]
    chunk1-chunk -.-> chunk0-insertion
    chunk2-chunk -.-> chunk1-insertion
```

</details>





The structure of the insertion event would look like:
```js
{
  "type": "m.room.insertion",
  "sender": "@appservice:example.org",
  "content": {
    "m.next_chunk_id": next_chunk_id,
    "m.historical": true
  },
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  // Doesn't affect much but good to use the same time as the closest event
  "origin_server_ts": 1626914158639
}
```


The structure of the chunk event would look like:
```js
{
  "type": "m.room.chunk",
  "sender": "@appservice:example.org",
  "content": {
    "m.chunk_id": chunk_id,
    "m.historical": true
  },
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  // Doesn't affect much but good to use the same time as the closest event
  "origin_server_ts": 1626914158639
}
```



### "Marker" events

Finally, we add "marker" events into the mix so that federated remote servers can also navigate and to know where/how to fetch historical messages correctly.

To lay out the different types of servers consuming these historical messages (more context on why we need "marker" events):

 1. Local server
    - This can pretty much work out of the box. Just add the events to the database and they're available. The new endpoint is just a mechanism to insert the events.
 1. Federated remote server that already has all scrollback history and then new history is inserted
    - The big problem is how does a HS know it needs to go fetch more history if they already fetched all of the history in the room? We're solving this with "marker" events which are sent on the "live" timeline and point back to the "insertion" event where we inserted history next to. The HS can then go and backfill the "insertion" event and continue navigating the chunks from there.
 1. Federated remote server that joins a new room with historical messages
    - We need to update the `/backfill` response to include historical messages from the chunks
 1. Federated remote server already in the room when history is inserted
    - Depends on whether the HS has the scrollback history. If the HS already has all history, see scenario 2, if doesn't, see scenario 3.
 1. For federated servers already in the room that haven't implemented MSC2716
    - Those homeservers won't have historical messages available because they're unable to navigate the "marker"/"insertion" events. But the historical messages would be available once the HS implements MSC2716 and processes the "marker" events that point to the history.


---

 - A "marker" event simply points back to an "insertion" event.
 - The "marker" event solves the problem of, how does a federated homeserver know about the historical events which won't come down incremental sync? And the scenario where the federated HS already has all the history in the room, so it won't do a full sync of the room again.
 - Unlike the historical events, the "marker" event is sent as a normal event on the "live" timeline so that comes down incremental sync and is available to all homeservers regardless of how much scrollback history they already have.
    - Note: If a server joins after a "marker" event is sent, it could be lost in the middle of the timeline and they could jump back in time past the "marker" and never pick it up. But `backfill/` response should have historical messages included. It gets a bit hairy if the server has the room backfilled, the user leaves, a "marker" event is sent, more messages put it back in the timeline, the user joins back, jumps back in the timeline and misses the "marker" and expects to see the historical messages. They will be missing the historical messages until they can backfill the gap where they left.
 - A "marker" event is not needed for every chunk/batch of historical messages. Multiple chunks can be inserted then once we're done importing everything, we can add one "marker" event pointing at the root "insertion" event
    - If more history is decided to be added later, another "marker" can be sent to let the homeservers know again.
 - When a remote federated homeserver, receives a "marker" event, it can mark the "insertion" prev events as needing to backfill from that point again and can fetch the historical messages when the user scrolls back to that area in the future.
 - We could remove the need for "marker" events if we decided to only allow sending "insertion" events on the "live" timeline at any point where you would later want to add history.  But this isn't compatible with our dynamic insertion use cases like Gitter where the rooms already exist with no "insertion" events at the start of the room, and the examples from this MSC like NNTP (newsgroup) and email which can potentially want to branch off of everything.

The structure of the "marker" event would look like:
```js
{
    "type": "m.room.marker",
    "sender": "@appservice:example.org",
    "content": {
        "m.insertion_id": insertion_event.event_id,
        "m.historical": true
    },
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "origin_server_ts": 1626914158639,
}
```

![](https://user-images.githubusercontent.com/558581/127429607-d67b6785-050f-4944-bd11-f31870ed43a0.png)

[Mermaid live editor playground link](https://mermaid-js.github.io/mermaid-live-editor/edit/#eyJjb2RlIjoiZmxvd2NoYXJ0IEJUXG4gICAgc3ViZ3JhcGggbGl2ZVxuICAgICAgICBtYXJrZXIxPlwibWFya2VyXCJdIC0tLS0-IEIgLS0tLS0tLS0tLS0tLS0tLS0-IEFcbiAgICBlbmRcbiAgICBcbiAgICBzdWJncmFwaCBjaHVuazBcbiAgICAgICAgY2h1bmswLWNodW5rW1tcImNodW5rXCJdXSAtLT4gY2h1bmswLTIoKFwiMlwiKSkgLS0-IGNodW5rMC0xKCgxKSkgLS0-IGNodW5rMC0wKCgwKSkgLS0-IGNodW5rMC1pbnNlcnRpb25bL2luc2VydGlvblxcXVxuICAgIGVuZFxuXG4gICAgc3ViZ3JhcGggY2h1bmsxXG4gICAgICAgIGNodW5rMS1jaHVua1tbXCJjaHVua1wiXV0gLS0-IGNodW5rMS0yKChcIjJcIikpIC0tPiBjaHVuazEtMSgoMSkpIC0tPiBjaHVuazEtMCgoMCkpIC0tPiBjaHVuazEtaW5zZXJ0aW9uWy9pbnNlcnRpb25cXF1cbiAgICBlbmRcbiAgICBcbiAgICBzdWJncmFwaCBjaHVuazJcbiAgICAgICAgY2h1bmsyLWNodW5rW1tcImNodW5rXCJdXSAtLT4gY2h1bmsyLTIoKFwiMlwiKSkgLS0-IGNodW5rMi0xKCgxKSkgLS0-IGNodW5rMi0wKCgwKSkgLS0-IGNodW5rMi1pbnNlcnRpb25bL2luc2VydGlvblxcXVxuICAgIGVuZFxuXG4gICAgXG4gICAgbWFya2VyMSAtLi0-IGNodW5rMC1pbnNlcnRpb25CYXNlXG4gICAgY2h1bmswLWluc2VydGlvbkJhc2VbL2luc2VydGlvblxcXSAtLS0tLS0tLS0tLS0tPiBBXG4gICAgY2h1bmswLWNodW5rIC0uLT4gY2h1bmswLWluc2VydGlvbkJhc2VbL2luc2VydGlvblxcXVxuICAgIGNodW5rMS1jaHVuayAtLi0-IGNodW5rMC1pbnNlcnRpb25cbiAgICBjaHVuazItY2h1bmsgLS4tPiBjaHVuazEtaW5zZXJ0aW9uXG4iLCJtZXJtYWlkIjoie30iLCJ1cGRhdGVFZGl0b3IiOmZhbHNlLCJhdXRvU3luYyI6dHJ1ZSwidXBkYXRlRGlhZ3JhbSI6ZmFsc2V9)

<details>
<summary>mermaid graph syntax</summary>

```mermaid
flowchart BT
    subgraph live
        marker1>"marker"] ----> B -----------------> A
    end
    
    subgraph chunk0
        chunk0-chunk[["chunk"]] --> chunk0-2(("2")) --> chunk0-1((1)) --> chunk0-0((0)) --> chunk0-insertion[/insertion\]
    end

    subgraph chunk1
        chunk1-chunk[["chunk"]] --> chunk1-2(("2")) --> chunk1-1((1)) --> chunk1-0((0)) --> chunk1-insertion[/insertion\]
    end
    
    subgraph chunk2
        chunk2-chunk[["chunk"]] --> chunk2-2(("2")) --> chunk2-1((1)) --> chunk2-0((0)) --> chunk2-insertion[/insertion\]
    end

    
    marker1 -.-> chunk0-insertionBase
    chunk0-insertionBase[/insertion\] -------------> A
    chunk0-chunk -.-> chunk0-insertionBase[/insertion\]
    chunk1-chunk -.-> chunk0-insertion
    chunk2-chunk -.-> chunk1-insertion
```

</details>





### Limit who can send historical messages

Since events being silently sent in the past is hard to moderate, it will probably be good to limit who can add historical messages to the timeline. The batch send endpoint is already limited to application services but we also need to limit who can send "insertion", "chunk", and "marker" events since someone can attempt to send them via the normal `/send` API (we don't want any nasty weird knots to reconcile either)

We can limit and protect from this by introducing a new `historical` power level which controls who can send "insertion", "chunk", and "marker" events. Since we're changing the power levels and `event_auth.py` stuff in Synapse, this probably requires a new room version. For experimenting, we can use an experimental room version, `org.matrix.msc2716`.

Alternatively, we can use the existing `events` power level. For the default and existing rooms, if the "insertion", "chunk", and "marker" event PL levels are unset, we can completely disallow sending of those events in the room. This lets people opt-in and set a power level when they want an application service to start inserting history.




