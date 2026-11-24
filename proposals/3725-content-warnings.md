# MSC3725: Content warnings

[MSC2010](2010-spoilers.md) made it possible to tag parts of messages as
spoilers, so that receiving clients can hide content that the user might not
want to see. However, the latter proposal only works with textual messages,
which are just one of the many event types that might require some kind of
content warning (images, videos, files, etc.). This MSC proposes a more general
content warning system to fill that gap, using
[Extensible Events](https://github.com/matrix-org/matrix-doc/pull/1767) to
encompass all possible event types.

As with textual spoilers, there are a variety of reasons that an event might
warrant a content warning, for example if it could spoil a story, or if some
recipients might find the content objectionable or disturbing. By providing a
content warning, clients can then take measures to require consent from the user
before displaying the content.

## Proposal

Content warnings are represented by a new event content type
`m.content_warning`, which looks like this:

```json
{
  "type": "m.image",
  "content": {
    "m.text": "Upload: screenshot.png (300 KB)",
    "m.file": {
      "url": "mxc://example.org/abcdef",
      "name": "screenshot.png",
      "mimetype": "image/png",
      "size": 300000
    },
    "m.image": {
      "width": 640,
      "height": 480
    },
    "m.content_warning": {
      "type": "m.spoiler",
      "description": "Contains spoilers for chapter 6"
    }
  }
}
```

The `type` field is optional, and represents the general, machine-readable
reason for the content warning. The following types are provided:

- `m.spoiler` for spoilers
- `m.nsfw` for NSFW content
- `m.graphic` for graphic or disturbing content
- `m.medical` for e.g. epilepsy warnings

The `description` field is also optional, and represents a more specific,
human-readable description of the content warning.

## Potential issues

A result of this proposal is that textual `m.message`s now have two different
ways to do spoilers: the `data-mx-spoiler` attribute, and the
`m.content_warning` event type. While this may seem a bit redundant, the two
methods are necessarily complementary, since the `data-mx-spoiler` attribute
provides finer-grained control over which parts of a message are hidden, while
the `m.content_warning` event type sits above it at the event level.

## Alternatives

In the case of images, an alternative solution, which some people currently use,
is to embed images inline in `m.text` messages, and then tag it using the
existing mechanism for textual spoilers. This is a pretty hacky workaround,
since it does not support other types of media, nor does it support encryption.
It also loses the semantics of standalone `m.image` events, which makes it
difficult for clients to render image spoilers differently from regular textual
spoilers.

## Security considerations

None that the author is aware of.

## Unstable prefix

Clients wishing to experimentally implement this proposal may do so by replacing
the `m.content_warning` event type with `town.robin.msc3725.content_warning`,
and replacing the content warning types `m.spoiler`, `m.nsfw`, `m.graphic`, and
`m.medical` with `town.robin.msc3725.spoiler`, `town.robin.msc3725.nsfw`,
`town.robin.msc3725.graphic`, and `town.robin.msc3725.medical` respectively.
