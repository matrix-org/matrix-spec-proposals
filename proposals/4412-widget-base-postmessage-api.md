# MSC4412: Matrix apps API

This is an early draft of an MSC to replace the existing attempts to specify the Widget API
(https://github.com/matrix-org/matrix-spec-proposals/issues/3803).

Context:
 * [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411): Made in tandem with this MSC
 * https://github.com/matrix-org/matrix-spec-proposals/pull/2871
 * https://github.com/matrix-org/matrix-spec-proposals/pull/2974
 * https://github.com/matrix-org/matrix-spec-proposals/pull/2762 - widget sending matrix events to a room
 * https://github.com/matrix-org/matrix-spec-proposals/issues/3803 / https://docs.google.com/document/d/1uPF7XWY_dXTKVKV7jZQ2KmsI19wn9-kFRgQ1tFQP7wQ/edit?tab=t.0#heading=h.9rn9lt6ctkgi - The "v2" widget API

This MSC defines the negotiation between Matrix Client ("Host") and Widget: how the widget loads and
sets itself up to communicate with the Host.

There can be different kinds of transports using the JSON based api specified in this MSC.
This MSC uses the api for the widget specified in [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411) which are by nature IFrames
hence postMessage is used.

The proposed role and motivation for the apps-API is the following.
Matrix is moving into the following direction:
 - less metadata on the server
 - more complexity on the client
 - more encryption
 - caching and indexing events on the client

 Those directions make a proper matrix client harder and harder to implement.
 Building a full client: login, encryption, event-cache, key backup... becomes more chellanging and a there is more trust in the software running it.

 With the simplification of the client-server api the apps-API tries to make developing higher level matrix software easier.
 It can be though of as a event-cache client api. Where most of the heavy lifting has already happened.

 This serves usecases like: Build a niche application (for example a fitness tracker, expenses tool, integration into specific hardware(xray scan)...) integrated in matrix
 but not requiring users to log into a custom matrix client.
 
## Proposal

The widget and the host will communicate over JSON.

The communication is using a request response pattern.
Each json object sent from or to the widget is called an action and has the following format:

```json5
{
  source: `widget` | `host`
  action: "xxx",
  requestId: "1234",
  request: { [arbitrary object] }
  version: "v1",
}
```

```json5
{
  source: `widget` | `host`
  action: "xxx",
  requestId: "1234",
  response: { [arbitrary object] },
  version: "v1",
}
```
This defines four possible postMessage types:
  - a toWidget request as
    - source: host window
    - `message.response === undefined` and `message.data !=== undefined`
  - a toWidget response as
    - source: widget window
    - `message.response !== undefined` and message data can be missing or undefined (its the implementation choice. Its helpful for debugging but not required)
  - a fromWidget request as
    - source: widget window
    - `message.response === undefined` and `message.data !=== undefined`
  - a fromWidget response as
    - source: host window
    - `message.response !== undefined` and message data can be missing or undefined (its the implementation choice. Its helpful for debugging but not required)

The requestId needs to be a uuid v4 (this is the version used by other parts of the spec).
The action combined with the source defines the type of the request data and the response data.
Examples could be:
 - `action`: `send_event` and `source`:`widget`
   - This is a request from the widget to ask the host to send an event to the matrix room
 - `action`: `send_event` and `source`:`host`
   - This is an action sent from the host to the widget containing an event that the host received from the homeserver in the room.

Actions do not need to be symmetric (The list of possible actions for source: `host` do not be the same as `widget`)

Every time the action is sent (defined by `source` and `action`) the other side has to send a response. Even if its just an ack (`response: {}`).
Consequently there are always EXACTLY two JSON objects sent with the same `requestId`. (one from the `host` and one from the `widget`)



### Slow actions
Actions are expected to be responsed quickly. All computation on the widget and host between request and response should be synced.

In some cases async operations are needed. (user interaction for capabilities/permissions)
This is expected to be done with two seperate actions.
For example `ask_user_sth` with source `widget` will immediatly get an ack. Then the host will do the user action.
After the user is done, it will send a new action `ask_user_sth_notify` with source `host` which the widget will immediatly ack.

Compared to the currently implemented widget api we remove:
  * widgetId: Widget IDs are useful at the room level as an identifier for the state event and potentially to the Host to tell its widgets apart, but a widget should not need to care about what its own ID is (keep temporarily in element web for backwards compat).
  * api: We do need to know the direction as it's not always implicit (because of mobile js injection fun) but renamed to 'source'). `widget` === `fromWidget`, `host` === `toWidget`.
  * request: From responses, ie. don't repeat the request back in responses, it's not necessary.

## Transport
In this MSC we introduce the postMessage transport. Future MSCs might want to introduce other transports.
 * Spec the request-response pattern over PostMessage
   For requests:
     * The Host receives a postmessage from the widget's 'Window' object (ie. [`source`](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage#source) and only sends postmessages to dedicated widgets (no `*` target is allowed)
     * Matching a request-respone with the correct widget uses fields that cannot be faked:
       * The host must check the [`source`](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage#source) and not the origin as multiple widgets may be hosted on the same origin. (makes sure widgetA does not impersonate widgetB)
       * The host must send a request-response only to the widget that actually should receive it. (makes sure widgetA does not get any data intended for widgetB)
     * -> no widgetId required in the transport
 


### State Event
This MSC adds a new field to the state event from [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411)
`usesWidgetAPI`. If this field is set to `true` the host will expect and set up listeners for widget api actions.
If this field is set to `false` the host will not set up listeners for the widget api and show the IFrame immediatly.
Now `usesWidgetAPI` will ALWAYS result in the host showing a loading state until it receives the `content_loaded` action.
In other words: the `content_loaded` action from the widget is always required when a widget uses the widget api.

This replaces `waitForIFrameLoaded`, hopefully being less confusing.

The new widgetStateEvent will look as following (see [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411) for reference)
```json5
{
  ...
  content: {
    name: string
    url: string
    avatar_url?: string
    usesWidgetAPI?: boolean // DEFAULT false
  }
}
```

### Core Actions
Implementations of this MSC only require `content_loaded`, `request_capabilites` and `notify_capabilites`: the "fundamental actions" (the ones that will be sent durina all widget livetimes). Any other requests / responses are defined in separate MSCs based on capabilites.
`supported_api_versions` is intentionally dropped.

#### Remove `supported_api_versions`
In case the reader is familiar with the current unspecced implementation of widgets the following justifies why this action is not needed:
The `supported_api_versions` are redundant with the capabilities (`request_capabilites` and `notify_capabilites`).
With this proposal the following is true:
 - with the **Core Actions** there will only be `source: widget` request actions. => So the host will never sent request actions but only response actions.
 - The widget can only sent: `request_capabilites` and `content_loaded`
This implies the first action will always come from the widget.

Instead of forcing the host to support `supported_api_versions` as a minimal requirment we force the host to implement
`source:widget,action:request_capabilites` and `source:widget,action:content_loaded`.
The host responding with no allowed capabilites is equivalent to an empty `supported_api_versions` response.
The host will only start sending data to the widget if the widget requests a capability.
So the host does not need to know about what the widget supports.
Capabilites themselves are versioned. So a widget will only request capabilites which it knows about.

#### `content_loaded`
This is one of the two always allowed actions a widget can send.
 * `source: widget`
 * Sent once the widget is ready to be displayed
 * Required to be sent form the widget. Before sending this. The client will NOT show the widget.
 * Useful for when the widget wants to do some work before being displayed. eg. asking the host what theme / language it should use or fetching events. These are defined in other MSCs)
 * If (and only if) `usesWidgetAPI` param is in the widget's state event, the Host shows a spinner in place of the widget until it receives this (`content_loaded`).
 * If the widget fails to send this before a client configured timeout (recommended 10s) the client should show an error.
 * Widgets that rely on longer load processes (media library, lots of images) should implement their own loading visalization.

#### Capability Negotiation
Any other widget actions can be introduced via capabilities, defined in other MSC. They're activated and deactivated by the Widget sending a
capabilities request (`request_capability` and `notify_capability`). Can be at any time, before or after `content_loaded`.
Capability negotiation in the current unspecified widget implementation was initiated by the Host.
Backwards compatiblity is achieved by:
 - if the host receives a `supported_api_versions` action first it will send the `capability` action.
 - if the host receives a `request_capability` action first it will NOT send the `capability` action.

The `request_capability` and `notify_capability` will work as described in: // TODO merge MSC2974 into this MSC
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/2974](MSC2974: Widgets: Capabilities re-exchange)

other MSCs with context about capabilties:
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/2762](MSC2762: Allowing widgets to send/receive events)
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/3817](MSC3817: Allow widgets to create rooms)

### Backwards compatibilty (transition path)
The transition path from the unspecified current implementation can be realised as following:
 - clients (hosts) need to support the "v1" action format proposed in this PR. in parallel to the `undefined` version implementations that currently exist.
 - Based on the first action (it always starts from the widget) the client decides what implementation to use.
 - Widgets are not allowed to switch version during their lifetime.
 - Once all hosts support both versions (`undefined`) and `v1` widgets should start implementing `v1`
 - 12 month later hosts are allowed to drop the version (`undefined`) code from their implementations.

#### Other transports
This just defines the PostMessage API and nothing else, but other transports could absolutely exist. Widgets (as they are by defintion IFrame based) will only ever need to speak PostMessage API though: any clients not able to embed an IFrame can use any transport to bridge to a browser app which then uses the PostMessage API as an adapter to the Widget. This is not specified in this MSC and consider a implementaion detail for the Host Client.

This api is designed in a way so a future MSC can reuse it to expose a WebApi independent interface to write widget like native apps
that can communicate over other transports with the host client.

All other actions types are within other capabilities and are defined in other MSCs.

### Naming
 * actions are always `snake_case` for widget actions (we're not changing them, not worth it)

## Potential issues

None yet

## Alternatives

We don't add a version field to requests: this might make it more symmetrical to CS API but might
confuse things if the same action has different meanings depending on version: probably not worth the
change.

## Security considerations

Widgets and Host must verify where the messages are from using the 'origin' and 'source' params
of the postMessage event.

## Unstable prefix

This MSC specifies messages that are already in use in practice, so we propose to continue using
the identifiers currently in use.

## Dependencies

[MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411), although would equally work
with the current "in the wild" implementation of widgets and/or the previous specifications given in
the context section.
