# MSC0000: Voice messages (using extensible events)

Voice messages are a useful way to quickly send a message to someone without having to use the more
awkward keyboard. Typically short in length, voice messages can be sent as annotated audio files
to recipients.

More information about voice messages and what they can be used for can be found on
[MSC2516 - Voice messages via msgtype](https://github.com/matrix-org/matrix-doc/pull/2516). This
MSC inherits a lot of the beliefs and usecases of that MSC, but instead packages the event contents
a bit differently. Specifically, this makes use of 
[MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767).

## Proposal

Much like MSC2516, voice messages are defined as OGG files, encoded with Opus, using relatively sane
settings for voice recordings. This proposal does not define specific settings for clients to use,
but does define a minimum compatibility for clients to respect (clients are able to support other
formats, but must support sending/receiving Opus at least).

We use Opus to be compatible with other messaging platforms, particularly the ones that can be bridged
easily to Matrix. This proposal aims to avoid having bridges (and to a degree, clients) transcode
voice messages, potentially decreasing the ability for them to be used as a faster method of communication.

No maximum duration is specified, however clients are encouraged not to send long-running recordings
as they might be rejected/ignored on the receiving end for file size reasons. Typically, this should
be less than 5 minutes worth of audio.

MSC1767 is used to package the voice message up in an annotated event format. Readers of this proposal
are encouraged to [read the MSC](https://github.com/matrix-org/matrix-doc/pull/1767) prior to commenting
or parsing this MSC's use of Extensible Events.

An example voice message would be:

```json5
{
  "type": "m.audio",
  "content": {
    // TODO: @@TR
  },
  // other fields required by the spec, but not important here
}
```

// TODO: Explain why

## Potential issues

TBD

## Alternatives

TBD

## Security considerations

TBD

## Unstable prefix

TBD
