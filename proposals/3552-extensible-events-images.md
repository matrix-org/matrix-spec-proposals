# MSC3552: Extensible Events - Images and Stickers

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers only images
and stickers.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way images
are represented should not block the overall schema from going through.

This MSC additionally relies upon [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551).

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new event type
is introduced to describe applicable functionality: `m.image`. This event type is simply an image
upload, akin to the now-legacy [`m.image` `msgtype` from `m.room.message`](https://spec.matrix.org/v1.1/client-server-api/#mimage).

An example is:

```json5
{
  "type": "m.image",
  "content": {
    "m.text": [
      // Format of the fallback is not defined, but should have enough information for a text-only
      // client to do something with the image, just like with plain file uploads.
      {"body": "matrix.png (12 KB) https://example.org/_matrix/media/v3/download/example.org/abcd1234"}
    ],
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "matrix.png",
      "mimetype": "image/png",
      "size": 12345
    },
    "m.image_details": { // optional
      "width": 640,
      "height": 480
    },
    "m.thumbnail": [ // optional
      {
        // A thumbnail is an m.file+m.image, or a small image
        "m.file": {
          "url": "mxc://exmaple.org/efgh5678",
          "mimetype": "image/jpeg",
          "size": 123

          // "name" is optional in this scenario
        },
        "m.image_details": {
          "width": 160,
          "height": 120
        }
      },
      // ...
    ],
    "m.caption": { // optional - goes above/below image
      "m.text": [{"body": "Look at this cool Matrix logo"}]
    },
    "m.alt_text": { // optional - accessibility consideration for image
      "m.text": [{"body": "matrix logo"}]
    }
  }
}
```

With consideration for extensible events, the following content blocks are defined:

* `m.image_details` - Currently records width and height (both required, in pixels), but in
  future could additionally supply other image details such as colour space.
* `m.thumbnail` - An array of (usually) smaller images the client can use to show in place of
  the event's image for bandwidth or size considerations. Currently requires two other content
  blocks nested under it: `m.file` and `m.image_details`.
  * Clients should find the thumbnail most suitable for them - the array is not ordered, but
    encouraged to have smaller images (by byte size) first.
  * Multiple thumbnail formats may be supplied (webp, webm, jpeg, etc) with the same dimensions.
    Clients should ensure they are capable of rendering the type before picking that thumbnail.
  * `m.file`'s `mimetype` is a required field in this block.
  * `m.file`'s `name` is optional in this block.
* `m.alt_text` - Alternative text for the content, for accessibility considerations. Currently
  requires an `m.text` content block to be nested within it, however senders should only
  specify a plain text body for ease of parsing.
  * *Note*: We use the full capability of `m.text` here not for mimetype, but future support
    for translations and other text-based extensions.

Together with content blocks from other proposals, an `m.image` is described as:

* **Required** - An `m.text` block to act as a fallback for clients which can't process images.
* **Required** - An `m.file` block to contain the image itself. Clients use this to show the image.
* **Optional** - An `m.image_details` block to describe any image-specific metadata, such as dimensions.
  Like with existing `m.room.message` events today, clients should keep images within a set of
  reasonable bounds, regardless of sender-supplied values. For example, keeping images at a minimum
  size and within a maximum size.
* **Optional** - An `m.thumbnail` block (array) to describe any thumbnails for the image.
* **Optional** - An `m.caption` block to represent any text that should be shown above or below the
  image. Currently this MSC does not describe a way to pick whether the text goes above or below,
  leaving this as an implementation detail. A future MSC may investigate ways of representing this,
  if needed.
* **Optional** - An `m.alt_text` block to represent alternative/descriptive text for the image. This
  is used as an accessibility feature, and per the block's definition above should only contain a plain
  text representation at the moment. Clients are encouraged to assume there is no alt text if no plain
  text representations are present. For clarity, this value would be supplied to the `alt` attribute
  of an `img` node in HTML.

The above describes the minimum requirements for sending an `m.image` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand image events should not
honour them.

To represent stickers, we instead use a mixin on `m.image_details`. A new (optional) boolean field
called `m.sticker` is added if the client is intended to render the image as a sticker. When rendering
as a sticker, the `m.caption` can be shown as a tooltip (or similar) rather than inline with the image
itself. `m.sticker` defaults to `false`.

The [`m.sticker` event type](https://spec.matrix.org/v1.1/client-server-api/#msticker) is deprecated
and removed, like `m.room.message` in MSC1767.

Note that `m.file` supports encryption and therefore it's possible to encrypt thumbnails and images
too.

If a client does not support rendering images inline, the client would instead typically represent
the event as a plain file upload, then fall further back to a plain text message.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable
and intentional for fallback considerations.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files, images, stickers, and extensible events also
apply here. For example, bounds on image size, assuming sender-provided details about the file are
false, etc.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
