# Body field as media caption

When sending images or other attachments, users often want to include text to
convey additional information. Most chat platforms offer media captions as a
first-class feature, allowing users to choose the attachment and write text,
then send both together in one message.

Matrix currently does not enable this on the protocol level: at best, clients
can emulate the behavior by sending two messages quickly; at worst, the user
has to do that manually. Sending separate messages means it's possible for
the second message to be delayed or lost if something goes wrong.

## Proposal

This proposal allows the `filename` field from [`m.file`], and the `format` and
`formatted_body` fields from [`m.text`] for all media msgtypes (`m.image`,
`m.audio`, `m.video`, `m.file`). This proposal does not affect the `m.location`
msgtype, nor the separate `m.sticker` event type: stickers already use `body`
as a description, and locations don't have file names.

If the `filename` field is present in a media message, clients should treat
`body` as a caption instead of a file name. If the `format`/`formatted_body`
fields are present in addition to `filename` and `body`, then they should take
priority as the caption text. Formatted text in media captions is rendered the
same way as formatted text in `m.text` messages.

The current spec is somewhat ambiguous as to how `body` should be handled and
the definition varies across different message types. The current spec for
[`m.image`] describes `body` as

> A textual representation of the image. This could be the alt text of the
> image, the filename of the image, or some kind of content description for
> accessibility e.g. ‘image attachment’.

while [`m.audio`] describes it as

> A description of the audio e.g. ‘Bee Gees - Stayin’ Alive’, or some kind of
> content description for accessibility e.g. ‘audio attachment’.

In practice, clients (or at least Element) use it as the file name. As a part
of adding captions, the `body` field for all media message types is explicitly
defined to be used as the file name when the `filename` field is not present.

For `m.file` messages, the [current (v1.9) spec][`m.file`] confusingly defines
`filename` as "The original filename of the uploaded file" and simultaneously
recommends that `body` is "the filename of the original upload", effectively
saying both fields should have the file name. In order to avoid (old) messages
with both fields being misinterpreted as having captions, the `body` field
should not be used as a caption when it's equal to `filename`.

[`m.file`]: https://spec.matrix.org/v1.9/client-server-api/#mfile
[`m.text`]: https://spec.matrix.org/v1.9/client-server-api/#mtext
[`m.image`]: https://spec.matrix.org/v1.9/client-server-api/#mimage
[`m.audio`]: https://spec.matrix.org/v1.9/client-server-api/#maudio

### Examples
<details>
<summary>Image with caption</summary>

```json
{
    "msgtype": "m.image",
    "url": "mxc://maunium.net/HaIrXlnKfEEHvMNKzuExiYlv",
    "filename": "cat.jpeg",
    "body": "this is a cat picture :3",
    "info": {
        "w": 479,
        "h": 640,
        "mimetype": "image/jpeg",
        "size": 27253
    },
    "m.mentions": {}
}
```

</details>
<details>
<summary>File with formatted caption</summary>

```json
{
    "msgtype": "m.file",
    "url": "mxc://maunium.net/TizWsLhHfDCETKRXdDwHoAGn",
    "filename": "hello.txt",
    "body": "this caption is longer than the file itself 🤔",
    "format": "org.matrix.custom.html",
    "formatted_body": "this <strong>caption</strong> is longer than the file itself 🤔",
    "info": {
        "mimetype": "text/plain",
        "size": 14
    },
    "m.mentions": {}
}
```

</details>

### Summary
* `filename` is defined for all media msgtypes.
* `body` is defined to be a caption when `filename` is present and not equal to `body`.
  * `format` and `formatted_body` are allowed as well for formatted captions.
* `body` is defined to be the file name when `filename` is not present.

## Potential issues

In clients that don't show the file name anywhere, the caption would not be
visible at all. However, extensible events would run into the same issue.
Clients having captions implemented beforehand may even help eventually
implementing extensible events.

Old clients may default to using the caption as the file name when the user
wants to download a file, which will be somewhat weird UX.

## Alternatives

### [MSC2529](https://github.com/matrix-org/matrix-spec-proposals/pull/2529)

MSC2529 would allow existing clients to render captions without any changes,
but the use of relations makes implementation more difficult, especially for
bridges. It would require either waiting a predefined amount of time for the
caption to come through, or editing the message on the target platform (if
edits are supported).

The format proposed by MSC2529 would also make it technically possible to use
other message types as captions without changing the format of the events,
which is not possible with this proposal.

### Extensible events

Like MSC2529, this would be obsoleted by [extensible events](https://github.com/matrix-org/matrix-spec-proposals/pull/3552).
However, fully switching to extensible events requires significantly more
implementation work, and it may take years for the necessary time to be
allocated for that.

## Security considerations

This proposal doesn't involve any security-sensitive components.

## Unstable prefix

The fields being added already exist in other msgtypes, so unstable prefixes
don't seem necessary. Additionally, using `body` as a caption could already be
considered spec-compliant due to the ambiguous definition of the field, and
only adding unstable prefixes for the other fields would be silly.
