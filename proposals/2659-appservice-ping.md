# Application service ping endpoint

## Problem
A relatively common problem when setting up appservices is the connection
between the appservice and homeserver not working in one or both directions.
If the appservice is unable to connect to the homeserver, it can simply show
the error message to the user. However, there's currently no easy way for the
appservice to know if the homeserver is unable to connect to it. This means
that the appservice might start up fine, but not actually work, because the
homeserver isn't sending events to it.

## Proposed solution
The proposed solution is a new endpoint in homeservers that appservices can use
to trigger a ping. A new endpoint is also added to the appservice side for the
homeserver to call without any side-effects.

Appservices can use the endpoint at startup to ensure communication works in
both directions, and show an error to the user if it doesn't.

### `POST /_matrix/app/v1/ping`
This endpoint is on the appservice side. Like all other appservice-side
endpoints, it is authenticated using the `hs_token`. When the token is correct,
this returns HTTP 200 and an empty JSON object as the body.

### `POST /_matrix/client/v1/appservice/{appserviceId}/ping`
When the endpoint is called, the homeserver makes a `/_matrix/app/v1/ping`
request to the appservice.

The request body may contain a `transaction_id` field, which, if present, must
be passed through to the appservice `/ping` request body as-is.

This endpoint is only allowed when using a valid appservice token, and it can
only ping the appservice associated with the token. If the token or appservice
ID in the path is wrong, the server may return `M_FORBIDDEN`. However,
implementations and future spec proposals may extend what kinds of pings are
allowed.

#### Response
If the ping request returned successfully, the endpoint returns HTTP 200. The
response body has a `duration` field containing the ping request roundtrip time
as milliseconds.

If the request fails, the endpoint returns a standard error response with
`errcode`s and HTTP status codes as specified below:

* If the appservice doesn't have a URL configured, `M_URL_NOT_SET` and HTTP 400.
* For non-2xx responses, `M_BAD_STATUS` and HTTP 502. Additionally, the response
  may include `status` (integer) and `body` (string) fields containing the HTTP
  status code and response body text respectively to aid with debugging.
* For connection timeouts, `M_CONNECTION_TIMEOUT` and HTTP 504.
* For other connection errors, `M_CONNECTION_FAILED` and HTTP 502.
  It is recommended to put a more detailed explanation in the `error` field.

## Alternatives

* The ping could make an empty `/transactions` request instead of adding a new
  ping endpoint. A new endpoint was found to be cleaner while implementing, and
  there didn't seem to be any significant benefits to reusing transactions.
* Appservices could be switched to using websockets instead of the server
  pushing events. This option is already used by some bridges, but implementing
  websocket support on the homeserver side is much more complicated than a
  simple ping endpoint.

## Unstable prefix
The endpoints can be implemented as `/_matrix/app/unstable/fi.mau.msc2659/ping`
and `/_matrix/client/unstable/fi.mau.msc2659/appservice/{appserviceId}/ping`.
Error codes can use `FI.MAU.MSC2659_` instead of `M_` as the prefix.
