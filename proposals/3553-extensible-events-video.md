# MSC3553: Extensible Events - Videos

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers only videos.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way videos
are represented should not block the overall schema from going through.

This MSC additionally relies upon [MSC3551](https://github.com/matrix-org/matrix-doc/pull/3551) and
[MSC3552](https://github.com/matrix-org/matrix-doc/pull/3552).

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new `m.video` event
type is introduced to replace the [`m.video` `msgtype`](https://spec.matrix.org/v1.1/client-server-api/#mvideo).

An example is:

```json5
{
  "type": "m.video",
  "content": {
    "m.text": [
      // Format of the fallback is not defined, but should have enough information for a text-only
      // client to do something with the video, just like with plain file uploads.
      {"body": "matrix.mp4 (12 KB, 1:30) https://example.org/_matrix/media/v3/download/example.org/abcd1234"}
    ],
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "matrix.mp4",
      "mimetype": "video/mp4",
      "size": 12345
    },
    "m.video_details": { // optional
      "width": 640,
      "height": 480,
      "duration": 90
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
    "m.caption": { // optional - goes above/below video
      "m.text": [{"body": "Look at this cool animated Matrix logo"}]
    }
  }
}
```

The newly introduced blocks are:

* `m.video_details` - Similar to `m.image_details` from MSC3552, optional information about the video.
  `width` and `height` are required, while `duration` (length in seconds of the video) is optional.

Together with content blocks from other proposals, an `m.video` is described as:

* **Required** - An `m.text` block to act as a fallback for clients which can't process videos.
* **Required** - An `m.file` block to contain the video itself. Clients use this to show the video.
* **Optional** - An `m.video_details` block to describe any video-specific metadata, such as dimensions.
  Like with existing `m.room.message` events today, clients should keep videos within a set of
  reasonable bounds, regardless of sender-supplied values. For example, keeping videos at a minimum
  size and within a maximum size.
* **Optional** - An `m.thumbnail` block (array) to describe "poster images" for the video.
* **Optional** - An `m.caption` block to represent any text that should be shown above or below the
  video. Currently this MSC does not describe a way to pick whether the text goes above or below,
  leaving this as an implementation detail. A future MSC may investigate ways of representing this,
  if needed.

The above describes the minimum requirements for sending an `m.video` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand video events should not
honour them. Such examples might include an `m.audio` block for "audio-only" mode (podcasts, etc) or
an `m.image` to represent the video as a GIF (or similar).

Note that `m.file` supports encryption and therefore it's possible to encrypt thumbnails and videos
too.

If a client does not support rendering videos inline, the client would instead typically represent
the event as a plain file upload, then fall further back to a plain text message. An image fallback
is not necessarily possible, despite all the required blocks being possible. This is due to the file
having a video mimetype, hopefully indicating to the client that an `<img />` (or similar) is not
appropriate for this event.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable
and intentional for fallback considerations.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files, videos, and extensible events also
apply here. For example, bounds on video size, assuming sender-provided details about the file are
false, etc.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
