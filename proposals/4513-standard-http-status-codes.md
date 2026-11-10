# MSC4513: Standard HTTP status codes for all endpoints, current and future

Current endpoints often under-specify the HTTP status codes which are permitted on them, especially
for errors. This leads to servers being unable to return unspecified errors in common cases, like when
a request body is too large, too frequent, or wrong.

This proposal introduces a set of common HTTP status codes which can be returned on *all* endpoints
in the specification, current and future, to enable servers to protect themselves from harmful and
otherwise unprocessable requests.


## Proposal

All endpoints, current and future, across all APIs (Identity, Federation, Client-Server, etc) in the
specification MAY return any of the following HTTP status codes:

* [`413 Content Too Large`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/413)
* [`414 URI Too Long`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/414)
* [`415 Unsupported Media Type`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/415)
* [`416 Range Not Satisfiable`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/416)
* [`417 Expectation Failed`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/417)
* [`429 Too Many Requests`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)
* [`431 Request Header Fields Too Large`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/431)
* [`500 Internal Server Error`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/500)
* [`502 Bad Gateway`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/502)
* [`503 Service Unavailable`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/503)
* [`504 Gateway Timeout`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504)

These HTTP status codes SHOULD be accompanied by [standard Matrix errors](https://spec.matrix.org/v1.19/client-server-api/#standard-error-response)
for the relevant API, but MAY be served without them.

When the status codes are used is left as an implementation detail. Servers are expected to use the
HTTP status codes reasonably. For example, 413 shouldn't be used if a send event request is within
the size limit for an event.

Servers SHOULD return the most specific HTTP status code possible at all times, especially if the
endpoint specifies better options or overloads a status code from above. Servers are not required to
return all of the above HTTP status codes.


## Potential issues

There are likely more status codes we could blanket-apply to endpoints, however their use is even
more niche than some of the status codes already included in this proposal. 431 for example is unlikely
to be returned in most environments, but has a reasonable semantic meaning that a buggy or malicious
client could cause a reverse proxy to return the error code with the proxy's default configuration.

More HTTP status codes can be added in future proposals as needed.

A reverse proxy's default configuration might also cause a client to receive a non-Matrix error response,
causing further errors within the client. This is already true today: a common reverse proxy setup
for a Matrix homeserver returns 503/504 errors without rewriting them as `500 M_UNKNOWN` errors. This
proposal permits the behaviour because it doesn't cause significant issues for clients.

Servers behind services like Cloudflare might need to rewrite errors anyway to avoid Cloudflare and
similar backing off requests. For example, if Cloudflare sees a 504 error then it might reject further
requests with a 504 itself to give the backend server a chance to recover. Those errors are likely
to be HTML pages rather than Matrix errors too.


## Alternatives

Alternatives largely amount to "don't do this" and aren't discussed here. Additions/subtractions to
the error codes list are expected to be discussed within the MSC and Potential Issues. This MSC does
not intend to be perfect or fully complete.


## Security considerations

It is the position of the spec, and this proposal, that servers *must* be able to protect themselves
from malicious or buggy requests. This includes DoS concerns, resource exhaustion, and server-side
failure. Some endpoints in the specification currently say "Rate limited: no", which is unacceptable.


## Unstable prefix

This proposal cannot practically be implemented with a prefix, and some of the status codes have already
been used by servers in production today. No significant issues are expected from returning these status
codes in production.


## Dependencies

No significant dependencies.
