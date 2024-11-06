# MSC3246: Audio waveforms (extensible events)

Some audio events might wish to have a waveform to represent a "thumbnail" of the audio clip the user
is about to receive. Most applicable to voice messages (like [MSC3245](https://github.com/matrix-org/matrix-doc/pull/3245)),
this proposal introduces a definition for the waveform in a larger [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)
(Extensible Events) context.

This MSC additionally relies upon [MSC3927](https://github.com/matrix-org/matrix-doc/pull/3927).

## Proposal

Under the `m.audio_details` content block, a new optional field named `waveform` is added. It is
an array of (non-floating) numbers to represent the amplitude of the audio over time. Because
floating point numbers are not allowed in Matrix events, integers should be between 0 and 256,
inclusive. Though there is no limit to the number of entries in the array, senders should aim to
have at least 30 and not more than 120.

## Potential issues

This extension can be difficult to rationalize outside the context of voice messages, potentially
making it unused by clients at render-time, or not populated due to effort by senders. MSCs which
need or want this functionality are encouraged to put hard blockers on this proposal.

## Alternatives

No applicable alternatives.

## Security considerations

Senders can specify too many or too few elements in the waveform, or the waveform could be a false
representation of the audio - receiving clients are encouraged to adjust the array size to fit their
purposes (downsample/upsample), and to not trust that the waveform is accurate. Once the audio file
has been downloaded, the client should generate its own waveform to replace the "thumbnail".

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3246.waveform`
instead of `waveform` when sending events.

Note that extensible events should only be used in an appropriate room version as well.

Implementations should note that this MSC previously had a range of 0-1024, inclusive. This was
changed to 256.
