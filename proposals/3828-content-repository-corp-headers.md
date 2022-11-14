# MSC3828: Content Repository Cross Origin Resource Policy (CORP) Headers

In 2018 two side-channel hardware vulnerabilities,
[Meltdown](https://en.wikipedia.org/wiki/Meltdown_(security_vulnerability))
and [Spectre](https://en.wikipedia.org/wiki/Spectre_(security_vulnerability)) were disclosed.
In web browsers this meant that features such as high resolution timers and SharedArrayBuffer
could be used to expose sensitive data across origins. In response, browser vendors have
required documents that wish to continue using features such as SharedArrayBuffer to be
served with the `Cross-Origin-Embedder-Policy: require-corp` header. This header prevents a
document from loading any cross-origin resources that don't explicitly grant the document
permission via the `Cross-Origin-Resource-Policy` header.

Currently Matrix homeservers are expected to serve all routes with the
`Access-Control-Allow-Origin: *` header. This allows web clients on one origin to fetch
content from homeservers on other origins. However, when the web client uses SharedArrayBuffer
and the required `Cross-Origin-Embedder-Policy: require-corp` header, all embedded documents
must set the required CORP header.

## Proposal

The content repository should serve assets with the `Cross-Origin-Resource-Policy: cross-origin`
header. This allows web clients to set the `Cross-Origin-Embedder-Policy: require-corp`
header and enable access to APIs like SharedArrayBuffer.

This header should be set on responses from the following endpoints:

- `/_matrix/media/v3/download`
- `/_matrix/media/v3/thumbnail`

## Potential issues

Chrome 73-75 have problems downloading files with this header, see [bug 952834](https://crbug.com/952834).
Chrome 80-85 has a [bug](https://crbug.com/1074261) with viewing multi-page PDF documents with CORP
headers set to `same-origin`. This proposal is for setting the header to `cross-origin` which should
not have an issue but I was not able to verify this. However,
[MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cross-Origin_Resource_Policy_(CORP)#browser_compatibility)
suggests this bug was fixed in Chrome 86 by disabling partial PDF loading. I was able to verify that
multi-page PDFs are viewable in the latest versions of Chrome, Safari, and Firefox with either header
value set. This should only be an issue if you require supporting Chrome 73-75.

Also see [Security considerations](#Security-considerations)

## Alternatives

Clients using features like SharedArrayBuffer cannot fetch media from the Matrix media
repositories without these headers.


## Security considerations

I don't believe this poses any additional risks to private data from Matrix homeservers.
We are not exposing iframes with personal data or any data that could not already be
gathered from Matrix's existing APIs. However, I believe this proposal deserves thorough review.

## Unstable prefix

None

## Dependencies

None
