# MSC4334: Per-room language support.

This MSC is to add a new `m.room.language` state event. This would allow users to set a desired
language preference for each room which would aid in client feature development.

Features such as message search require a tokenizer which depend on the language being tokenized.
Enabling per-room language setting would allow a multi-lingual user to have search working in 
different languages across rooms.

Accessibility features such as screen readers would also benefit from knowing what language they
are reading.

## Proposal

Add a new `m.room.language` state event. This would hold a single field `"language": <language>`
and an empty `state_key`, similar to the `m.room.name`, using the 
[IETF BCP 47](https://datatracker.ietf.org/doc/bcp47/).

Here is an example event:
```json
{
  "content": {
    "language": "en-US"
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "state_key": "",
  "type": "m.room.language",
  "unsigned": {
    "age": 1234,
    "membership": "join"
  }
}
```

## Alternatives

Rather than adding a new state event, this could be a client setting. However, the drawbacks of
this are that each member of a room would have to ensure they have the right language setting. 

## Security considerations

There are no security concerns. 

## Unstable prefix

Unstable implementations of this proposal should use `org.matrix.msc4334.room.language` which will 
chang to `m.room.language` when stable.
