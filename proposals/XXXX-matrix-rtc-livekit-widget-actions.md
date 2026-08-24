# MSCXXXX: MatrixRTC widget actions for authenticated livekit realted endpoints

Widgets embedded in a room may need to join MatrixRTC sessions and call the related livekit specific CS-api endpoints
([MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)).
To do so they depend on authenticated Client-Server endpoints:

- **POST** `/_matrix/client/v1/rtc/livekit/get_token` to obtain the jwt token for the SFU
- **POST** `/_matrix/client/v1/rtc/livekit/delegate_delayed_leave` to hand the session's delayed leave
  event over to the server
  ([MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195)).

Widgets never hold an access token, so they cannot call these endpoints themselves: the hosting client
has to do it on their behalf.

## Proposal

The widget API is extended with three new `fromWidget` actions. Each action delegates exactly one
endpoint and is gated behind its own capability:

| Action | Capability | Delegated endpoint |
| --- | --- | --- |
| `rtc_livekit_get_token` | `rtc_livekit_get_token` | **POST** `/_matrix/client/v1/rtc/livekit/get_token` |
| `rtc_livekit_delegate_delayed_leave` | `rtc_livekit_delegate_delayed_leave` | **POST** `/_matrix/client/v1/rtc/livekit/delegate_delayed_leave` |

For the two actions the following rules apply:

- If the widget was not approved for the corresponding capability, the client MUST reject the request
  with an error response and MUST NOT call the endpoint.
- Otherwise the client calls the delegated endpoint, using the action's `data` verbatim as the request
  body (`data` is empty for `get_rtc_transports`, which has no body).
- On success the client forwards the endpoint's response body verbatim under `response`.
- On failure the client responds with the standard widget API `error` envelope instead. Using the
  ` matrix_api_error?: { http_status, http_headers, url, response: { errcode, error, ... } } } }` structure.
  This allows the widget to determin if this endpoint is unsupported by the HS.

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
      "jwt": "thejwt",
      "url": "wss://matrix-rtc.example.com/livekit/sfu"
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

The error response matters here in particular: it is how the widget learns that the homeserver does not
support delegated delayed leave and that the widget has to keep refreshing the delayed event itself
(heartbeat).

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
identifiers with `org.matrix.mscXXXX.`, that is `org.matrix.msc4515.get_rtc_transports`,
`org.matrix.mscXXXX.rtc_livekit_get_token` and
`org.matrix.mscXXXX.rtc_livekit_delegate_delayed_leave`. Clients and widgets should only call or support
these actions if a widget API version of `org.matrix.mscXXXX` is advertised.

## Dependencies

This MSC builds on [MSC4519](https://github.com/matrix-org/matrix-spec-proposals/pull/4519) and
[MSC4195](https://github.com/matrix-org/matrix-spec-proposals/pull/4195), neither of which has been
accepted into the spec at the time of writing.

It is also a sibling MSC to: [MSC4515](https://github.com/matrix-org/matrix-spec-proposals/pull/4515)
Also, in practice, widgets should be formally included in the spec before this MSC gets included.
