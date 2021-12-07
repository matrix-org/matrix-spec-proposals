# MSC3553: Extensible Events - Videos

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for non-text messaging types. This MSC covers only videos.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way images
are represented should not block the overall schema from going through.

This MSC additionally relies upon [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551) and
parts of [MSC3552](https://github.com/matrix-org/matrix-doc/pull/3552) for thumbnails.

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new `m.video` primary
event type is introduced to replace the [`m.video` `msgtype`](https://spec.matrix.org/v1.1/client-server-api/#mvideo).

An example is:

```json5
{
  "type": "m.video",
  "content": {
    "m.text": "Upload: matrix.mp4 (12 KB)", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "matrix.mp4",
      "mimetype": "video/mp4",
      "size": 12345
    },
    "m.thumbnail": [
        {
            // an inline m.file, minus `name`
            "url": "mxc://example.org/efgh5678",
            "mimetype": "image/jpeg",
            "size": 123,

            // an inline m.image
            "width": 160,
            "height": 120
        },
        // ...
    ],
    "m.caption": [
        // array of m.message objects
        { "m.text": "matrix demo" },
        { "body": "<b>matrix</b> demo", "mimetype": "text/html" }
    ],
    "m.video": {
      "width": 1280,
      "height": 720,
      "duration": 90000 // milliseconds
    }
  }
}
```

All details shown above except `m.video` in the content are inherited from [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551) and [MSC3552](https://github.com/matrix-org/matrix-doc/pull/3552).

`m.video` is simply a container for the video-specific metadata that is not already covered by other MSCs.
Note that the event does not have an `m.image` - clients should use the first image-like thumbnail as a poster
for the video. It is reasonable for a client to include a lower quality copy (eg: 480p) as a thumbnail in the
event.

Note that videos can be encrypted using the same approach as `m.file`.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files, videos, and extensible events also apply here.

## Transition

The same transition introduced by extensible events is also applied here:

```json5
{
  "type": "m.room.message",
  "content": {
    "body": "matrix.mp4",
    "msgtype": "m.video",
    "url": "mxc://example.org/9af6bae1ae9cacc93058ae386028c52f28e41d35",
    "info": {
      "duration": 90000,
      "mimetype": "video/mp4",
      "size": 12345,
      "w": 1280,
      "h": 720,
      "thumbnail_url": "mxc://example.org/elsewhere",
      "thumbnail_info": {
          "size": 123,
          "mimetype": "image/jpeg",
          "w": 160,
          "h": 120
      }
    },

    // Extensible Events
    "m.text": "matrix.mp4", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/9af6bae1ae9cacc93058ae386028c52f28e41d35",
      "name": "matrix.mp4",
      "mimetype": "video/mp4",
      "size": 12345
    },
    "m.thumbnail": [
        {
            // an inline m.file, minus `name`
            "url": "mxc://example.org/elsewhere",
            "mimetype": "image/jpeg",
            "size": 123,

            // an inline m.image
            "width": 160,
            "height": 120
        },
        // ...
    ],
    "m.caption": [
        // array of m.message objects
        { "m.text": "matrix demo" },
        { "body": "<b>matrix</b> demo", "mimetype": "text/html" }
    ],
    "m.video": {
      "width": 1280,
      "height": 720,
      "duration": 90000 // milliseconds
    }
  }
}
```

The event details are copied and quite verbose, however this is best to ensure compatibility with the
extensible events format.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Example:
```json5
{
  "type": "org.matrix.msc1767.video",
  "content": {
    "org.matrix.msc1767.text": "matrix.mp4", // or other m.message-like event
    "org.matrix.msc1767.file": {
      "url": "mxc://example.org/9af6bae1ae9cacc93058ae386028c52f28e41d35",
      "name": "matrix.mp4",
      "mimetype": "video/mp4",
      "size": 12345
    },
    "org.matrix.msc1767.thumbnail": [
        {
            // an inline m.file, minus `name`
            "url": "mxc://example.org/elsewhere",
            "mimetype": "image/jpeg",
            "size": 123,

            // an inline m.image
            "width": 160,
            "height": 120
        },
        // ...
    ],
    "org.matrix.msc1767.caption": [
        // array of m.message objects
        { "m.text": "matrix demo" },
        { "body": "<b>matrix</b> demo", "mimetype": "text/html" }
    ],
    "org.matrix.msc1767.video": {
      "width": 1280,
      "height": 720,
      "duration": 90000 // milliseconds
    }
  }
}
```
