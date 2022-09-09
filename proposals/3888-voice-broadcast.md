# MSC3888: Voice Broadcast

As a user I want to be able to send a voice broadcast to all users of a room,
so that I can easily provide information by just talking.
Compared to already existing voice messages it should be possible to listen to
voice broadcast at the time they are being recorded.
Think of this being a live-podcast over Matrix.

Some use-case scenarios for this feature can be to verbally provide updates,
trainings, or talk to a large number of people.


## Proposal

This MSC proposes using chunks of voice messages to implement the Voice 
Broadcast feature. It will built on top of [MSC3245: Voice Messages][MSC3245]
and is heavily inspired by [MSC3489: Live Location Sharing][MSC3489].

A new state event `m.voice_broadcast_info` will be introduced. This state event
identifies a broadcast and provides its state, such as "started" or "paused".
In addition to that `m.voice` messages will receive a relation to the state
event to mark them as voice broadcast chunks.

`m.voice_broadcast_info` event example:

```json
{
    "type": "m.voice_broadcast_info,
    "state_key": "@matthew:matrix.org",
    "content": {
        "state": "started",
    }
}
```

- `type` is `m.voice_broadcast_info`.
- `state_key` contains the broadcaster's MXID.
- `state` describes the broadcast state as listed:
  - `running` flags a voice broadcast as currently being live.
  - `paused` stands for a paused broadcast that may be resumed.
  - `stopped` marks a broadcast as finished.

`m.voice` messages that belong to the broadcast will have a [MSC3267][MSC3267] 
relation to the identifying state event.

Example of a voice message as part of a broadcast:

```json
{
    "type": "m.voice",
    "content": {
        "m.relates_to": {
            "rel_type": "m.reference",
            "event_id": "$voice_broadcast_info_event_id",
        }
    }
}
```


## Potential Issues

### Not Actually Being Live

Compared to a streaming solution the chunked voice message broadcast is not
actually live. Instead there will always be an offset of the chosen length of
the single voice chunks. For example if someone asks for a live response in chat
during his broadcast, he won't receive an immediate response.


### Client Fallback Behaviour

Depending on the chosen length of each broadcast chunk clients not supporting
this MSC will receive a number of message. Example for an 1 hour broadcast and
a five minute chunk length: 60 / 5 = 20 messages. This can be quite annoying.

TODO: Can we disable notifications for N > 1 chunk messages?


## Alternatives

### Video/Voice rooms with recording

Server-side recording would be required for reliable recording. It would be 
quite challenging to do this with maintaining end-to-end-encryption.


#### Element Call

In order for voice broadcasts to support a large number of listeners, 
it would rely on SFU (selective forwarding unit), which is not yet ready.


### Streaming File Transfer


## Unstable Prefix

Until this MSC lands, the following unstable prefixes should be used:

`m.voice_broadcast_info` → `org.matrix.msc3888.voice_broadcast_info`
`state` → `org.matrix.msc3888.state`

Example of the state event with unstable prefix:

```json
{
    "type": "m.voice_broadcast_info,
    "state_key": "@matthew:matrix.org",
    "content": {
        "org.matrix.msc3888.state": "started",
    }
}
```


[MSC3245]: https://github.com/matrix-org/matrix-spec-proposals/blob/travis/msc/voice-messages/proposals/3245-voice-messages.md
[MSC3489]: https://github.com/matrix-org/matrix-spec-proposals/blob/matthew/location-streaming/proposals/3489-location-streaming.md
[MSC3267]: https://github.com/matrix-org/matrix-spec-proposals/blob/aggregations-references/proposals/3267-reference-relations.md
