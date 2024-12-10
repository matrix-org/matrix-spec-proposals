# MSC4148: Permitting HTTP(S) URLs for SSO IdP icons

The current [`m.login.sso` flow schema](https://spec.matrix.org/v1.10/client-server-api/#definition-mloginsso-flow-schema)
includes an optional `icon` field for clients to use when representing the Identity Provider.

Use of this icon currently relies on unauthenticated media download/thumbnail endpoints, which are
slated for deprecation and eventual removal through [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916).
Clients do not yet have credentials for the user and therefore may not be able to access these icons.
MSC3916 recommends that servers continue to allow the icons on the unauthenticated endpoints, though
this is only helpful so long as the endpoints exist.

This proposal introduces yet another temporary measure for handling these icons in the face of authenticated
media and the upcoming transition to OIDC: servers are permitted to use HTTP(S) URLs instead.

## Proposal

`icon` for the [`m.login.sso` flow schema](https://spec.matrix.org/v1.10/client-server-api/#definition-mloginsso-flow-schema)
has the following changes:

1. `mxc://` URI usage is *deprecated*, [pending removal](https://spec.matrix.org/v1.10/#deprecation-policy).
2. HTTPS and HTTP URLs are permitted.
3. Servers SHOULD prefer to use HTTPS URLs over HTTP or MXC URLs.
4. Icons SHOULD be 64x64 pixels in size, accounting for a wide range of screen resolutions.
   * This is because the thumbnail APIs are no longer accessible to clients with HTTP(S) URLs, so
     "reasonable" sizes should be picked. This is not a strong requirement as deployment-specific
     considerations may apply (larger sign-in button on a custom client, etc).

Some suggested spec text for `icon` to capture these changes would be:

> Optional. An HTTP(S) URL to provide an image/icon representing the IdP. Intended to be shown alongside
> `name` if provided.
>
> Servers SHOULD prefer HTTPS URLs over HTTP. `mxc://` URIs SHOULD NOT be used as their usage is deprecated
> here, though are permitted. Clients may have to use the deprecated, unauthenticated, media download
> and thumbnail endpoints to access content addressed by `mxc://` URIs.
>
> Images SHOULD be 64x64 pixels in size.

## Potential issues

Existing clients may block non-`mxc://` URI usage and show no icon. Though this can lead to subpar
user experience, the actual impact is expected to be temporary.

## Alternatives

* As it turns out, Element Web [overrides](https://github.com/matrix-org/matrix-react-sdk/blob/679b170bc5ae5eeb9c04c47fc5eeb663cb45b30c/src/components/views/elements/SSOButtons.tsx#L42)
  the icon if it recognizes the `brand`. This behaviour prevents authenticated media from breaking the
  icons, and avoids issues with HTTP(S) URL compatibility for the client. Other clients may wish to
  pursue a similar approach, particularly for popular brands/sign in methods.

* This entire SSO login mechanism could be replaced, which is what is happening with OIDC (as of
  writing). This MSC is intended to fill a gap between 'now' and when OIDC lands rather than being
  a complete solution.

## Security considerations

MXC URIs are intended to keep media 'inside' Matrix to reduce opportunities for user information to
be harvested by external entities. Unlike random image uploads to a room though, the server the user
is about to register an account on is the only entity able to control these URLs, reducing the risk
surface. Clients may wish to look into an approach similar to Element Web for handling common icons,
and possibly ways of not using icons if they feel "too sketchy". For example, if the icons aren't
served by a subdomain of the Client-Server API URL (`https://*.matrix.org` in the case of
`https://matrix-client.matrix.org`), the icon could be omitted.

## Unstable prefix

Placing this MSC behind an unstable prefix becomes very difficult very quickly. Instead, clients and
servers are suggested to *not* implement this proposal until it is considered stable.

## Dependencies

No direct dependencies. [MSC3916](https://github.com/matrix-org/matrix-spec-proposals/pull/3916)
increases the need for this MSC, however.
