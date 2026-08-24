# MSC4533: MatrixRTC widget actions for authenticated LiveKit related endpoints

Widgets embedded in a room may need to join MatrixRTC sessions
([MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)) over LiveKit
([MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195)). To do so they depend on two
authenticated Client-Server API endpoints:

- **POST** `/_matrix/client/v1/rtc/livekit/get_token` to obtain the JWT for the SFU.
- **POST** `/_matrix/client/v1/rtc/livekit/delegate_delayed_leave` to hand the session's delayed leave
  event over to the server.

Widgets never hold an access token, so they cannot call these endpoints themselves: the hosting client
has to do it on their behalf.

## Proposal

The widget API is extended with two new `fromWidget` actions. Each action delegates exactly one
endpoint and is gated behind its own capability:

| Action | Capability | Delegated endpoint |
| --- | --- | --- |
| `rtc_livekit_get_token` | `rtc_livekit_get_token` | **POST** `/_matrix/client/v1/rtc/livekit/get_token` |
| `rtc_livekit_delegate_delayed_leave` | `rtc_livekit_delegate_delayed_leave` | **POST** `/_matrix/client/v1/rtc/livekit/delegate_delayed_leave` |

For both actions the following rules apply:

- If the widget was not approved for the corresponding capability, the client MUST reject the request
  with an error response and MUST NOT call the endpoint.
- Otherwise the client calls the delegated endpoint, using the action's `data` verbatim as the request
  body.
- On success the client forwards the endpoint's response body verbatim under `response`.
- On failure the client responds with the standard widget API `error` envelope, that is
  `{ "error": { "message": "...", "matrix_api_error"?: { "http_status", "http_headers", "url",
  "response": { "errcode", "error" } } } }`. When the delegated call itself failed, the client MUST
  include the `matrix_api_error` details, so that the widget can determine whether the endpoint is
  unsupported by the homeserver.

### `rtc_livekit_get_token`

```json
{
   "api": "fromWidget",
   "widgetId": "widget-1234",
   "requestId": "req-abc",
   "action": "rtc_livekit_get_token",
   "data": {
      "server_name": "example.com",
      "url": "wss://livekit.example.com",
      "room_id": "!tDLCaLXijNtYcJZEey:example.com",
      "slot_id": "the_id",
      "member": {
         "id": "xyzABCDEF10123",
         "claimed_device_id": "DEVICEID"
      }
   },
   "response": {
      "jwt": "thejwt"
   }
}
```

### `rtc_livekit_delegate_delayed_leave`

```json
{
   "api": "fromWidget",
   "widgetId": "widget-1234",
   "requestId": "req-abc",
   "action": "rtc_livekit_delegate_delayed_leave",
   "data": {
      "room_id": "!tDLCaLXijNtYcJZEey:example.com",
      "slot_id": "the_id",
      "member": {
         "id": "xyzABCDEF10123",
         "claimed_device_id": "DEVICEID"
      },
      "delay_id": "1234567890"
   },
   "response": {}
}
```

The error response matters here in particular:
[MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195) defines no fallback for
homeservers that do not implement `delegate_delayed_leave`, so the widget has to detect this from the
`matrix_api_error` (an HTTP 404 with `M_UNRECOGNIZED`) and keep refreshing the delayed leave event
itself (heartbeat).

## Potential issues

## Alternatives

Instead of adding capabilities, the actions could be granted implicitly to widgets that are allowed to
send RTC member events. There is no precedent for such a mechanism, so we keep "one action ↔ one
capability". Clients are free to merge the two capabilities into a single consent prompt for users.

Offer a generic `do_authenticated_api_call` action where the widget could call any path via the host.
This would make consent much harder to reason about ("allow widget to make calls to `this/path` on your
behalf"). Precedent for high level VoIP APIs exists with
[MSC3846](https://github.com/matrix-org/matrix-spec-proposals/pull/3846) (TURN servers).

## Security considerations

- The widget never sees the access token: the client makes the authenticated call and returns only the
  endpoint body.
- The client relays `data` verbatim, so the endpoints MUST NOT rely on the caller being the client
  itself. In particular a widget can ask for a token for any `room_id`/`slot_id`, which the homeserver
  authorises against the user's actual membership as usual.

## Unstable prefix

While this MSC is not yet included in the spec, implementations should prefix all action and capability
identifiers with `org.matrix.msc4533.`, that is `org.matrix.msc4533.rtc_livekit_get_token` and
`org.matrix.msc4533.rtc_livekit_delegate_delayed_leave`. Clients and widgets should only call or support
these actions if a widget API version of `org.matrix.msc4533` is advertised.

While [MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195) is itself unstable, the
client delegates to its unstable endpoints, that is
`/_matrix/client/unstable/io.element.msc4195/rtc/livekit/get_token` and
`/_matrix/client/unstable/io.element.msc4195/rtc/livekit/delegate_delayed_leave`.

## Dependencies

This MSC builds on [MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195), which
has not been accepted into the spec at the time of writing.

It is a sibling MSC to [MSC4515](https://github.com/matrix-org/matrix-spec-proposals/pull/4515), which
delegates the RTC transports discovery endpoint in the same way.

Also, in practice, widgets should be formally included in the spec before this MSC gets included.
