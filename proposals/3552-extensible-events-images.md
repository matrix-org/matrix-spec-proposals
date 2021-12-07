# MSC3552: Extensible Events - Images and Stickers

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for non-text messaging types. This MSC covers only images
and stickers.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way images
are represented should not block the overall schema from going through.

This MSC additionally relies upon [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551).

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, two new primary event types
are introduced to describe their related functionality: `m.image` and `m.sticker`.

`m.image` is simply an image upload, akin to the now-legacy
[`m.image` `msgtype` from `m.room.message`](https://spec.matrix.org/v1.1/client-server-api/#mimage).

An example is:

```json5
{
  "type": "m.image",
  "content": {
    "m.text": "Upload: matrix.png (12 KB)", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "matrix.png",
      "mimetype": "image/png",
      "size": 12345
    },
    "m.image": {
        "width": 640,
        "height": 480
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
        { "m.text": "matrix logo" },
        { "body": "<b>matrix</b> logo", "mimetype": "text/html" }
    ]
  }
}
```

Under the extensible events format, the `m.thumbnail` and `m.caption` arrays are ordered by most preferred
first. Any number of captions and thumbnails can be provided, however it's expected that most cases will
always have at most 1 or 2 representations.

Note that `m.thumbnail` and `m.caption` must always be an array, even if containing a single element. This
is to make parsing easier/more predictable on the client side.

The remainder of the fallback deliberately uses [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551)
and its inherited behaviour for textual fallback to represent the image upload.

Stickers are modified to match the `m.image` schema above, replacing the current primary type for
[`m.sticker`](https://spec.matrix.org/v1.1/client-server-api/#msticker):

```json5
{
  "type": "m.sticker",
  "content": {
    "m.text": "Happyface", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "happy_sticker.png",
      "mimetype": "image/png",
      "size": 12345
    },
    "m.image": {
        "width": 640,
        "height": 480
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
        { "m.text": "Happyface" }
    ]
  }
}
```

Note that there is no `m.sticker` event in the content: this is because the primary type accurately
describes the event and no further metadata is needed. In future, if the specification requires
sticker-specific metadata to be added (like which pack it came from), this would likely appear under
an `m.sticker` object in the event content.

Note that stickers, images, and thumbnails can all be encrypted using the same approach as `m.file`.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files, images, stickers and extensible events also
apply here.

## Transition

The same transition introduced by extensible events is also applied here:

```json5
{
  "type": "m.room.message",
  "content": {
    "body": "image.png",
    "msgtype": "m.image",
    "url": "mxc://example.org/9af6bae1ae9cacc93058ae386028c52f28e41d35",
    "info": {
      "mimetype": "image/png",
      "size": 2386,
      "w": 301,
      "h": 287,
      "thumbnail_url": "mxc://example.org/elsewhere",
      "thumbnail_info": {
          "size": 238,
          "mimetype": "image/jpeg",
          "w": 30,
          "h": 28
      }
    },

    // Extensible Events
    "m.text": "image.png", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/9af6bae1ae9cacc93058ae386028c52f28e41d35",
      "name": "image.png",
      "mimetype": "image/png",
      "size": 2386
    },
    "m.image": {
        "width": 301,
        "height": 287
    },
    "m.thumbnail": [
        {
            "url": "mxc://example.org/elsewhere",
            "mimetype": "image/jpeg",
            "size": 238,
            "width": 30,
            "height": 28
        },
        // ...
    ],
    "m.caption": [
        // array of m.message objects
        { "m.text": "Screenshot of something cool" }
    ]
  }
}
```

The event details are copied and quite verbose, however this is best to ensure compatibility with the
extensible events format.

For stickers, the same transition plan as `m.room.message` is taken into effect, though with the legacy
schema being deprecated rather than the whole event type. Similarly, the idea is to smash the two schemas
together much like images above.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Example:
```json5
{
  "type": "org.matrix.msc1767.image",
  "content": {
    "org.matrix.msc1767.text": "Happyface", // or other m.message-like event
    "org.matrix.msc1767.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "happy_sticker.png",
      "mimetype": "image/png",
      "size": 12345
    },
    "org.matrix.msc1767.image": {
        "width": 640,
        "height": 480
    },
    "org.matrix.msc1767.thumbnail": [
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
    "org.matrix.msc1767.caption": [
        // array of m.message objects
        { "org.matrix.msc1767.text": "Happyface" }
    ]
  }
}
```
