# MSC4549: Audio metadata for `m.audio` events

Audio files commonly contain information that lets a music player identify and present a track, such as its
title, artist, album, and cover art. Matrix `m.audio` events currently have no interoperable place to carry
this information. As a result, clients cannot show the details accompanying an audio attachment within the
timeline.

This MSC adds optional audio metadata to the existing `info` object of an `m.audio` message event. It enables
the sending client to describe an attached track without requiring receiving clients to inspect or download the
media file.

## Proposal

This MSC adds an optional `audio_metadata` property to the existing `info` object of an
[`m.audio`](https://spec.matrix.org/v1.19/client-server-api/#maudio) message event.

### `audio_metadata`

`audio_metadata` is an object. All its properties are optional strings:

Name | Type | Description
--- | --- | ---
`title` | `string` | The title of the audio track or song.
`artist` | `string` | The artist or performer of the track.
`album` | `string` | The album to which the track belongs.
`cover_art` | `string` | A [BlurHash](https://blurha.sh/) approximating the track's cover art.

For example, an `m.audio` event may contain:

```json
{
    "content": {
        "body": "Moonwalker.flac",
        "info": {
            "duration": 180000,
            "mimetype": "audio/flac",
            "size": 4200000,
            "audio_metadata": {
                "title": "Moonwalker",
                "artist": "Jake Chudnow",
                "album": "The Moon",
                "cover_art": "LBEpAr~VM{x[004:oyM|9GM|xtIU"
            }
        },
        "msgtype": "m.audio",
        "url": "mxc://example.org/abc123"
    }
}
```

Sending clients MAY populate any subset of these fields when they have corresponding metadata for the audio
file. Receiving clients MAY use any metadata fields they support and ignore fields they do not use. In
particular, a client MAY use `cover_art` as the background of that message's audio player. It is not intended
to replace a cover-art image attachment or to require a client to display cover art.

The `cover_art` value, when present, MUST be a BlurHash. BlurHashes were chosen because they provide a small
approximation of cover art and many clients will already implement BlurHash support for
[MSC2448].
Clients which cannot decode a `cover_art` value, including an invalid value, SHOULD ignore it.

## Potential issues

The metadata is supplied by the sending client and may be inaccurate, incomplete, or unrelated to the attached
audio.

## Alternatives

### Put each field directly in `info`

The fields could be added directly to `info`. Grouping them in `audio_metadata` keeps audio-specific metadata
separate from the generic media properties already in `info`, avoids a collection of top-level fields, and leaves
room to extend the metadata object later.

### Attach an image as cover art

An `mxc://` URI for an image could provide full cover art, but would require clients to fetch and render another
piece of media. A BlurHash is deliberately small and is sufficient for the optional background treatment
described by this MSC.

### Use ThumbHash for `cover_art`

ThumbHash was considered as another compact image placeholder format. BlurHash is proposed because clients may
already support it through [MSC2448], reducing the implementation work needed to render the metadata.

## Security considerations

`audio_metadata`, including its BlurHash, is attacker-controlled event content. Clients decoding a BlurHash
SHOULD apply appropriate resource limits and ignore malformed values.

## Unstable prefix

Before this MSC is accepted and incorporated into the specification, implementations SHOULD use
`org.matrix.msc4549.audio_metadata` in place of `audio_metadata` inside an `m.audio` event's `info` object.
The development property has the same structure as `audio_metadata`.

## Dependencies

None.
