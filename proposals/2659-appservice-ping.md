# MSC2659: Application service ping endpoint

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

The request body contains an optional `transaction_id` string field, which
comes from the client ping request defined below.

Appservices don't need to have any special behavior on this endpoint, but they
may use the incoming request to verify that an outgoing ping actually pinged
the appservice rather than going somewhere else.

This proposal doesn't define any cases where a homeserver would call the ping
endpoint unless explicitly requested by the appservice (using the client
endpoint below). Therefore, appservices don't necessarily have to implement
this endpoint if they never call the client ping endpoint.

### `POST /_matrix/client/v1/appservice/{appserviceId}/ping`
When the endpoint is called, the homeserver makes a `/_matrix/app/v1/ping`
request to the appservice.

The request body may contain a `transaction_id` string field, which, if present,
must be passed through to the appservice `/ping` request body as-is.

This endpoint is only allowed when using a valid appservice token, and it can
only ping the appservice associated with the token. If the token or appservice
ID in the path is wrong, the server may return `M_FORBIDDEN`. However,
implementations and future spec proposals may extend what kinds of pings are
allowed.

In case the homeserver had backed off on sending transactions, it may treat a
successful ping as a sign that the appservice is up again and transactions
should be retried.

#### Response
If the ping request returned successfully, the endpoint returns HTTP 200. The
response body has a `duration_ms` field containing the `/_matrix/app/v1/ping`
request roundtrip time as milliseconds.

If the request fails, the endpoint returns a standard error response with
`errcode`s and HTTP status codes as specified below:

* If the appservice doesn't have a URL configured, `M_URL_NOT_SET` and HTTP 400.
* For non-2xx responses, `M_BAD_STATUS` and HTTP 502. Additionally, the response
  may include `status` (integer) and `body` (string) fields containing the HTTP
  status code and response body text respectively to aid with debugging.
* For connection timeouts, `M_CONNECTION_TIMEOUT` and HTTP 504.
* For other connection errors, `M_CONNECTION_FAILED` and HTTP 502.
  It is recommended to put a more detailed explanation in the `error` field.

### Example flow

1. bridge -> homeserver (request #1): `POST http://synapse:8008/_matrix/client/v1/appservice/whatsapp/ping`
   * Header `Authorization: Bearer as_token`
   * Body: `{"transaction_id": "meow"}`
2. homeserver -> bridge (request #2): `POST http://bridge:29318/_matrix/app/v1/ping`
   * Header `Authorization: Bearer hs_token`
   * Body: `{"transaction_id": "meow"}`
3. bridge -> homeserver (response to #2): 200 OK with body `{}`
4. homeserver -> bridge (response to #1): 200 OK with body `{"duration_ms": 123}`
   (123 milliseconds being the time it took for request #2 to complete).

## Alternatives

* The ping could make an empty `/transactions` request instead of adding a new
  ping endpoint. A new endpoint was found to be cleaner while implementing, and
  there didn't seem to be any significant benefits to reusing transactions.
* A `/versions` endpoint could be introduced to work for both pinging and
  checking what spec versions an appservice supports. However, it's not clear
  that a new endpoint is the best way to detect version support (a simple flag
  in the registration file may be preferable), so this MSC proposes a `/ping`
  endpoint that doesn't have other behavior.
* Appservices could be switched to using websockets instead of the server
  pushing events. This option is already used by some bridges, but implementing
  websocket support on the homeserver side is much more complicated than a
  simple ping endpoint.

## Unstable prefix
The endpoints can be implemented as `/_matrix/app/unstable/fi.mau.msc2659/ping`
and `/_matrix/client/unstable/fi.mau.msc2659/appservice/{appserviceId}/ping`.
Error codes can use `FI.MAU.MSC2659_` instead of `M_` as the prefix.

`fi.mau.msc2659` can be used as an `unstable_features` flag in `/versions` to
indicate support for the unstable prefixed endpoint. Once the MSC is approved,
`fi.mau.msc2659.stable` can be used to indicate support for the stable endpoint
until the spec release containing the endpoint is supported.
