# MSC3440 Threading via `m.thread` relation

## Problem

Threading is a great way to create alternative timelines to group messages related to each other. This is particularly useful in high traffic rooms where multiple conversations can happen in parallel or when a single discussion might stretch over a very long period of time.

The main goal when implementing threads is to create conversations that are easier to follow and smoother to read.

There have been several experiments in threading for Matrix...

 - [MSC2326](https://github.com/matrix-org/matrix-doc/pull/2326): Label based filtering
 - [MSC2836](https://github.com/matrix-org/matrix-doc/pull/2836): Threading by serverside traversal of relationships
 - "Threads as rooms"

...but none have yet been widely adopted due to the upheaval of implementing an entirely new Client-Server API construct in the core message sending/display path.

Meanwhile, threading is very clearly a core requirement for any modern messaging solution, and Matrix uptake is suffering due to the lack of progress.

## Proposal

### Event format

A new relation would be used to express that an event belongs to a thread.

```json
"m.relates_to": {
  "rel_type": "m.thread",
  "event_id": "$thread_root"
}
```
Where $thread_root is the event ID of the root message in the thread.

A big advantage of relations over quote replies is that they can be server-side aggregated. It means that a client is not bound to download the entire history of a room to have a comprehensive list of events being part of a thread.

It will have a custom aggregation  which is a summary of the thread: the latest message, a list of participants and the total count of messages. I.e. in places which include bundled relations (per [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)), the thread root would include additional information in the `unsigned` field:

```json
{
  "latest_event": {
    "content": { ... },
    ...
  },
  "senders": ["@john:example.com", ...],
  "count": 7
}
```

#### Quote replies in a thread 

No recommendation to modifying quote replies is made, this would still be handled via the `m.in_reply_to` field of `m.relates_to`. Thus you could quote a reply in a thread:

```json
"m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "$thread_root",
    "m.in_reply_to": {
        "event_id": "$event_target"
    }
}
```

It is possible that an `m.in_reply_to` event targets an event that is outside the
related thread. Clients should always do their upmost to display the quote-reply
and upon clicking it the event should be displayed and highlighted in its original context.

### Fetch all replies to a thread

To fetch an entire thread, the `/relations` API can be used as defined in [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)

```
GET /_matrix/client/unstable/rooms/!room_id:domain/relations/$thread_root/m.thread
```

Where `$thread_root` is the event ID of the root message in the thread.

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) would need to be clarified to ensure that returned messages include any bundled relations necessary for displaying the thread, e.g. reactions to the threaded events.

### Fetch all threads in a room

To fetch all threads in a room it is proposed to use the [`/messages`](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-rooms-roomid-messages) API and expand the room event filtering to include relations. The `RoomEventFilter` will take additional parameters:

* `relation_types`: A list of relation types which must be bundled with the event to include it. If this list is absent then no filtering is done on relation types.
* `relation_senders`: A list of senders of relations...

This can also be combined with the `sender` field to search for threads which a user has participated in (or not participated in).

```
GET /_matrix/client/unstable/rooms/!room_id:domain/messages/filter=...
```

Where filter would be JSON and URL-encoded string include the above new fields:

```json
{
  "types": ["m.room.message"],
  "relation_senders": [...],
  "relation_types": ["m.thread"]
}
```

### Limitations

#### Read receipts

Read receipts and read markers assume a single chronological timeline. Threading changes that assumption making the current API not very practical.

Clients can synthetize read receipts but it is possible that some notification get lost upon a fresh start where the clients have to start off the `m.read` information received from the homeserver.

Synchronising the synthesized notification count across devices will present its own challenges and is probably undesirable at this stage. The preferred route would be to create another MSC to make read receipts support multiple timelines in a single room.

#### Single-layer event aggration

Bundling only includes relations a single-layer deep, so it might return an event with `m.thread` relation, the `m.annotation` to that event and the `m.reference` relations to that event, but not the `m.annotation` to the `m.reference`.

### Client considerations

#### Display "m.thread" as "m.in_reply_to"

It is possible for clients to provide a backwards compatible experience for users by treating the new relation `m.thread` the same way they would treat a `m.in_reply_to` event.

Failing to do the above should still render the event in the room's timeline. It might create a disjointed experience as events might lack the original context for correct understanding.

#### Sending `m.thread` before fully implementing threads

To ensure maximum compability and continuity in the conversation it is recommend for clients who do not fully support threads yet to adapt the `m.relates_to` body to use the `m.thread` relation type when replying to a threaded event.

This will help threads enabled clients to render the event in the place that gives the maximum context to the users.

As a fallback, it is recommended that clients make clicking on a quote reply related to a threaded event open that thread and highlight the corresponding event

## Alternatives

[MSC2836](https://github.com/matrix-org/matrix-doc/pull/2836), "Threading as rooms", building on `m.in_reply_to` are the main alternatives here. The first two are non-overlapping with this MSC.

### Threads as rooms

The provides full server-side APIs for navigating trees of events, and could be considered an extension of this MSC for scenarios which require that capability (e.g. Twitter-style microblogging as per [Cerulean](https://matrix.org/blog/2020/12/18/introducing-cerulean), or building an NNTP or IMAP or Reddit style threaded UI)

"Threads as rooms" is the idea that each thread could just get its own Matrix room in parallel with the one which spawned the thread.

Advantages to "Threads as rooms" include:
 * May be simpler for client implementations.
 * Also requires minimal Client-Server API changes

Disadvantages include:
 * Access control, membership, history visibility, room versions etc needs to be synced between the thread-room and the parent room
 * Harder to control lifetime of threads in the context of the parent room if they're completely split off
 * Clients which aren't aware of them are going to fill up with a lot of rooms.
 * Bridging to non-threaded chat systems is trickier as you may have to splice together rooms
 * The sheer number of rooms involved probably makes it dependent on `/sync` v3 landing (the to-be-specced next generation of `/sync` which is constant-time complexity with your room count).

### Threads via m.in_reply_to

The rationale for using a new relation type instead of building on `m.in_reply_to` is to re-use the event relationship APIs provided by [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675). The MSC3267 definition of `m.reference` relationships could be updated to mention threads (perhaps by using the key field from [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) as the thread ID), but it is clearer to define a new relation type. It is unclear what impact this would have on [MSC3267](https://github.com/matrix-org/matrix-doc/pull/3267), but that is unimplemented by clients.

## Security considerations

None

## Unstable prefix

Clients and servers should use list of unstable prefixes listed below while this MSC has not been included in a spec release.

  * `io.element.thread` should be used in place of `m.thread` as relation type
  * `io.element.relation_senders` should be used in place of `relation_senders` in the `RoomEventFilter`
  * `io.element.relation_types` should be used in place of `relation_types` in the `RoomEventFilter`