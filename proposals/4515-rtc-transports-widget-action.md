# MSC4515: RTC Transports discovery for widgets

Widgets embedded in a room may need to know which real-time communication (RTC) backends the homeserver
offers, for example to join a call.
[MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) Matrix RTC offers a way for clients
to discover the available transports through a new authenticated Client-Server endpoint, **GET**
`/_matrix/client/v1/rtc/transports`.

Given that this new endpoint is authenticated, widgets cannot access it directly: they need a new widget
action to get the information by delegating to the client.

## Proposal

The widget API is extended with one new interface to access the discovery of rtc transports. The user must
manually approve the `rtc_transports` capability before the action can be used.

To trigger the action to get the configuration, widgets will use a new fromWidget request with the action
`get_rtc_transports` which takes the following shape:

```json
{
   "api":"fromWidget",
   "widgetId":"widget-1234",
   "requestId":"req-abc",
   "action":"get_rtc_transports",
   "data":{}
}
```

If the widget did not get approved for the `rtc_transports` capability, the client MUST send an error
response (as required currently by the capabilities system for widgets).

Upon reception of the action, the hosting client should call **GET** `/_matrix/client/v1/rtc/transports`
and forward the response body verbatim to the widget under the `response` field.

**Success Response**
```json
{
   "api":"fromWidget",
   "widgetId":"widget-1234",
   "requestId":"req-abc",
   "action":"get_rtc_transports",
   "data":{},
   "response":{
      "rtc_transports":[
         {
            "type":"livekit",
            "livekit_service_url":"https://livekit-jwt.example.com"
         }
      ]
   }
}
```

The `rtc_transports` field follows the same format as
[MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143), that is:

- `rtc_transports` (required, array): Array of objects describing the transports the homeserver supports.
    - `type`: (required, string): The globally unique transport identifier. MUST follow the Common
      Namespaced Identifier Grammar but without the namespacing requirements.
    - Optionally includes further properties specific to the transport type. The concrete properties are
      defined by the transport's specification.


**Error Response**
```json
{
   "api":"fromWidget",
   "widgetId":"widget-1234",
   "requestId":"req-abc",
   "action":"get_rtc_transports",
   "data":{},
   "response":{
      "error": { "message": "Missing capability" }
   }
}
```

The `error` envelope follows the standard widget API error format. Two error cases are possible:

- **Missing capability**: the widget was not approved for the `rtc_transports` capability. The client MUST
  reject the request without calling the endpoint.
- **Upstream failure**: the delegated **GET** `/_matrix/client/v1/rtc/transports` call fails (the
  homeserver returns an error, does not implement the endpoint, or is unreachable). The client SHOULD
  surface the homeserver's `errcode` and message in the `error` envelope where available, so the widget
  can distinguish a transient failure from an unsupported homeserver.

## Potential issues

**Staleness**. This is a one-shot fetch with no push/refresh (unlike MSC3846's watch_turn_servers). If
infrastructure rotates, the widget must re-request. This is intentional: RTC transports are quite stable.

## Alternatives

Instead of adding a new capability, maybe the `get_rtc_transports` could be granted automatically if the
widget is allowed to send rtc member events. There are no other examples of such mechanism, so we choose
to keep the "one action ↔ one capability". If needed the client consent policy could merge several
capability in a single check for users.

Offer a generic `do_authenticated_api_call` action where widget could call any path via the host. This
would create a more complex consent from the user point of view ("allow widget to make calls to
`this/path` on your behalf"). Also there are precedents related to VOIP that had more high level APIs,
like [MSC3846](https://github.com/matrix-org/matrix-spec-proposals/pull/3846) TurnServers.

## Security considerations

- The widget never sees the access token — the client makes the authenticated call and returns only the
  endpoint body.

## Unstable prefix

While this MSC is not yet included in the spec, implementations should use
`org.matrix.msc4515.rtc_transports` in place of the `rtc_transports` capability identifier, and
`org.matrix.msc4515.get_rtc_transports` in place of the `get_rtc_transports` action name. Clients and
widgets should only call or support these actions if a widget API version of `org.matrix.msc4515` is
advertised.

## Dependencies

This MSC builds on [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) (which at the
time of writing have not yet been accepted into the spec).
