# MSC3286: Media spoilers

[MSC2010](2010-spoilers.md) created ways for clients to tag parts of messages as
spoilers, enabling receiving clients to hide spoilered content unless the user
explicitly chooses to view it. While that proposal only covered textual
spoilers, it is also often desirable to be able to mark images, videos, and
other media as spoilers, since many clients automatically display previews for
media that recipients might not want to see.

As with textual spoilers, there are a variety of reasons that one might want to
mark media as a spoiler, for example if it would spoil a story, or if some
recipients might find the content objectionable or disturbing. By marking such
media as a spoiler, clients can then take measures to require consent from the
user before displaying the content.

## Proposal

To support this, an optional `spoiler` property of type `string` is added to the
`info` dictionaries of `m.image`, `m.video`, `m.audio`, and `m.file` messages.
When present, it indicates that the given media has been tagged as a spoiler.

The value of `spoiler` represents a placeholder text that clients may display as
the reason for the spoiler. Providing a reason is optional, and one may indicate
the absence of a reason by setting `spoiler` to an empty string.

### Examples

Message content for an image with a spoiler reason:

```json
{
  "body": "screenshot.png",
  "info": {
    "mimetype": "image/png",
    "size": 123456,
    "spoiler": "Contains spoilers for chapter 6"
  },
  "msgtype": "m.image",
  "url": "mxc://example.org/abcdef"
}
```

Message content for a video without a spoiler reason:

```json
{
  "body": "recording.mp4",
  "info": {
    "mimetype": "video/mp4",
    "size": 123456,
    "spoiler": ""
  },
  "msgtype": "m.video",
  "url": "mxc://example.org/abcdef"
}
```

## Potential issues

None that the author is aware of.

## Alternatives

An alternative solution, which some people currently use, is to embed images
inline in `m.text` messages, and then tag it using the existing mechanism for
textual spoilers. However, this is a rather hacky workaround, as it does not
support other types of media, nor does it support encryption. It also loses the
semantics of standalone `m.image` events, which makes it difficult for clients
to render image spoilers differently from regular textual spoilers.

## Security considerations

None that the author is aware of.

## Unstable prefix

Clients wishing to experimentally implement this proposal may do so by replacing
the `spoiler` key in `m.image`, `m.video`, `m.audio`, and `m.file` messages with
`town.robin.msc3286.spoiler`.
