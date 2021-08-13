# Support `<iframe />` in preview url

Synapse converts oEmbed format to Open Graph. oEmbed `"rich"` type `html` is scanned for relevant html tags that can be converted to `og:` meta tags. We propose for `<iframe />` tags to be included.

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

There is always cause for concern when displaying foreign content. However, preview resource is linking to the foreign content and displaying it already.

## Unstable prefix

