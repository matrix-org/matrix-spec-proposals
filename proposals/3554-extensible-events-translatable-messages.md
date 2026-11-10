# MSC3554: Extensible Events - Translatable Messages

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers translations
on `m.text` content blocks specifically.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way images
are represented should not block the overall schema from going through.

**Note**: As a second priority MSC in the Extensible Events series, this MSC is not proposed to be a
blocker on extensible events entering the specification - this can mean that when extensible events
are available, translations might not be (in stable form). Readers should consider the unstable prefix
section for early support of this MSC.

## Proposal

As defined by MSC1767, `m.text` currently specifies an array with "representations" for the text
on the event. Clients are expected to find the first representation they can render based on mimetype,
which can be implicit.

Sender-provided translations can be useful in contexts where the sender knows multiple languages are
used in a room, such as announcements or other prepared communications. Less common in instant messaging
(at least without a translation service on the sender's side), the receiving client can use the message
which matches the user's preferred language.

This MSC adds an additional key, `lang`, to the `m.text` representation schema and adjusts how a
client decides upon a representation to include the language in that consideration. The array overall
is still ordered, which means the sender should also supply the language which fits the scenario best
as the first item.

An example:

```json5
{
    "type": "m.message",
    "content": {
        "m.text": [
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

*Note*: `m.text`'s support for `mimetype` has been excluded from the example for brevity. It is still
supported in events.

By default, messages are assumed to be sent in English (`en`).

`lang` must be a valid language code under [BCP-47](https://www.rfc-editor.org/rfc/bcp/bcp47.txt). This is
in line with the HTML specification which uses a similar attribute on the `<html>` node.

There is no specific guidance for when to use translation support, though cases can include automatic machine
translation, bots with internationalization support, and possibly some bridges.

## Potential issues

The language code spec might not encompass all of the possible language code combinations, but should cover
plenty given its popularity in HTML.

If a sending client supports several languages, receiving clients could spend extra time attempting to find
a suitable representation to render. This is considered a non-issue, though clients should consider how to
efficiently search an array.

## Alternatives

No significant alternatives known.

## Security considerations

No specific considerations are required for this proposal.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc3554.lang` instead of `lang`
when sending events.

Note that extensible events should only be used in an appropriate room version as well.
