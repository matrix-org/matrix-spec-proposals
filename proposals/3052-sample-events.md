# MSC3052: Sample events

Sample events are intended as a generic representation of timing-sensitive and replayable exchange
of sample data.

## Proposal

The sample event format is very simple. It consists of a JSON block with a sample metadata and data.

JSON part is formatted as follows:

```json
{
    "type": "m.samples",
    "content": {
        "sample.type": "audio/pcm",
        "sample.rate": 44100,
        "sample.duration" : 123.4567, 
        "sample.length" : undefined,
        "sample.width" : undefined,
        "sample.depth" : undefined,
        "sample.encoding" : "encoding",
        "samples" : "whatever_samples"
    }
}
```

`sample.type` is a MIME type, `sample.rate` is the sample rate in Hertz, `sample.duration` is
the duration of this sample event in seconds, `sample.length`, `sample.width` and `sample.depth`
are integers for positional data if exists. For future binary formats such as CBOR as mentioned
in MSC3079, it is preferred to have a binary encoding that will allow the samples placed raw
into the event body.

When clients encounter multiple sample events from others, they shall align all the samples by timestamp
and add the required amount of additional latency required to keep the latency invariant true. The latency
build-up and drop should be as gradual as possible. Clients MUST NOT rescale any of the sample events to
compensate for latency. Playing a combination of sample events of same type from different senders
with different sample rates is ill-formed, while combination of multiple sample events of different type
with different sample rates is implementation defined.

## Potential issues

Mistimed sample events can cause a client to hang forever by locking out on that specific sample event.

## Alternatives

* Have signalling on Matrix and actual data separately, which unfortunately means the samples
and the metadata possibly having different latency.

* Have sample events with `m.samples` as a subtype of `m.room.message` rather than an event type of its
own right (After all, sample events will just be message events with special client handling).

## Security considerations

Ability to hijack sample streams to livelock by deliberately mis-timing sample events.

## Unstable prefix

Not implemented yet.
