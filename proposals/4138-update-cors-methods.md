# MSC4138: Update allowed HTTP methods in CORS responses

The [specification](https://spec.matrix.org/v1.10/client-server-api/#web-browser-clients) suggests
that servers allow a limited subset of the available [HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
available in [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) responses. However, it's
reasonable to expect the specification to use other methods in the future or as part of feature
detection. To permit these use cases early, this MSC proposes adding a few more allowable values to
the `Access-Control-Allow-Methods` header.

## Proposal

The [`Access-Control-Allow-Methods` header's recommended value](https://spec.matrix.org/v1.10/client-server-api/#web-browser-clients)
is updated to note that the HTTP methods described cover existing specified endpoints. Servers which
support additional endpoints or methods should add those methods as well. The specification will be
updated whenever a new method is supported by an endpoint.

Examples of possible future-use methods include:

* `PATCH` - A plausibly useful HTTP method for future use.
* `HEAD` - Similar to `PATCH`, `HEAD` is plausibly useful for feature detection and cases like
  [MSC4120](https://github.com/matrix-org/matrix-spec-proposals/pull/4120).

The following methods are *not* included because they don't have foreseeable use in Matrix:

* `CONNECT`
* `TRACE`

## Potential issues

None anticipated.

## Alternatives

No significant alternatives.

## Security considerations

CORS is meant to help ensure requests made by the client are properly scoped in the client. If the
client wishes to use an HTTP method not allowed by the server, the web browser will mask the
response with an error before the application can inspect it. Therefore, to increase future
compatibility, we append a few useful HTTP methods while still excluding ones which are (currently)
nonsensical.

## Unstable prefix

This proposal cannot have an unstable prefix due to the nature of CORS. Servers are already able to
go off-spec and serve different headers because the spec is merely a recommendation.

## Dependencies

This proposal has no dependencies.
