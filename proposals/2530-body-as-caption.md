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

This proposal allows the `filename` field from `m.file`, and the `format` and
`formatted_body` fields from `m.text` for all media msgtypes (`m.image`,
`m.audio`, `m.video`, `m.file`).

If the `filename` field is present in a media message, clients should treat
`body` as a caption instead of a file name. The `format`/`formatted_body`
fields should also be supported and work the same way as they do in `m.text`
messages.

The current spec is somewhat ambiguous as to how `body` should be handled and
the definition varies across different message types. In practice, clients
(or at least Element) use it as the file name. As a part of adding captions,
the `body` field for all message types is explicitly defined to be used as the
file name when the `filename` field is not present.

For `m.file` messages, the current spec confusingly defines both `filename` and
`body` as the file name. In order to avoid (old) messages with both fields from
being misinterpreted as having captions, the `body` field should not be used as
a caption when it's equal to `filename`.

## Potential issues

In clients that don't show the file name anywhere, the caption would not be
visible at all. However, extensible events would run into the same issue.
Clients having captions implemented beforehand may even help eventually
implementing extensible events.

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
