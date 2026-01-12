# MSC4003: Semantic table attributes

The specification currently [advises][msgtypes] clients to malform HTML tables
by removing attributes that encode table data. For example, if a message
contains the following table—

> <table>
> <thead>
> <tr><th>A</th><th>B</th><th>C</th></tr>
> </thead>
> <tbody>
> <tr><td colspan="2">D</td><td>E</td></tr>
> </tbody>
> </table>

—the specification advises that it be transformed to:

> <table>
> <thead>
> <tr><th>A</th><th>B</th><th>C</th></tr>
> </thead>
> <tbody>
> <tr><td>D</td><td>E</td></tr>
> </tbody>
> </table>

To maintain message integrity, HTML attributes that encode table _data_ should
be permitted. These attributes pose no security risk, serve a narrowly defined
semantic role, and are a natural completion of the existing permissions.

## Proposal

### Process

To identify which attributes should be permitted, apply the following
constraints:

1.  Constrain to the [permitted tags][msgtypes] of the existing specification.

    > `table`, `thead`, `tbody`, `tr`, `th`, `td`

    Rationale: The purpose of this MSC is to correct a technical oversight in
    the existing specification while preserving its intent, not to add new
    functionality.

1.  Constrain to the [permitted attributes][Sanitize] of a typical sanitizer.

    > | Tag     | Permitted attributes                                                                                         |
    > | ------- | ------------------------------------------------------------------------------------------------------------ |
    > | `table` | `align`, `bgcolor`, `border`, `cellpadding`, `cellspacing`, `frame`, `rules`, `sortable`, `summary`, `width` |
    > | `th`    | `abbr`, `align`, `axis`, `colspan`, `headers`, `rowspan`, `scope`, `sorted`, `valign`, `width`               |
    > | `td`    | `abbr`, `align`, `axis`, `colspan`, `headers`, `rowspan`, `valign`, `width`                                  |

    Rationale: Security takes priority over other concerns.

1.  Constrain to attributes that encode content (not
    [presentation][separation of content and presentation]):

    > | Tag     | Permitted attributes                                                                                                                             |
    > | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
    > | `table` | ~~`align`~~, ~~`bgcolor`~~, ~~`border`~~, ~~`cellpadding`~~, ~~`cellspacing`~~, ~~`frame`~~, ~~`rules`~~, ~~`sortable`~~, `summary`, ~~`width`~~ |
    > | `th`    | `abbr`, ~~`align`~~, `axis`, `colspan`, `headers`, `rowspan`, `scope`, ~~`sorted`~~, ~~`valign`~~, ~~`width`~~                                   |
    > | `td`    | `abbr`, ~~`align`~~, `axis`, `colspan`, `headers`, `rowspan`, ~~`valign`~~, ~~`width`~~                                                          |

    Rationale: The scope of this MSC is data integrity. Presentation is the
    responsibility of the client.

1.  Constrain to [standard] attributes:

    > | Tag     | Permitted attributes                                         |
    > | ------- | ------------------------------------------------------------ |
    > | `table` | ~~`summary`~~                                                |
    > | `th`    | `abbr`, ~~`axis`~~, `colspan`, `headers`, `rowspan`, `scope` |
    > | `td`    | ~~`abbr`~~, ~~`axis`~~, `colspan`, `headers`, `rowspan`,     |

    Rationale: Strict adherence to open standards supports interoperability and
    accessibility.

### Results

Following the above process, the resulting proposed permissions are:

| Tag  | Permitted attributes                                       |
| ---- | ---------------------------------------------------------- |
| `th` | [`abbr`], [`colspan`], [`headers`], [`rowspan`], [`scope`] |
| `td` | [`colspan`], [`headers`], [`rowspan`]                      |

## Potential issues

In practice the `headers` attribute is useless without corresponding `id`
attributes, but robust handling of `id` attributes in user-generated content is
a broader topic with potentially complex needs and should be discussed
separately. For the purposes of this MSC it would suffice to simply omit the
`headers` attribute, but including it here has negligible cost and the benefit
of separating concerns in the long term.

## Security considerations

As specified, the `abbr`, `colspan`, `headers`, `rowspan`, and `scope`
attributes have no potential for causing effects outside of the table. All are
permitted in default configurations of popular HTML sanitizers:

- [Sanitize] (used by GitHub)
- [Loofah] (used by Rails)
- [Bleach] (popular Python library)

Exceptions:

- [sanitize-html] (used by Element) doesn’t include them, but is a younger
  project with currently incoherent defaults that are unfit as a reference for
  any use case.
- [Ammonia] (popular Rust library) permits most of the proposed attributes but
  omits `abbr` without explanation. From skimming its version history its
  defaults appear to have been formed through ad hoc feedback rather than
  principled research.

[`abbr`]: https://html.spec.whatwg.org/multipage/tables.html#the-th-element
[Ammonia]: https://github.com/rust-ammonia/ammonia/blob/v3.3.0/src/lib.rs#L422-L442
[Bleach]: https://github.com/mozilla/bleach/blob/v6.0.0/bleach/_vendor/html5lib/filters/sanitizer.py#L195
[`colspan`]: https://html.spec.whatwg.org/multipage/tables.html#attributes-common-to-td-and-th-elements
[`headers`]: https://html.spec.whatwg.org/multipage/tables.html#attributes-common-to-td-and-th-elements
[Loofah]: https://github.com/flavorjones/loofah/blob/v2.20.0/lib/loofah/html5/safelist.rb#L231
[msgtypes]: https://spec.matrix.org/v1.6/client-server-api/#mroommessage-msgtypes
[`rowspan`]: https://html.spec.whatwg.org/multipage/tables.html#attributes-common-to-td-and-th-elements
[Sanitize]: https://github.com/rgrove/sanitize/blob/v6.0.1/lib/sanitize/config/relaxed.rb#L27-L29
[sanitize-html]: https://github.com/apostrophecms/sanitize-html/blob/v1.9.0/index.js#L295
[`scope`]: https://html.spec.whatwg.org/multipage/tables.html#the-th-element
[separation of content and presentation]: https://en.wikipedia.org/wiki/Separation_of_content_and_presentation
[standard]: https://html.spec.whatwg.org/multipage/tables.html
