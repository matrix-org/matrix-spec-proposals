# Markup locations for Text

[MSC3574](https://github.com/opentower/matrix-doc/blob/main/proposals/3574-resource-markup.md)
proposes a mechanism for marking up resources (webpages, documents, videos, and
other files) using Matrix. The proposed mechanism requires an
`m.markup.location` schema for representing the location of annotations within
different kinds of resources. MSC3574 punts on what standard location types
might be available, deferring that large family of questions to other MSCs.
This MSC aims to provide basic location types for marking up textual resources.
 
## Proposal

Markup locations for text should approximately follow the format for textual
annotations provided by the w3c's [web annotation data
model](https://www.w3.org/TR/annotation-model/). This will simplify
interoperability with WADM-based annotation systems like
[hypothes.is](https://hypothes.is).

Markup locations for text should applicable to `text/*` Media Types, including
markdown and html. It should also be at least partly applicable to formats that
provide an associated text stream, such as `application/pdf`,
`application/epub+zip`, and video or audio files with embedded lyrics or
captions.

The WADM model provides two basic notions of locations in text: "Text Position"
(roughly, an offset) and "Text Quote" (roughly, a search query). In practice,
both should be provided for a given text location whenever possible, for robust
anchoring in contexts where the underlying text may change (for example, on the
web). In these cases, clients can use the Text Position offset to find an
approximate position, and look for the nearest approximately matching Text
Quote.

### Text Positions

Text Positions will be represented within an `m.markup.location` as follows:

```
m.markup.location: {
    m.markup.text.position: {
        start: ..
        end: ..
    }
    ..
}
```

The `start` and `end` values should be non-negative integers, with 0 indicating
a position before the first character of the document's text, 1 indicating the
position after the first character and before the second, and so on.

The following requirements from the web annotation data model must be
respected:

> The selection of the text must be in terms of unicode code points (the
"character number"), not in terms of code units (that number expressed using a
selected data type). Selections should not start or end in the middle of a
grapheme cluster. The selection must be based on the logical order of the text,
rather than the visual order, especially for bidirectional text.

> The text must be normalized before recording in the Annotation. Thus HTML/XML
tags should be removed, and character entities should be replaced with the
character that they encode. 

In view of the ambiguity of the markdown format (and similar text formats), and
the resulting complexity of normalization, special markdown characters should
*not* be removed before generating a text position.

### Text Quotes

Text Quotes will be represented within an `m.markup.location` as follows:

```
m.markup.location: {
    m.markup.text.quote: {
        exact: ...
        prefix: ...
        suffix: ...
    }
    ..
}
```

The `exact` value should be the text occupying the designated location. The
`prefix` should be a snippet of text occurring before the designated location,
and the `suffix` should be a snippet occurring after the designated location.
`prefix` and `suffix` may be omitted in cases where they're clearly unnecessary
to disambiguate the location. 

Text should be normalized as above. In the case of multiple matches, all
matches should be treated as part of the location.

### Text Ranges

There may be cases in which we want to use the selectors above to indicate the
endpoints of a text range, because we want, for example, to select from the
beginning of a document to a certain phrase, or because we want to select a
long quote without including the contents of the quote in the `exact` value.

In these cases, we can use a Text Range location, `m.markup.text.range`. Each
endpoint of the range should be given either as a non-negative integer, or as a
`prefix`/`suffix` pair. So for example,

```
m.markup.location: {
    m.markup.text.range: {
        start: 0
        end: {
            prefix: "the",
            suffix: " end"
    }
}
```

would indicate all of "this is the end" except " end".

### Web Annotation Data Model Serialization

## Security considerations
