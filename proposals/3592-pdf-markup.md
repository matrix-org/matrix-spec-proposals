# Markup locations for PDF documents

[MSC3574](https://github.com/matrix-org/matrix-spec-proposals/pull/3574)
proposes a mechanism for marking up resources (webpages, documents, videos, and
other files) using Matrix. The proposed mechanism requires an
`m.markup.location` schema for representing the location of annotations within
different kinds of resources. MSC3574 punts on what standard location types
might be available, deferring that large family of questions to other MSCs.
This MSC aims to provide two basic location types for marking up PDFs.

## Proposal

Markup locations for PDFs should approximately follow the format of embedded
annotations provided in the PDF standard, for more straightforward integration
with PDF rendering and editing libraries that clients may wish to make use of. 

The PDF standard includes many different kinds of annotations: 19 in PDF 1.4 
(see [p499 here](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/pdf_reference_archives/PDFReference.pdf)) 
and 26 in PDF 1.7, (see [p390 here](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf)).
This proposal introduces events for two of these kinds of annotations: *Text 
Annotations*, which represent "sticky notes" at a certain point in the text, 
and *Highlights*,which represent a certain range of text that should be highlighted.

PDF annotations all accept a very large set of different attributes. Of
these, only two are mandatory: `Subtype` and `Rect`, where `Subtype` gives the
annotation type, and `Rect` gives the position of the annotation on the PDF
page as a rectangle represented by an array of the form

    [lower-left-x, lower-left-y, upper-right-x, upper-right-y]

where each item is a number of "user space units" (72ths of an inch) from the
bottom left corner of the page, sometimes called *points*.

This MSC does not propose to include any of the optional attributes. The
`Subtype` attribute will be indicated by a key of the `m.markup.location`
object. So only `Rect`, and the attributes specific to each annotation type,
need to be provided for.

Within a PDF, an annotation occurs as part of the content stream associated 
with a particular page, so the page number doesn't need to be represented as
an attribute of the annotation. Since this information is not automatically 
available in the Matrix context, `m.markup` locations for PDFs will also 
require a *page index* field. The page index is a non-negative integer, and 
is distinct from a *page label*, which is a string (for example "iv" within 
the front matter of a book).

### Text Annotations

Text annotations will be represented within an `m.markup.location` as follows:

```
"m.markup.location": {
    "m.markup.pdf.text": {
        "rect": {"left": ..., "right": ..., "top": ..., "bottom": ...}
        "contents": ...
        "page_index": ...
    }
    ..
}
```

The `contents` is a string indicating text for the text annotation. Precisely
how to set it will be left as an implementation detail for clients.

Optionally, `m.markup.pdf.text` may also contain a `name` value, which should
be a string that names an icon to be used in displaying the annotation.
Standardly recognized values are: "Comment", "Key", "Note", "Help",
"NewParagraph", "Paragraph" and "Insert".

### Highlight Annotations

Highlight Annotations will be represented within an `m.markup.location` as
follows:

```
"m.markup.location": {
    "m.markup.pdf.highlight": {
        "rect": {"left": ..., "right": ..., "top": ..., "bottom": ...}
        "contents": ...,
        "quad_points": [...],
        "page_index": ...
    }
    ..
}
```

The `contents` are as above. `quad_points` is an array of arrays of the form:

    [x_1,y_1,x_2,y_2,x_3,y_3,x_4,y_4]

each of which represents the vertices (in counterclockwise order) of an
oriented quadrilateral region of the PDF page. Each quadrilateral is meant to
encompass a word or group of contiguous words in the highlighted text.

Optionally, the `m.markup.pdf.highlight` may also include a `text_content` value,
which should be a string containing the highlighted text. The `text_content`
value is not part of the PDF standard, but is included as a convenience for
clients.

## Alternatives

Rather than accepting this MSC, we could wait for a more comprehensive MSC that
tries to comprehensively specify a complete set of location types on PDFs.
However, it seems best to work iteratively, and start with the pdf location
types that can most easily be implemented, rather than waiting until something
truly comprehensive can be implemented.

Rather than using userspace units, we could use some more fine-grained
coordinate system, for example milli-units. The PDF standard lets units
take on "real number values" so precision greater than one unit is possible.
But since we can't have float values in matrix events, we can't capture this
greater precision on the present proposal. However, this would probably create
confusion, and precision greater than 1/72th of an inch is probably excessive.

## Security considerations

Because room state is unencrypted, `m.space.child` events conveying locations
via `m.markup.location.highlight` could leak information about an encrypted
resource text through the `text_contents` field, or about the annotation itself
through the `contents` field. This is part of a more general problem with state
events potentially leaking information, and deserves a general resolution, a la
[MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414)

## Unstable prefix

| Proposed Final Identifier | Purpose                                                    | Development Identifier                        |
| ------------------------- | ---------------------------------------------------------- | --------------------------------------------- |
| `m.markup.pdf.text`       | key in `m.markup.location`                                 | `com.open-tower.msc3592.markup.pdf.text`      |
| `m.markup.pdf.highlight`  | key in `m.markup.location`                                 | `com.open-tower.msc3592.markup.pdf.highlight` |
