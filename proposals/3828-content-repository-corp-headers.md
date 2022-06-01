# MSC3828: Content Repository Cross Origin Resource Policy (CORP) Headers

In 2018 two side-channel hardware vulnerabilities, [Meltdown](https://en.wikipedia.org/wiki/Meltdown_(security_vulnerability)) and [Spectre](https://en.wikipedia.org/wiki/Spectre_(security_vulnerability)) were disclosed. In web browsers this meant that features such as high resolution timers and SharedArrayBuffer could be used to expose sensitive data across origins. In response, browser vendors have required documents that wish to continue using features such as SharedArrayBuffer to be served with the `Cross-Origin-Embedder-Policy: require-corp` header. This header prevents a document from loading any cross-origin resources that don't explicitly grant the document permission via the `Cross-Origin-Resource-Policy` header.

Currently Matrix homeservers are expected to serve all routes with the `Access-Control-Allow-Origin: *` header. This allows web clients on one origin to fetch content from homeservers on other origins. However, when the web client uses SharedArrayBuffer and the required `Cross-Origin-Embedder-Policy: require-corp` header, all embedded documents must set the required CORP header.

## Proposal

The content repository should serve assets with the `Cross-Origin-Resource-Policy: cross-origin` header. This allows web clients to set the `Cross-Origin-Embedder-Policy: require-corp` header and enable access to APIs like SharedArrayBuffer.

This header should be set on responses from the following endpoints:

- `/_matrix/media/r0/download`
- `/_matrix/media/r0/thumbnail`

## Potential issues

See [Security considerations](#Security-considerations)

## Alternatives

Clients using features like SharedArrayBuffer cannot fetch media from the Matrix media repositories without these headers.


## Security considerations

I don't believe this poses any additional risks to private data from Matrix homeservers. We are not exposing iframes with personal data or any data that could not already be gathered from Matrix's existing APIs. However, I believe this proposal deserves thorough review.

## Unstable prefix

TODO

## Dependencies

None