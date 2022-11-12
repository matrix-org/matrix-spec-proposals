# MSC3245: Voice messages (using extensible events)

Voice messages are a useful way to quickly send a message to someone without having to use the more
awkward keyboard. Typically short in length, voice messages can be sent as annotated audio files
to recipients.

More information about voice messages and what they can be used for can be found on
[MSC2516 - Voice messages via msgtype](https://github.com/matrix-org/matrix-doc/pull/2516). This
MSC inherits a lot of the beliefs and usecases of that MSC, but instead packages the event contents
a bit differently. Specifically, this makes use of [MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767).

This MSC additionally relies upon [MSC0001](https://github.com/matrix-org/matrix-doc/pull/0001) and
[MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551).

## Proposal

Much like MSC2516, voice messages are defined as OGG files, encoded with Opus, using relatively sane
settings for voice recordings. This proposal does not define specific settings for clients to use,
but does strongly recommend reducing file size without losing audio quality as much as possible. Some
suggested default settings are:

* Sample rate: 48kHz
* Bitrate: 24kbps
* Mono (single channel)
* Appropriate complexity and resample quality for the platform.
* Encoder application: 2048 (voice, default is typically 2049 as audio). This doesn't have any signficant
  impact on the resulting recording.

We use Opus to be compatible with other messaging platforms, particularly the ones that can be bridged
easily to Matrix. This proposal aims to avoid having bridges (and to a degree, clients) transcode
voice messages as that would likely push voice messages further away from the "faster communication"
use case. Bridges are already needing to do processing on the events and can see seconds worth of latency:
an extra couple seconds to re-encode a voice message would not be helping that.

No maximum duration is specified, however clients are encouraged not to send long-running recordings
as they might be rejected/ignored on the receiving end for file size reasons. Typically, this should
be less than 5 minutes worth of audio.

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new `m.voice` event
type is introduced.

An example is:

```json5
{
  "type": "m.voice",
  "content": {
    "m.markup": [
      // Format of the fallback is not defined, but should have enough information for a text-only
      // client to do something with the voice message, just like with plain file uploads.
      //
      // Another option might be to include speech-to-text conversion here, so text-only clients can
      // "see" the contents without having to download them.
      {"body": "Voice Message (8 KB, 1:30) https://example.org/_matrix/media/v3/download/example.org/abcd1234"}
    ],
    "m.file": {
      "mimetype": "audio/ogg",
      "url": "mxc://example.org/abcdef",
      "name": "Voice message.ogg",
      "size": 7992
    },
    "m.audio_details": {
      "duration": 90,
      "waveform": [0, 256, /*...*/ 1024] // https://github.com/matrix-org/matrix-doc/pull/3246
    }
  }
}
```

No new content blocks are introduced in this MSC.

Together with content blocks from other proposals, an `m.voice` is described as:

* **Required** - An `m.markup` block to act as a fallback for clients which can't process voice messages.
* **Required** - An `m.file` block to contain the audio itself. Clients use this to represent the voice
  message. Per above, it MUST be in the file format described by this MSC.
* **Required** - An `m.audio_details` block to describe any audio-specific metadata, such as duration.
  * Under this MSC, the `waveform` is required in this usage. `duration` is already required.

The above describes the minimum requirements for sending an `m.voice` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand voice messages should not
honour them.

Note that `m.file` supports encryption and therefore it's possible to encrypt audio too.

If a client does not support rendering voice messages inline, the client would instead typically represent
the event as a regular audio file, then plain file upload, and finally plain text message.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable
and intentional for fallback considerations.

## Alternatives

As mentioned, [MSC2516](https://github.com/matrix-org/matrix-doc/pull/2516) exists to make voice messages a
dedicated `msgtype`, which would work in the near term. There's additionally discussion on that MSC on whether
or not a flag within the event would be more appropriate than a `msgtype`. This proposal believes that both a
`msgtype` and flag within the `content` would accomplish the same thing as this MSC, however that the fallback
scenarios are less desirable. Flags in the `content` are subject to extensive proliferation if accepted, making
it harder to migrate to event formats like Extensible Events. Dedicated message types have the issue of not all
clients handling unknown message types the same way. Some clients would render it as a plain file upload while
many others would simply ignore the message entirely. This is not great representation for an audio message.
This proposal counters both problems by using Extensible Events out of the box, which results in clients being
able to render whatever they can, which will typically be either the voice message or an audio event, and fall
back accordingly to the not-great representations if they need to.

## Security considerations

Voice messages by nature are human voices being sent over the internet. This can be used for malicious purposes
outside the control of Matrix: users are cautioned to not send voice messages to untrusted places, such as large
public rooms or unknown individuals.

As with all media events, clients should be wary that the contained file is actually an audio file. Playing JPEGs
or executables over the user's speakers are unlikely to go very well.

Voice messages are likely best used in encrypted rooms due to the high likelihood that the members of the room are
trusted, and the user's voice is not uploaded plainly to the media repo. Typically, this will be DMs or other
forms of private chats in most clients.

## Unstable prefix

While this MSC is not considerede stable, implementations should use `org.matrix.msc3245.voice.v2` in place
of the `m.voice` event type, additionally using any applicable prefixes for content blocks and similar.

As this is a new event type and clients would not be massively impacted by seeing the event, clients are
specifically permitted to send this event type into rooms which *don't* support extensible events: clients
which understand voice messages should be parsing the event as such, and clients which understand extensible
events but not voice messages should *not* attempt to represent the event (unless it's in an applicable room
version).

**Note**: We use a "v2" event here because a prior draft of this MSC was implemented in the wild. The MSC's
version history represents that possible schema, which used `m.room.message` and an older version of extensible
events instead. This version of the proposal does not describe that schema.

## Dependent MSCs

This MSC requires [MSC1767 - Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767) in order
to make the most sense in the specification.
