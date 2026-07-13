# MSC4274: Inline media galleries via msgtypes

Matrix allows sharing individual media files such as images or videos via
dedicated [`m.room.message` msgtypes]. This is, however, not practical for
sharing larger collections of files. For one thing, there is no mechanism to set
a joint caption for several media files. For another, there is no way to inform
other clients that a set of pictures belongs together and should be grouped
accordingly in the timeline. These shortcomings call for a built-in media
gallery feature as it is widely known from other messaging apps.

This proposal defines a compact and pragmatic variant of sharing media galleries
in a single event.

## Proposal

A new `msgtype` of `m.gallery` is introduced with the following properties in
`content`:

- `body` (string): The caption of the gallery.
- `format` (string): The format used in `formatted_body`. Currently only
  `org.matrix.custom.html` is supported.
- `formatted_body` (string): The formatted version of the body. Required if
  `format` is specified.
- `itemtypes` (array): Ordered array of metadata for each item in the gallery.

The objects in the `itemtypes` array have the same schema as the `content` of
the msgtypes `m.image`, `m.video`, `m.audio` and `m.file`. Rather than
`msgtype`, they use `itemtype` though.

``` json5
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.gallery",
    "body": "Checkout my photos from [FOSDEM 2025](https://fosdem.org/2025/)",
    "format": "org.matrix.custom.html",
    "formatted_body": "Checkout my photos from <a href=\"https://fosdem.org/2025/\">FOSDEM 2025</a>",
    "itemtypes": [{
      "itemtype": "m.image",
      "body": "filename.jpg",
      "info": {
        "h": 398,
        "mimetype": "image/jpeg",
        "size": 31037,
        "w": 394
      },
      "url": "mxc://example.org/JWEIFJgwEIhweiWJE",
      ...
    }, ...]
  },
  ...
}
```

## Potential issues

The size of galleries under this proposal is limited by the event size limit
(65,536 bytes). An encrypted gallery event with a single image, including
thumbnail, and no caption measures about 2,000 bytes. Each additional image adds
roughly another 1,000 bytes. Therefore galleries would be capped to about 60
images. While this is a limitation, the amount seems practical for most use
cases.

Additionally, this proposal doesn't prescribe a fallback mechanism for clients
that don't support `m.gallery` msgtypes. Clients that care about backwards
compatibility could encode media links or a generic fallback text into `body` or
`formatted_body`, respectively. It is unclear, however, if a fallback is
actually desirable or not because unwrapping 60 images into somebody else's
timeline might be considered inappropriate if not spammy.

## Alternatives

This proposal is similar to the seemingly abandoned [MSC3382]. The latter
conflates galleries into `m.text` (or even arbitrary) msgtypes and reuses
`msgtype` inside the items which creates a circular dependency. These issues are
solved in the present proposal.

Rather than adding a new `msgtype`, galleries could be expressed via extensible
events by reusing parts of [MSC1767] and related proposals. This would only take
effect in a future room version, however, and can be covered in a separate MSC.

Another alternative is to define galleries as chains of related events as in
[MSC2881]. Compared to the inline approach taken in this proposal, this has
better fallback support, is more flexible and less prone to event size limits.
At the same time, it is significantly more complex to implement in terms of
replies, edits, redactions, forwarding, etc.

Finally, rather than defining galleries on the sender's side, receiving clients
could opportunistically group consecutive images in the timeline into galleries.
This might need specific rules such as grouping by sender or time windowing.
Different clients might prefer very different display rules, however. Therefore,
it seems more practical that the spec annotates galleries clearly while leaving
their UI treatment to clients themselves.

## Security considerations

None.

## Unstable prefix

Until this proposal is accepted into the spec, implementations SHOULD refer to
`m.gallery` as `dm.filament.gallery`.

## Dependencies

None.

  [`m.room.message` msgtypes]: https://spec.matrix.org/v1.13/client-server-api/#mroommessage-msgtypes
  [MSC3382]: https://github.com/matrix-org/matrix-spec-proposals/pull/3382
  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [MSC2881]: https://github.com/matrix-org/matrix-spec-proposals/pull/2881
