# MSC4269: Unambiguous mentions in body

The use of display names makes it difficult to parse user mentions from a message body. Clients can
also make it difficult to type user IDs without having them replaced with a mention.

Some clients, such as bots, have no use for or do not want to deal with the complexity of parsing
the pseudo-HTML of the `formatted_body`. In addition, the `m.mentions` added by [MSC3952] is not
enough, either, as the listed user IDs lack the context of the message body.

Translating the display names in the message body back to user IDs is difficult, if not impossible.
However, the reverse operation - translating unambiguous user IDs in the body into display names -
is trivial in comparison.

Thus it is proposed that the message `body` should contain user IDs instead of display names. 

## Proposal

The specified client behavior for user and room mentions is modified so that the event's `body`
should contain the unambiguous user ID, canonical room alias or room ID instead of the anchor's
text component.

## Potential issues

Some clients, especially bridges, might rely on the body containing the display name for a good user
experience. However, it would not be difficult to modify such a client to translate user IDs in the
message body to display names.

## Alternatives

- Change the spec so that the anchor's text component is the user ID. It would make user mentions
  more consistent with room mentions. This changes the `formatted_body` as well, potentially
  requiring more changes to clients.

- Specify the use of markdown links in the `body` matching the anchors in the `formatted_body`.
  While easier to parse, it's not as simple as just the user ID.

- Bracket display names in the `body` somehow, making it possible to look them up, perhaps with the
  help of `m.mentions`. However, they remain ambiguous.

## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.

[MSC3952]: https://github.com/matrix-org/matrix-spec-proposals/pull/3952
