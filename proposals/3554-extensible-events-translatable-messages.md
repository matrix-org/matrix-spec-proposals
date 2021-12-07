# MSC3554: Extensible Events - Translatable Messages

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for non-text messaging types. This MSC covers only support
for translations on the `m.message` type.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way images
are represented should not block the overall schema from going through.

## Proposal

A new field is added to the `m.message` type definition to denote which language is being represented
by the `body`: `lang`.

An example:

```json5
{
    "type": "m.message",
    "content": {
        "m.message": [
            {
                "body": "Je suis un poisson",
                "lang": "fr"
            },
            {
                "body": "I am a fish",
                "lang": "en"
            }
        ]
    }
}
```

*Note*: `m.message`'s support for `mimetype` has been excluded from the example for brevity. It is still
supported in events.

As already covered by Extensible Events, the first element in the array would be the representation that
unaware clients would use, which in the example above would be French. Clients which are aware of language
support might end up picking the English version instead.

By default, messages are assumed to be sent in English (`en`).

`lang` must be a valid language code under [BCP-47](https://www.rfc-editor.org/rfc/bcp/bcp47.txt). This is
in line with the HTML specification which uses a similar attribute on the `<html>` node.

There is no specific guidance for when to use translation support, though cases can include automatic machine
translation, bots with internationalization support, and possibly some bridges.

## Potential issues

The language code spec might not encompass all of the possible language code combinations, but should cover
plenty given its popularity in HTML.

This does not apply to `m.text` or `m.html`, necessitating the use of the longer form `m.message` when sending
translated messages.

## Alternatives

No significant alternatives known.

## Security considerations

No specific considerations are required for this proposal.

## Unstable prefix

This MSC does not introduce anything which should conflict with stable usage. Implementations are encouraged
to review [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s unstable prefixing approach.
