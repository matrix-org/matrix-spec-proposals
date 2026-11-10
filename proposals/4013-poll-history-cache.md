# MSC4013: Poll history cache

The purpose of this MSC is to allow clients to quickly fetch all the polls in a given room (aka “Poll history”).

## Problem

Clients sometimes may want to access quickly to all the polls sent in a given room (similarly to how they may want to
access all the media being sent in a room).Today clients don’t have an efficient way to make such an operation. 
Clients that want to implement this feature for encrypted rooms on the status quo may need to backward paginate on the 
room’s timeline until all the polls are found or they reach the beginning of the timeline. For unencrypted rooms the 
problem doesn't exist since clients can call the 
[messages API](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv3roomsroomidmessages) 
filtering by event type (e.g. by `m.poll.start`).

## Proposal

Introduce a new state event `m.room.poll_history`. This state event is supposed to be referenced by any `m.poll.start` 
that will be sent next in the room. The new state event must have an empty string as `state_key`.
More information on polls can be found on the [MSC3381](https://github.com/matrix-org/matrix-spec-proposals/pull/3381).

This is how the new state event would look like:

```json5
{
   // irrelevant fields not shown
   "content": {},
   "state_key": "",
   "type": "m.room.poll_history",
   "event_id": "poll_history_id"
}

```

### Dependencies
- [MSC3381](https://github.com/matrix-org/matrix-spec-proposals/pull/338)

## Client behaviour
First of all a room creator sends the new `m.room.poll_history` state event in the `initial_state` when calling the 
[createRoom API](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3createroom).

For example the body when creating a new encrypted room would look like this:

```json5
{
    "preset": "private_chat",
    "name": "Some room",
    "is_direct": false,
    "initial_state": [
      // ... other state events
      {
        "stateKey": "",
        "type": "m.room.encryption",
        "content": {
          "algorithm": "m.megolm.v1.aes-sha2"
        }
      },
      {
        "stateKey": "",
        "type": "m.room.poll_history",
        "content": {}
      }
    ]
}
```


Any time a client starts a new poll, it also includes a reference to the above state event id like this:

```json5
{
    "type": "m.poll.start",
    // irrelevant fields not shown
    "content": {
        "m.poll.start": {
            "kind": "m.poll.disclosed",
            "answers": [ 
                {"id": "id_a", "m.text": "Yes"},
                {"id": "id_b", "m.text": "No"}
            ],
            "question": { "m.text": "Do you like polls?" },
            "max_selections": 1,
        },
        // reference to the state event of type "m.room.poll_history"
        "m.relates_to": {
            "event_id": "poll_history_id",
            "rel_type": "m.reference"
        }    
    }
}
```

Clients can now use the event relationship to fetch the history of polls in the room:

1. They call the [relations API](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv1roomsroomidrelationseventid) 
with the new state event’s event identifier (`poll_history_id` in the example). Since the API takes a timeline direction 
and a pagination token, clients still have the flexibility to decide how many polls they want to fetch in a given room 
and in which direction. 
    
    The request would look like this:
    
    `/_matrix/client/v1/rooms/{Room ID}/relations/poll_history_id/m.reference?from=from_token&dir=b&limit=100`
    
    The [response](https://spec.matrix.org/v1.6/client-server-api/#server-side-aggregation-of-mreference) will contain 
    an array of related event identifiers. In encrypted rooms these events have likely the type `m.room.encrypted`. 
    After the decryption clients should keep just decrypted events of type `m.poll.start`.
4. For each event `id_some` kept from the previous step, clients need to make the poll aggregation either by fetching 
data from a local database (if available) or by calling again the relations API again with the `id_some` event id. 
At this point clients have all the information they need to build the full poll history.

## Potential issues

### History on already existing rooms
It’s desirable to have the new `m.room.poll_history` state as a part of the `initial_state` of a room, but sometimes 
people may want to have a similar behaviour on already existing rooms. In this case a user with enough power level can 
just publish a `m.room.poll_history` event in the room. It is worth noticing that in this cases `m.poll.start` events 
sent before wouldn't have any relationship with the state event. 

### Rooms with both old and new clients
Clients understanding the new `m.room.poll_history` state event should still not fetch the poll history as described 
above if the `m.room.poll_history` is missing in a room. It's still possible however to have old and new clients in a 
room supporting the poll history. In this case new clients wouldn't see new polls opened by old clients in the poll 
history. This problem doesn't affect the room's timeline.

### Privacy
Even in encrypted rooms references to other events (key `m.relates_to`) are clear text. With this proposal, starting a
poll in an encrypted room means sending an event of type `m.room.encrypted` having a reference to the state event id of
type  `m.room.poll_history`. Since state events are also clear text, people may infer that the actual content of the
encrypted message is actually a started poll (although its content is still encrypted).

## Power levels considerations
The new `m.room.poll_history` event isn’t supposed to change over time. For this reason the power level required to
change the  `m.room.poll_history` event should be as high as the the one required for changing the state event
`m.room.power_levels` (or similar).

## Possible extensions

The problem this MSC is trying  to fix here is to build an index for events of a given type (`m.poll.start` in this case).
In theory this approach can be useful to group other events together (e.g. images) with the purpose to show them
together on clients. To fix this problem we can think of a more generic state event type `m.room.history` and use the
`state_key` to differentiate several types of events.

For polls the state event would look like this:

```json5
{
   // irrelevant fields not shown
   "content": {},
   "state_key": "m.poll.start",
   "type": "m.room.history",
   "event_id": "poll_history_id"
}

```

## Alternatives considered

### State event for each poll

An alternative can be to have multiple instances of the same state event `m.room.poll_history` but with different
`state_key`s.  In this case the client opening a poll is also required to send a state event with the `state_key` equal
to `@sender:somewhere.org_XYZ`. The string `XYZ` should be a unique token for the poll. The perfect candidate is the
event id of the `m.poll.start` event. 
The poll history can later be built by fetching all the state events with type `m.room.poll_history` by calling the
[state API](https://spec.matrix.org/v1.6/client-server-api/#get_matrixclientv3roomsroomidstateeventtypestatekey).
This is possible since here the state event also contains the event id of the `m.poll.start` event: 

```json5
{
   // irrelevant fields not shown
   "content": { 
       // the id of the `m.poll.start` event
       "poll_id": "poll started event id"
   },
    // Potentially XYZ == the id of the `m.poll.start` event
   "state_key": "@someone:somewhere.org_XYZ",
   "type": "m.room.poll_history",
   "event_id": "poll_history_id"
}

```

Potential problems with this approach however are:
- Users opening a poll need enough power level to send a state event (`m.room.poll_history`)
- This approach has an additional dependency:
[MSC3757](https://github.com/matrix-org/matrix-spec-proposals/blob/andybalaam/owner-state-events/proposals/3757-restricting-who-can-overwrite-a-state-event.md)

### State event containing an array of poll started events

The idea here is to introduce new state event as the main proposal. The only difference is that here clients are
supposed to update the state event every time they open a new poll. The new state event's purpose is to contain all the
ids for `m.poll.start` events.

The new state event would look like this:
```json5
{
   // irrelevant fields not shown
   "content": { 
       "polls":  [
           "poll_started_a_id",
           "poll_started_b_id",
       
       ]
   },
   "state_key": "",
   "type": "m.room.poll_history",
   "event_id": "poll_history_id"
}

```

Potential problems with this approach are:
- Users opening a poll need enough power level to send a state event (`m.room.poll_history`)
- Conflicts may arise when two users attempt to change the state event at the same time
- A malicious user or a bug in a client may accidentally erase the history sending a wrong payload

# Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc4013.*` as a prefix in place of
`m.*` for the new state event type.
