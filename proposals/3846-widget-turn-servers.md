# MSC3846: Allowing widgets to access TURN servers

*The following is adapted from [MSC3819](https://github.com/matrix-org/matrix-spec-proposals/pull/3819).*

Widgets (embedded HTML applications in Matrix) currently have a relatively large surface area they can use for
interacting with their attached client, primarily in the context of a room. They can send/receive
[events with MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762) and
[to-device events with MSC3819](https://github.com/matrix-org/matrix-spec-proposals/pull/3819), allowing them to
simulate an entire Matrix client in application code for specific, limited use cases.

This MSC forms part of a larger, ongoing, question about how to embed other Matrix clients into another client or room
for access. An increasingly more popular client development option is to build out an entirely new Matrix client and
want to embed that within another client (as a widget) to avoid the user needing to switch apps. To support this, we
need to consider both long term and short term impact of the changes we propose. This MSC aims closer to the short term.

A longer term solution to the problem of clients wanting to be embedded in other clients might still be widgets, though
with a system like [MSC3008](https://github.com/matrix-org/matrix-spec-proposals/pull/3008) to restrict access to the
client-server API more effectively. For this MSC's purpose though, we're aiming to cover a specific functionality of the
client-server API: providing access TURN servers.

While we could expose the entire client-server API over `postMessage` (or similar) for embedded clients to access, the
permissions model gets hairy and difficult to secure on the client side. Instead, we're exploring what it would look
like to special case what is needed for specific applications, as needed.

The specific goal of exposing TURN servers is to make it possible for widget-ized Matrix clients to implement
[MSC3401 - Native group VoIP](https://github.com/matrix-org/matrix-spec-proposals/pull/3401), when combined with the
abilities of [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/3819) and
[MSC3819](https://github.com/matrix-org/matrix-spec-proposals/pull/3819).

## Proposal

To set up calls with minimal latency and support the full-mesh group call mode of
[MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401), widgets need to be able to continuously
receive updates about the latest valid TURN server credentials, rather than requesting them once at start-up or
on-demand. Otherwise, call setup with new participants may start failing midway through a call, or suffer the latency
penalty of making a widget API call for every new participant.

To this end, we introduce a new capability, `m.turn_servers`, used for accessing TURN server credentials. When approved,
it opens up access to the following actions:

**`fromWidget` action of `watch_turn_servers`**

```json5
{
  // This is a standardized widget API request.
  "api": "fromWidget",
  "widgetId": "20220712_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "watch_turn_servers", // value defined by this proposal
  "data": {} // nothing
}
```

Upon receipt, the client begins polling for TURN servers over the client-server API (if it wasn't already). It should
queue an `update_turn_servers` action as soon as possible, and then continue to update the widget with new TURN server
data whenever the previous data expires, using further `update_turn_servers` actions.

Both the `data` and `response` fields for this action are empty:

```json5
{
  // This is a standardized widget API request.
  "api": "fromWidget",
  "widgetId": "20220712_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "watch_turn_servers",
  "data": {},
  "response": {} // nothing
}
```

If the widget was already watching, this action has no effect. If the client is for whatever reason unable to start
polling (for example if TURN access for the account is 403'd), the client sends back an error response.

**`fromWidget` action of `unwatch_turn_servers`**

```json5
{
  // This is a standardized widget API request.
  "api": "fromWidget",
  "widgetId": "20220712_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "unwatch_turn_servers", // value defined by this proposal
  "data": {} // nothing
}
```

This action tells the client to stop sending the widget TURN server updates. As with `watch_turn_servers`, the `data`
and `response` fields for this action are empty. If the widget was not already watching for TURN servers, the action has
no effect.

```json5
{
  // This is a standardized widget API request.
  "api": "fromWidget",
  "widgetId": "20220712_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "unwatch_turn_servers",
  "data": {},
  "response": {} // nothing
}
```

**`toWidget` action of `update_turn_servers`**

```json5
{
  // This is a standardized widget API request.
  "api": "toWidget",
  "widgetId": "20220712_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "update_turn_servers", // value defined by this proposal
  "data": {
    "uris": [
      "turn:turn.example.com:3478?transport=udp",
      "turn:10.20.30.40:3478?transport=tcp",
      "turns:10.20.30.40:443?transport=tcp"
    ],
    "username": "1443779631:@user:example.com",
    "password": "JlKfBy1QwLrO20385QyAtEyIv0="
  }
}
```

This action informs the widget of the current TURN server URIs and credentials provided by the homeserver. As shown, the
`data` for this action contains a list of TURN URIs, along with the username and password to use with them.

The widget acknowledges the request with an empty response object:

```json5
{
  // This is a standardized widget API request.
  "api": "toWidget",
  "widgetId": "20220712_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "update_turn_servers",
  "data": {
    "uris": [
      "turn:turn.example.com:3478?transport=udp",
      "turn:10.20.30.40:3478?transport=tcp",
      "turns:10.20.30.40:443?transport=tcp"
    ],
    "username": "1443779631:@user:example.com",
    "password": "JlKfBy1QwLrO20385QyAtEyIv0="
  },
  "response": {} // nothing
}
```

## Potential issues

For simplicity, this proposal gives the widget no way to know *when* TURN server data will expire. It is instead
intended that the client will handle the TTL returned by the homeserver opaquely, for the sole purpose of refreshing the
TURN server data when it expires. It also gives no way to inform the widget when network errors or rate limits occur
during polling, leaving it up to the client to either wait for the error to be resolved on its own, or inform the widget
in the meantime that no TURN servers are available, by sending an empty `uris` list.

## Alternatives

A simpler approach would be to expose a single from-widget action to fetch the TURN data along with a TTL, just like
what would be returned by the `/_matrix/client/v3/voip/turnServer` endpoint. However, in practice this would not make
the implementation any simpler, but instead just shift the burden of refreshing the data and handling transient errors
onto to the widget. Clients wishing to support the `m.turn_servers` capability will likely already be doing VoIP in some
form, so by placing the burden on clients to handle the polling opaquely, we enable them to reuse their existing TURN
server logic.

## Security considerations

By granting a widget access to TURN credentials, the client is entrusting the widget with the same responsibility to not
misuse the TURN server that the homeserver is entrusting to the client. So, as with other widget capabilities, the
client must either prompt the user for permission, or take appropriate measures to verify that the capability can be
safely auto-approved, such as if the widget is running code from a specific, trusted domain.

## Unstable prefix

While this MSC is not yet included in the spec, implementations should use `town.robin.msc3846.turn_servers` in place of
the `m.turn_servers` capability identifier, and only call/support the actions if a widget API version of
`town.robin.msc3846` is advertised.

## Dependencies

None, though in practice, widgets should probably be formally included in the spec before this MSC gets included.
