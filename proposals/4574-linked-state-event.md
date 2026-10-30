# MSC4574: Linked State Event

A lot of words have been spilled over how matrix could provide for encrypted state events,
but none has gone far enough to be fully specified and actively implemented. However, in
practice this problem still has arisen and is being actively addressed, at least partially.

This MSC explains how this current approach that exists in the wild works in principle and
proposes to make minor changes to the existing protocol to provide for this pattern to be
a slightly more elegant solution for at least some of the use cases.

## In principle: just link the event

The current approach is as simple as it is elegant. Rather than dealing with encryption
on the state layer directly, the state event content is split into two events: a regular
encrypted event to the room, which contains the encrypted state and then a second state
event of a custom type which essentially just references the event ID of the encrypted
state event.

Now when the client needs to look up the actual state, it just reads the custom state
event of the room and then looks up the corresponding actual event, decrypts it and knows
the actual state of the room. This approach is simple and straight forward. No complex
state machine and potential ordering problems in the regular event stream as the latest
state event always points to the full latest state. And thanks to having event ID in there
even if this other event was longer ago, the client can just fetch it from the server.

At least for non critical state events, this approach is simple and effective, as the
DAG and the regular permission system applies to the state event. The minor drawback
is that you create a level of indirection between the state event and the actual state
and still get all the problems of the regular decryption process (e.g. what if that event
was before your time?).

### Examples this is used in practice

- [Nordeck's Whiteboard uses this approach](https://github.com/nordeck/matrix-neoboard/blob/main/docs/model/matrix-events.md#netnordeckwhiteboard-state-event)
  to keep track of the state of the latest whiteboard without revealing the information
  outside the e2ee channel.
- [FitKo Neo is proposing this approach](https://gitlab.opencode.de/fitko/matrix-g2x/solution-architecture/-/merge_requests/57/diffs#line_a9ecc80c6_A1540)\
  to track channel metadata that needs to stay private

## Proposal: A linked state event type

The indirection also makes the lookup slower and potentially a requires additional network
requests. This MSC proposes to change that by introducing a new state event field that
the server understands and allows to resolve that relationship directly.

This MSC proposes creating a new relationship type (`rel_type`) `m.state_content` that indicates
this relationship. Any state event's `content` can use that relationship to point to the actual
event with the, potentially encrypted, state content. If that field is present, and the server CAN
resolve the relationship in the same room, it SHOULD include the event when delivering the state
event under a new  `linked_event` field.

By including the entire event already in the state event, next to the local `content`, the server
saves the client a network request to fetch the linked event and allows for faster state processing.

### Example state event with linked event'

```json
{
    "type": "m.room.custom_state",
    "state_key": "someKey",
    "content": {
        "rel_type": "m.state_content",
        "event_id": "$someEventId:example.org"
    }
}
```

### Example delivered state event with linked encrypted event

```json
{
  "type": "m.room.custom_state",
  "state_key": "someKey",
  "content": {
      "rel_type": "m.state_content",
      "event_id": "$someEventId:example.org"
  },
  "linked_event": {
    "content": {
      "algorithm": "m.megolm.v1.aes-sha2",
      "ciphertext": "AwgAEnACgAkLmt6qF84IK++J7UDH2Za1YVchHyprqTqsg...",
      "device_id": "RJYKSTBOIE",
      "sender_key": "IlRMeOPX2e0MurIyfWEucYBRVOEEUMrOHqn/8mLqMjA",
      "session_id": "X3lUlvLELLYxeTx4yOVu6UDpasGEVO0Jbu+QFnm0cKQ"
    },
    "event_id": "$someEventId:example.org",
    "origin_server_ts": 1432735824653,
    "sender": "@alice:example.org",
    "type": "m.room.encrypted",
    "unsigned": {
      "age": 1234,
    }
  }
}
```
