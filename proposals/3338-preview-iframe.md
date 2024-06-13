# Support `<iframe />` in preview url

Synapse preview object has limited support for extracting content from oEmbed `"rich"` type `html`. We propose for `<iframe />` tags from the `html` to be represented.

## Background

Synapse preview converts oEmbed format to Open Graph tags, downloads referred content and serves it. The process is well suited for oEmbed `photo`, `video` and `link` types. With the `"rich"` type, oEmbed `html` element is scanned for `og:` meta tags, and if specific tags are not found the content is searched for the relevant html tags that can be converted to missing `og:` tags. At the moment, `title`, `description` and `image` tags are being looked for, `video` being on the wish list.

This works fine when the content is public, however some content is available only for authenticated users. That content cannot be downloaded from the provider, because it needs authenticated client. One of the ways of providing such content is to embed it in `iframe` that requests authentication. For that case we need `iframe` specifics.

## Proposal

It is not often that oEmbed  `html` will contain `<iframe />` tag, however it is a way of displaying authenticated content.

We propose for `iframe` to be specified with:

  * `og:url` tag for `iframe` `src`
  * custom tag `matrix:iframe` set to `true`
  * custom tag `matrix:iframe:width` for `iframe` `width` (optional)
  * custom tag `matrix:iframe:height` for `iframe` `height` (optional)

## Potential issues

It is a new set of tags that does not conflict, so shold not bring any issues.

## Security considerations

The feature is only oEmbed related. If privacy is an issue, administrators can always provide a curated list of "trusted" oembed providers rather than using the default list. May not be ideal, but gives an option. If it is a big concern, maybe  a config param `oembed_show_iframe` or similar can be added  on the client side.

The rationale is: "We want oEmbed content from provider X, provider X sent us an `iframe`, therefore we want that `iframe`"

## Unstable prefix

