# MSC4159: Remove the deprecated name attribute on HTML anchor elements

Some message types in `m.room.message`, such as `m.text`, permit including HTML in the event content.
The spec [recommends] that clients limit the HTML they render to prevent attacks and provides a list
of permitted HTML tags and attributes. In particular, it allows using the `name` attribute on `a` tags.
This attribute is obsolete according to the [WHATWG HTML Living Standard] which is why this proposal
attempts to remove it from the spec.


## Proposal

The `name` attribute was originally introduced to define targets for linking to specific parts of a
webpage. As an example, including the named anchor `<a name="foo">bar</a>` on a site allows you to append
the fragment `#foo` to the URL to cause your browser to scroll the anchor into view after loading the page.

In modern versions of HTML this feature has been superseded by the `id` attribute which extends targeted
linking to more than just `a` tags. As a result, the `name` attribute is marked deprecated in [MDN].

> Was required to define a possible target location in a page. In HTML 4.01, `id` and `name` could
> both be used on `<a>`, as long as they had identical values.
>
> Note: Use the global attribute `id` instead.

Furthermore, it is also tracked as [obsolete but conforming] in WHATWG.

> Authors should not specify the `name` attribute on `a` elements. If the attribute is present, its value
> must not be the empty string and must neither be equal to the value of any of the IDs in the element's
> tree other than the element's own ID, if any, nor be equal to the value of any of the other `name`
> attributes on `a` elements in the element's tree. If this attribute is present and the element has an ID,
> then the attribute's value must be equal to the element's ID. In earlier versions of the language, this
> attribute was intended as a way to specify possible targets for fragments in URLs. The `id` attribute
> should be used instead.

On top of the deprecation of the `name` attribute in HTML, it is unclear what this feature would ever have
been used for in the context of Matrix. It appears highly undesirable to let events define targeted links
into a client's UI, not least because the value of the `name` attribute would need to be unique on the
entire page. Additionally, linking to specific events is already possible via [matrix.to URIs].

Therefore, the `name` attributed is removed from the list of permitted attributes on `a` tags without a
replacement.


## Potential issues

Use cases that currently depend on the `name` attribute will be broken once the attribute is removed from
the allowed list. No concrete use cases are known as of writing, however.


## Alternatives

None.


## Security considerations

None.


## Unstable prefix

None.


## Dependencies

None.


[MDN]: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a#name
[WHATWG HTML Living Standard]: https://html.spec.whatwg.org/
[matrix.to URIs]: https://spec.matrix.org/v1.10/appendices/#matrixto-navigation
[obsolete but conforming]: https://html.spec.whatwg.org/#obsolete-but-conforming-features
[recommends]: https://spec.matrix.org/v1.10/client-server-api/#mroommessage-msgtypes
