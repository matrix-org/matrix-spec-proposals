# MSC4528: `M_INCOMPATIBLE_SERVER` error code

Following [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291) and
[MSC4311](https://github.com/matrix-org/matrix-spec-proposals/pull/4311), the Server-Server API
tells sending servers to convert certain federation errors into 5xx errors over the Client-Server
API. [`PUT /_matrix/federation/v2/send_join/{roomId}/{eventId}`](https://spec.matrix.org/v1.19/server-server-api/#put_matrixfederationv2send_joinroomideventid)
and [`PUT /_matrix/federation/v2/invite/{roomId}/{eventId}`](https://spec.matrix.org/v1.19/server-server-api/#put_matrixfederationv2inviteroomideventid)
both say of their `400` response:

> If `M_MISSING_PARAM` or `M_INVALID_PARAM` is returned and the request is associated
> with a Client-Server API request, the Client-Server API request SHOULD fail
> with a 5xx error rather than being passed through.

These rejections occur when the events in the request fail the validation introduced by those MSCs,
for example when an invite lacks a full-PDU `m.room.create` event in its stripped state. The
rationale for a 5xx is that there is nothing the client can do differently to make the request
succeed.

This translation has three problems:

1. No specific status code or `errcode` is given, so clients cannot detect this case and give a more
   helpful error message.

2. Many clients and client SDKs automatically retry requests which fail with a 5xx status code.
   However, the failures in the MSCs are not transient as the two servers will remain incompatible
   until one of them is updated, which will not happen within any retry window.

3. There is no good 5xx error code to use. 500 response rates are often monitored and assumed to
   mean something has gone wrong and needs fixing. 502/503 response are often interpreted by reverse
   proxies and load balancers as the backend being down, and will stop sending traffic to said
   backend. The other defined 5xx errors don't really fit and are rarely used.

This proposal replaces the 5xx translation with a `400` response carrying a new standard error code,
`M_INCOMPATIBLE_SERVER`, meaning the request failed because the local server and a remote server it
needed to communicate with are incompatible with each other.

The spec already uses `400` error codes to indicate final error responses that are not the fault of
the sending client, such as `M_INCOMPATIBLE_ROOM_VERSION`.

## Proposal

A new standard error code is added to the Client-Server API:

* `M_INCOMPATIBLE_SERVER`: The request could not be completed because it required communicating with
  a remote server which is incompatible with the local server.

Clients SHOULD NOT automatically retry a request which failed with `M_INCOMPATIBLE_SERVER` and
SHOULD surface the failure to the user. Servers SHOULD use the human-readable `error` field to describe
the incompatibility, which clients MAY show to the user.

Future proposals SHOULD continue to strive to maintain backwards compatibility where feasible,
rather than use `M_INCOMPATIBLE_SERVER`.

The paragraph quoted above is replaced, on both the `/send_join` and `/invite` endpoints, with the
following:

> If `M_MISSING_PARAM` or `M_INVALID_PARAM` is returned and the request is associated with a
> Client-Server API request, the Client-Server API request SHOULD fail with a
> `400 M_INCOMPATIBLE_SERVER` standard Matrix error rather than the federation error being passed
> through.

For example, a client calling [`POST /_matrix/client/v3/rooms/{roomId}/invite`](https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3roomsroomidinvite)
where the invited user's server rejects the federation invite would receive:

```json
{
  "errcode": "M_INCOMPATIBLE_SERVER",
  "error": "example.org rejected the invite because the two servers are incompatible. One of them may need updating."
}
```

Note that the message does not say which server is at fault. On receiving the federation error, the
sending server cannot know which of the two implementations is outdated.

While the [MSC4291](https://github.com/matrix-org/matrix-spec-proposals/pull/4291) and
[MSC4311](https://github.com/matrix-org/matrix-spec-proposals/pull/4311) validation failures are the
motivating cases, the error code is defined generically. Other endpoints and future proposals MAY
use `M_INCOMPATIBLE_SERVER` wherever a request fails because a remote server could not interoperate
with the local server, rather than because of a client error or a fault within the local server
itself.

## Potential issues

* Strictly speaking, `400` is the wrong class for this failure. The client's request was well-formed
  and the fault lies between the two servers. In practice, however, Matrix (and the lot of the web)
  treats 4xx responses as permanent failures and 5xx responses as potentially transient ones. The
  strict interpretation of the status ranges offers no third option for a final error that is
  no-one's fault (which is the case here). Matrix already returns `400` for failures outside the
  client's control, such as
  [`M_INCOMPATIBLE_ROOM_VERSION`](https://spec.matrix.org/v1.19/client-server-api/#other-error-codes).

* The receiving server may return `M_MISSING_PARAM` or `M_INVALID_PARAM` because of a bug rather
  than version skew. The sending server cannot tell the difference, and does not need to. Either
  way the two implementations failed to interoperate, and retrying will not help.

* This proposal is backwards compatible as the current text is only a SHOULD and does not specify
  the response body. Given the underspecified nature of the existing text, no client can be relying
  on the current behaviour anyway.

## Alternatives

We could keep the 5xx translation but specify it fully, e.g. as `502 M_INCOMPATIBLE_SERVER`. In
strict HTTP terms `502 Bad Gateway` is the closest fit, since the local server is acting as a
gateway to a remote server which returned an unusable response. However, using a 502 here goes
against the common assumptions made by clients and proxies about such errors.

## Security considerations

None foreseen.

## Unstable prefix

None needed.

## Dependencies

None.
