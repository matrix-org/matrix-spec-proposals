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

`audio_metadata` is an object. All its properties are optional:

Name | Type | Description
--- | --- | ---
`title` | `string` | The title of the audio track or song.
`artist` | `string` | The artist or performer of the track.
`album` | `string` | The album to which the track belongs.
`cover_art` | `string` | An `mxc://` URI for the track's cover art image. Only present if the cover art is unencrypted.
`cover_art_file` | [`EncryptedFile`](https://spec.matrix.org/v1.19/client-server-api/#definition-encryptedfile) | Information on the encrypted cover art image. Only present if the cover art is encrypted.
`cover_art_info` | [`ThumbnailInfo`](https://spec.matrix.org/v1.19/client-server-api/#definition-thumbnailinfo) | Metadata about the cover art image referred to in `cover_art` or `cover_art_file`.
`cover_art_blurhash` | `string` | A [BlurHash](https://blurha.sh/) approximating the track's cover art.

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
                "cover_art": "mxc://example.org/def456",
                "cover_art_info": {
                    "h": 600,
                    "w": 600,
                    "mimetype": "image/jpeg",
                    "size": 48000
                },
                "cover_art_blurhash": "LBEpAr~VM{x[004:oyM|9GM|xtIU"
            }
        },
        "msgtype": "m.audio",
        "url": "mxc://example.org/abc123"
    }
}
```

Sending clients MAY populate any subset of these fields when they have corresponding metadata for the audio
file. Receiving clients MAY use any metadata fields they support however they like, and ignore fields they do
not use. For example, a client might display the cover art image alongside that message's audio player, or use
`cover_art_blurhash` as the player's background or as a placeholder while the image loads. None of these fields
require a client to display cover art.

The `cover_art` value, when present, MUST be an `mxc://` URI. When the audio file is encrypted, and so is
described by `file` rather than `url`, the cover art image MUST also be encrypted using the existing
[encrypted attachment](https://spec.matrix.org/v1.19/client-server-api/#sending-encrypted-attachments) format
and described by `cover_art_file` in place of `cover_art`. A sending client MUST NOT include both `cover_art`
and `cover_art_file`. Receiving clients which cannot download, decrypt, or render the cover art image SHOULD
ignore `cover_art` and `cover_art_file`.

The server cannot thumbnail encrypted media, so a receiving client must fetch the whole file to display
`cover_art_file`. Sending clients therefore may wish to downscale or compress the cover art before uploading it.

The `cover_art_blurhash` value, when present, MUST be a BlurHash. BlurHashes were chosen because they provide a
small approximation of cover art and many clients will already implement BlurHash support for [MSC2448].
Clients which cannot decode a `cover_art_blurhash` value, including an invalid value, SHOULD ignore it.

Sending clients which include `cover_art` or `cover_art_file` SHOULD also include `cover_art_info` and the
corresponding `cover_art_blurhash`. `cover_art_info` lets receiving clients lay out the image and its placeholder,
and know the image's MIME type. It MUST NOT be present without `cover_art` or `cover_art_file`. Sending clients
MAY include `cover_art_blurhash` without `cover_art` or `cover_art_file`, as providing the cover art image
requires uploading an additional file, which may be undesirable.

## Potential issues

The metadata is supplied by the sending client and may be inaccurate, incomplete, or unrelated to the attached
audio.

## Alternatives

### Put each field directly in `info`

The fields could be added directly to `info`. Grouping them in `audio_metadata` keeps audio-specific metadata
separate from the generic media properties already in `info`, avoids a collection of top-level fields, and leaves
room to extend the metadata object later.

### Use ThumbHash for `cover_art_blurhash`

ThumbHash was considered as another compact image placeholder format. BlurHash is proposed because clients may
already support it through [MSC2448], reducing the implementation work needed to render the metadata.

## Security considerations

`audio_metadata`, including its BlurHash and cover art, is attacker-controlled event content. Clients
decoding a BlurHash SHOULD apply appropriate resource limits and ignore malformed values. Clients fetching
`cover_art` or `cover_art_file` SHOULD treat it like any other untrusted media, potentially including applying
size limits.

## Unstable prefix

Before this MSC is accepted and incorporated into the specification, implementations SHOULD use
`org.matrix.msc4549.audio_metadata` in place of `audio_metadata` inside an `m.audio` event's `info` object.
The development property has the same structure as `audio_metadata`.

## Dependencies

None.

  [MSC2448]: https://github.com/matrix-org/matrix-spec-proposals/pull/2448
