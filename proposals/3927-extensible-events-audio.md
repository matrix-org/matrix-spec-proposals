# MSC3927: Extensible Events - Audio

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers only audio.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way audio files
are represented should not block the overall schema from going through.

This MSC additionally relies upon [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551).

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new event type
is introduced to describe applicable functionality: `m.audio`. This event type is simply an audio
upload, akin to the now-legacy [`m.audio` `msgtype` from `m.room.message`](https://spec.matrix.org/v1.1/client-server-api/#mimage).
Note that this MSC is specifically scoped to handling audio files and not audio-related features
like voice messages, though such features might build upon this MSC.

An example is:

```json5
{
  "type": "m.audio",
  "content": {
    "m.text": [
      // Format of the fallback is not defined, but should have enough information for a text-only
      // client to do something with the audio, just like with plain file uploads.
      {"body": "matrix.mp3 (12 KB, 1:30) https://example.org/_matrix/media/v3/download/example.org/abcd1234"}
    ],
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "matrix.mp3",
      "mimetype": "audio/mp3",
      "size": 12345
    },
    "m.audio_details": { // optional
      "duration": 90
    },
    "m.caption": { // optional - goes above/below audio
      "m.text": [{"body": "Listen to the Matrix logo in all its glory"}]
    }
  }
}
```

With consideration for extensible events, the following content blocks are defined:

* `m.audio_details` - Currently records duration (in seconds, required) of the audio file.

Together with content blocks from other proposals, an `m.audio` is described as:

* **Required** - An `m.text` block to act as a fallback for clients which can't process audio files.
* **Required** - An `m.file` block to contain the audio itself. Clients use this to represent the audio.
* **Optional** - An `m.audio_details` block to describe any audio-specific metadata, such as duration.
* **Optional** - An `m.caption` block to represent any text that should be shown above or below the
  audio file. Currently this MSC does not describe a way to pick whether the text goes above or below,
  leaving this as an implementation detail. A future MSC may investigate ways of representing this,
  if needed.

The above describes the minimum requirements for sending an `m.audio` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand audio events should not
honour them.

Note that `m.file` supports encryption and therefore it's possible to encrypt audio too.

If a client does not support rendering audio inline, the client would instead typically represent
the event as a plain file upload, then fall further back to a plain text message.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable
and intentional for fallback considerations.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files, audio, and extensible events also
apply here. For example, assuming sender-provided details about the file are false, etc.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
