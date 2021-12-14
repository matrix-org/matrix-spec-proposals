# MSC3440 Threading via `m.thread` relation

## Problem

Threading is a great way to create alternative timelines to group messages related 
to each other. This is particularly useful in high traffic rooms where multiple 
conversations can happen in parallel or when a single discussion might stretch 
over a very long period of time.

The main goal when implementing threads is to create conversations that are easier 
to follow and smoother to read.

There have been several experiments in threading for Matrix...

 - [MSC2326](https://github.com/matrix-org/matrix-doc/pull/2326): 
 Label based filtering
 - [MSC2836](https://github.com/matrix-org/matrix-doc/pull/2836): 
 Threading by serverside traversal of relationships
 - "Threads as rooms"
 - Building threads off `m.in_reply_to`

Meanwhile, threading is very clearly a core requirement for any modern messaging 
solution, and Matrix uptake is suffering due to the lack of progress.

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

A big advantage of relations over quote replies is that they can be server-side 
aggregated. It means that a client is not bound to download the entire history of 
a room to have a comprehensive list of events being part of a thread.

When a thread head is aggregated (as in MSC2675), returns a summary of the thread: 
the latest message, a list of participants and the total count of messages. 
I.e. in places which include bundled relations (per 
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)), the thread root 
would include additional information in the `unsigned` field:

```json
{
  "latest_event": {
    "content": { ... },
    ...
  },
  "count": 7,
  "current_user_participated": true
}
```

* `latest_event`: A reference to the last `m.thread` relation part of the thread
* `count`: An integer counting the number of `m.thread` events
* `current_user_participated`: A flag set to `true` if the current logged in user
  has participated in the thread

#### Quote replies in a thread 

No recommendation to modifying quote replies is made, this would still be handled 
via the `m.in_reply_to` field of `m.relates_to`. Thus you could quote a reply in a thread:

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

To fetch an entire thread, the `/relations` API can be used as defined in 
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675)

```
GET /_matrix/client/unstable/rooms/!room_id:domain/relations/$thread_root/m.thread
```

Where `$thread_root` is the event ID of the root message in the thread.

In order to properly display a thread it is necessary to retrieve the relations 
to threaded events, e.g. the reactions to the threaded events. This proposes 
clarifying [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) that 
the `/relations` API includes bundled relations. This follows what MSC2675 already describes:

> Any API which receives events should bundle relations (apart from non-gappy 
incremental syncs), for instance: initial sync, gappy incremental sync, 
/messages and /context.

### Fetch all threads in a room

To fetch all threads in a room it is proposed to use the 
[`/messages`](https://matrix.org/docs/spec/client_server/latest#get-matrix-client-r0-rooms-roomid-messages) 
API and expand the room event filtering to include relations. The `RoomEventFilter` 
will take additional parameters:

* `relation_types`: A list of relation types which must be exist pointing to the event
  being filtered. If this list is absent then no filtering is done on relation types.
* `relation_senders`: A list of senders of relations which must exist pointing to
  the event being filtered. If this list is absent then no filtering is done on relation types.

This can also be combined with the `sender` field to search for threads which a 
user has participated in (or not participated in).

```
GET /_matrix/client/unstable/rooms/!room_id:domain/messages?filter=...
```

The filter string would include the new fields, above. In this example, the URL 
encoded JSON is presented unencoded and formatted for legibility:

```json
{
  "types": ["m.room.message"],
  "relation_senders": [...],
  "relation_types": ["m.thread"]
}
```

### Limitations

#### Read receipts

Read receipts and read markers assume a single chronological timeline. Threading 
changes that assumption making the current API not very practical.

Clients can synthetize read receipts but it is possible that some notifications get 
lost upon a fresh start where the clients have to start off the `m.read` 
information received from the homeserver.

Synchronising the synthesized notification count across devices will present its 
own challenges and is probably undesirable at this stage. The preferred route 
would be to create another MSC to make read receipts support multiple timelines 
in a single room.

#### Single-layer event aggration

Bundling only includes relations a single-layer deep. This MSC is not looking to
solve nested threading but is rather focusing on bringing mechanisms to allow
threading in chat applications

Nested threading is out of scope for this proposal and would be the subject of
a different MSC.
A `m.thread` event can only reference events that do not have a `rel_type`

```
[
  {
    "event_id": "ev1",
    ...
  },
  {
    "event_id": "ev2",
    ...
    "m.relates_to": {
      "rel_type": "m.thread",
      "event_id": "ev1",
      "m.in_reply_to": {
          "event_id": "ev1"
      }
    }
  },
  {
    "event_id": "ev3",
    ...
    "m.relates_to": {
      "rel_type": "m.annotation",
      "event_id": "ev1",
      "key": "✅"
    }
  }
]
```

Given the above list of events, only `ev1` would be a valid target for an `m.thread`
relation event.

### Client considerations

#### Display "m.thread" as "m.in_reply_to"

Clients that don't support threads will render threaded messages in the room's 
timeline at the point at which they were sent. This does risk a confusing experience 
for those on such clients, but options to mitigate this are limited.

Having older clients treat threaded messages as replies would give a better 
experience, but adding reply metadata in addition to thread metadata would mean 
replies could not then be used in threads and would be significant extra metadata.

Clients that wish to offer basic thread support can display threads as replies to 
the thread root message. See matrix-org/matrix-react-sdk#7109 for an example.

#### Sending `m.thread` before fully implementing threads

Clients that do not support threads yet should include a `m.thread` relation to the 
event body if a user is replying to an event that has an `m.thread` relation type

This is done so that clients that support threads can render the event in the most 
relevant context.

If a client does not include that relation type to the outgoing event, it will be 
rendered in the room timeline with a quote reply that should open and highlight the 
event in the thread context when clicked.

When replying to the following event, a client that does not support thread should 
copy in `rel_type` and `event_id` properties in their reply mixin.

```
{
  ...
  "m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "ev1"
  }
}
```

## Alternatives

[MSC2836](https://github.com/matrix-org/matrix-doc/pull/2836), "Threading as rooms", and 
building on `m.in_reply_to` are the main alternatives here. The first two are 
non-overlapping with this MSC.

It is also worth noting that relations in this MSC could be expressed using the 
scalable relation format described in [MSC3051](https://github.com/matrix-org/matrix-doc/pull/3051).

### Threads as rooms

Threads as rooms could provide full server-side APIs for navigating trees of events, 
and could be considered an extension of this MSC for scenarios which require that 
capability  (e.g. Twitter-style microblogging as per 
[Cerulean](https://matrix.org/blog/2020/12/18/introducing-cerulean), or building 
an NNTP or IMAP or Reddit style threaded UI)

"Threads as rooms" is the idea that each thread could just get its own Matrix room..

Advantages to "Threads as rooms" include:
 * May be simpler for client implementations.
 * Restricting events visiblity as the room creator
 * Ability to create read-only threads

Disadvantages include:
 * Access control, membership, history visibility, room versions etc needs to be 
 synced between the thread-room and the parent room
 * Harder to control lifetime of threads in the context of the parent room if 
 they're completely split off
 * Clients which aren't aware of them are going to fill up with a lot of rooms.
 * Bridging to non-threaded chat systems is trickier as you may have to splice 
 together rooms

### Threads via serverside traversal of relationships MSC2836

Advantages include:
 * Fits other use cases than instant messaging
 * Simple possible API shape to implement threading in a useful way

Disadvantages include:
 * Relationships are queried using `/event_relationships` which is outside the 
 bounds of the `/sync` API so lacks the nice things /sync gives you (live updates). 
 That being said, the event will come down `/sync`, you just may not have the 
 context required to see parents/siblings/children.
 * Threads can be of arbitrary width (unlimited direct replies to a single message) 
 and depth (unlimited chain of replies) which complicates UI design when you just 
 want "simple" threading.
 * Does not consider use cases like editing or reactions

### Threads via m.in_reply_to

The rationale for using a new relation type instead of building on `m.in_reply_to` 
is to re-use the event relationship APIs provided by 
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675). The MSC3267 definition 
of `m.reference` relationships could be updated to mention threads (perhaps by 
using the key field from [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) 
as the thread ID), but it is clearer to define a new relation type. It is unclear 
what impact this would have on [MSC3267](https://github.com/matrix-org/matrix-doc/pull/3267), 
but that is unimplemented by clients.

## Security considerations

None

## Unstable prefix

Clients and servers should use list of unstable prefixes listed below while this 
MSC has not been included in a spec release.

  * `io.element.thread` should be used in place of `m.thread` as relation type
  * `io.element.relation_senders` should be used in place of `relation_senders` 
  in the `RoomEventFilter`
  * `io.element.relation_types` should be used in place of `relation_types` 
  in the `RoomEventFilter`

## Dependencies

This MSC builds on [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674), 
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) and, 
[MSC3567](https://github.com/matrix-org/matrix-doc/pull/3567/files)  (which at the 
time of writing have not yet been accepted into the spec).
