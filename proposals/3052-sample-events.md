# MSC3052: Sample events

Sample events are intended as a generic representation of timing-sensitive and replayable exchange
of sample data.

## Proposal

The sample event format is very simple. It consists of a JSON chunk stating the metadata such as sample
rate, sequence number and sample count, followed by a blob of actual samples.

JSON part is formatted as follows:

```json
{
    "type": "m.samples",
    "content": {
        "sample_type": "audio/pcm",
        "sample_rate": 44100,
        "sample_duration" : 123.4567, 
        "sample_length" : undefined,
        "sample_width" : undefined,
        "sample_depth" : undefined
    }
}
```

`sample_type` is a MIME type, `sample_rate` is the sample rate in Hertz, `sample_duration` is
the duration of this sample event in seconds, `sample_length`, `sample_width` and `sample_depth`
are integers for positional data if exists.

When clients encounter multiple sample events from others, they shall align all the samples by timestamp
and add the required amount of additional latency required to keep the latency invariant true. The latency
build-up and drop should be as gradual as possible. Clients MUST NOT re-time any of the sample events.
Playing a combination of sample events from different senders with different

## Potential issues

Mistimed sample events can cause a client to hang forever by locking out on that specific sample event.

## Alternatives

Having signalling on Matrix and actual data separately, which unfortunately means the samples
and the metadata possibly having different latency.

## Security considerations

Ability to hijack sample streams to livelock by deliberately mis-timing sample events.

## Unstable prefix

Not implemented yet.
