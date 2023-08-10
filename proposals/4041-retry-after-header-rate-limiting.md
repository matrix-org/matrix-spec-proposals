# MSC4041: Use http header Retry-After to enable library-assisted retry handling

The current Matrix Client-Server API (v1.7) recommends that home servers should protect themselves from
being overloaded by enforcing rate-limits to selected API calls.
If home servers limit access to an API they respond with an http error code 429 and a response body
that includes a property `retry_after_ms` to indicate how long a client has to wait before retrying.

Some http libraries (like [Ky](https://github.com/sindresorhus/ky), [got](https://github.com/sindresorhus/got
and [urllib3](https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry)) ease
the burden of handling retries by honoring the http header `Retry-After`. As explained in 
[RFC 9119 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110#field.retry-after) this header is optional
and contains either a (relative) value for the delay in seconds or an (absolute) date.

The current Matrix Client Server API specification does not take this header into account. This wastes the 
potential that current http libraries offer in terms of automated retry handling.

## Proposal

In order to allow developers to make use of the automated retry handling capabilities of http libraries
home servers should add an http header `Retry-After` in case they respond with an http error 429.
Since the body of the response already contains a property `retry_after_ms` (in miliseconds) the value 
of `Retry-After` should be the calculated by rounding up `retry_after_ms * 1000` to the next integer. 
Doing so would correspond to a (relative) delay (in seconds) as defined in 
[RFC 9119 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110#field.retry-after).

## Potential issues

Existing SDKs may use client libraries that migth be able to honor the http header `Retry-After`. Since 
this header is currently not part of the response developers might have created purpose-built functions
in order to handle rate-limiting correctly.

If the http header `Retry-After` is introduced existing SDKs might behave differently thus leading to an
unexpected behaviour.


## Alternatives

N/A


## Security considerations

N/A

## Unstable prefix

N/A

## Dependencies

N/A