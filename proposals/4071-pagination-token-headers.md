# MSC4071: Pagination Token Headers

Many (Matrix) desktop apps are today written using webviews (electron, tauri, etc), these enforce
the use of CORS for requests to Matrix APIs. This adds an additional ~20-50ms (best case) to API
calls and usually isn't noticeable. But in Matrix the sync (and to a lesser extend messages)
endpoints are so often requested that this can have an impact (increased latency, wasted CPU, wasted
bandwidth) on both server and client.

This MSC proposes an opt-in workaround that enables clients to specify the pagination token in a
header rather than query string thus avoiding a new CORS request each time the token changes. This
is absolutely a hack, and if accepted must only be used to work around this specific problem.

Note that there are a bunch of less hacky [alternatives](#alternatives) but none of them are simple
and quick to implement such as this. This is very much a patch to alleviate the immediate issue while
better solutions can be worked out.

## Proposal

Super simple - clients may pass pagination tokens as a header instead of query parameters using the
format `X-Matrix-Pagination-$PARAM`, the following table lists the available headers by endpoint:

|Endpoint (link to current spec)|Query Parameter|Header Alternative|
|-|-|-|
|[`sync`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3sync)|`since`|`X-Matrix-Pagination-Since`|
|[`messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages)|`from`|`X-Matrix-Pagination-From`|
|[`messages`](https://spec.matrix.org/v1.8/client-server-api/#get_matrixclientv3roomsroomidmessages)|`to`|`X-Matrix-Pagination-To`|

Servers must treat the values exactly the same as the query string versions.

If a client makes a request specifying both header and query string servers should reject the request
with a 400 response and `M_INVALID_PARAM` error code.

## Potential issues

As noted above, this is a hack to work around CORS restrictions. Unfortunately CORS isn't going to
change any time soon (if ever). Whether the advantages outweigh the "ugliness" of this hack is up 
for discussion here.

## Alternatives

A POST request with a body containing the parameters would also suffice as a solution. Like this
proposal this would also be a hacky workaround.

[matrix-spec#223](https://github.com/matrix-org/matrix-spec/issues/223) discusses some other alternative
workarounds for the issue.

[MSC2108](https://github.com/matrix-org/matrix-spec-proposals/pull/2108) proposes using SSE as an
alternative. This would indeed work, but it's a significant change to implement and deploy everywhere.

## Security considerations

In the context of Matrix clients CORS provides no security and homeservers are expected to accept
all CORS preflight requests, so this change has no security impact.

## Unstable prefix

No unstable prefix required, but servers should indicate unstable support for this within the
`unstable_features` key of the versions endpoint as so:

```json
{
    "unstable_versions": {
        "com.beeper.msc4071": true
    }
}
```
