# MSC4412: Matrix apps API

This MSC specifies the base of the widget API: the format of the messages ("actions") a widget and
the Matrix client embedding it (the "host") exchange, the transport they are sent over, and how a
widget negotiates capabilities with the host. All further functionality is defined by other MSCs on
top of this one, using capabilities.

It replaces the previous attempts to specify the widget API
([#3803](https://github.com/matrix-org/matrix-spec-proposals/issues/3803)).

Related work:
 * [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411): made in tandem with
   this MSC, defines widgets themselves
 * [MSC2871](https://github.com/matrix-org/matrix-spec-proposals/pull/2871)
 * [MSC2974](https://github.com/matrix-org/matrix-spec-proposals/pull/2974)
 * [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762): widgets sending Matrix
   events to a room
 * [The "v2" widget API draft](https://docs.google.com/document/d/1uPF7XWY_dXTKVKV7jZQ2KmsI19wn9-kFRgQ1tFQP7wQ/edit?tab=t.0#heading=h.9rn9lt6ctkgi)

## Motivation

Matrix is moving towards:
 - less metadata on the server
 - more complexity on the client
 - more encryption
 - caching and indexing events on the client

This makes a full Matrix client (login, encryption, event cache, key backup, ...) increasingly
challenging to implement, and users have to place more trust in the software running it.

The apps-API makes developing higher level Matrix software easier: it is a much simpler interface
than the client-server API, offered by a client that has already done the heavy lifting. It can be
thought of as a client API on top of the event cache.

This allows niche applications (for example a fitness tracker, an expenses tool or an integration
with specific hardware such as an X-ray scanner) to integrate with Matrix without requiring users
to log into a custom Matrix client.

## Proposal

### Action format

The widget and the host communicate by exchanging JSON objects called actions, using a
request-response pattern:

```json5
{
  source: "widget" | "host",
  action: "xxx",
  requestId: "1234",
  version: "v1",
  // in a request:
  request: { [arbitrary object] },
  // in a response:
  response: { [arbitrary object] },
}
```

 * `source`: the side that sent the request. A response carries the same `source` as its request.
 * `action`: the name of the action. Together with `source` it defines the shape of `request` and
   `response`.
 * `requestId`: a UUID v4 (the version used by other parts of the spec), chosen by the requester.
   The response carries the same `requestId`.
 * `version`: always `"v1"`.
 * `request`: the request data. A response does not need to repeat it, but MAY do so (this is
   helpful for debugging).
 * `response`: the response data. An object is a response if and only if this field is present.

Every request MUST be answered with exactly one response, even if it is just an ack
(`response: {}`). Consequently exactly two JSON objects are sent per `requestId`: one by the host
and one by the widget.

Actions are not symmetric: the set of actions with `source: "host"` does not need to match the set
with `source: "widget"`, and the same `action` can mean different things depending on `source`.
For example:
 - `action: "send_event"`, `source: "widget"`: the widget asks the host to send an event to the
   Matrix room.
 - `action: "send_event"`, `source: "host"`: the host passes the widget an event it received from
   the homeserver in the room.

### Action naming
Actions are always `snake_case` for widget actions (we're not changing them, not worth it)
Actions names should start with a verb.
 - `Host` -> `Widget` recommended verbs:
  - `update`
  - `forward`
- `Widget` -> `Host` recommended verbs
  - `send`
  - `request`

### Action timouts
Actions are expected to be responsed quickly. All computation on the widget and host between request and response should be synced.

If a widget api response takes longer then 10s the communication should be considered as stalled: An error should be thrown.

In some cases longer async operations are needed. (user interaction for capabilities/permissions)
This is expected to be done with two seperate actions.
For example `request_data` with source `widget` will immediatly get an ack. Then the host will do the user action.
After the user is done, it will send a new action `update_data` with source `host` which the widget will immediatly ack.

### Transport
Actions are sent using [`window.postMessage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage).
This is the only transport specified by this MSC.

Widgets are by definition web content embedded in an IFrame
([MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411)). `postMessage` is the
mechanism the web platform provides for communication between an embedding window and a
(cross-origin) IFrame. It needs no additional setup or connection, lets the receiver identify the
sending window in a way that cannot be faked. A widget therefore only ever needs to implement the
`postMessage` transport. (A client might bridget to the widget postmessage communication via a
different tranport as an implementation detail. E.g. App <-`https`-> Widget Web wrapper <-`postMessage`-> widget)

Each action (request or response) is sent as the `message` of exactly one `postMessage` call. The
following rules apply:

 * The host MUST identify the widget a message came from using the
   [`source`](https://developer.mozilla.org/en-US/docs/Web/API/MessageEvent/source) (the widget's
   `Window` object) of the message event. The `origin` alone is not sufficient, as multiple widgets
   may be hosted on the same origin. This ensures widget A cannot impersonate widget B.
 * The host MUST send each action only to the `Window` of the widget it is intended for and MUST set
   the `targetOrigin` to the widget's origin. A `targetOrigin` of `*` MUST NOT be used. This ensures
   widget A does not receive data intended for widget B.
 * A response MUST only be sent to the `Window` the corresponding request was received from.

Because the widget is identified by its `Window` object, no `widgetId` is required in the actions.

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
Implementations of this MSC only require `content_loaded`, `request_capabilities` and `update_capabilities`: the "fundamental actions" (the ones that will be sent durina all widget livetimes). Any other requests / responses are defined in separate MSCs based on capabilites.
`supported_api_versions` is intentionally dropped.

#### `content_loaded` (`Widget` -> `Host`)
```json5
{
  source: `widget`
  action: "content_loaded",
  requestId: "1234",
  request: {}, // empty object
  // response: {}, // empty response for ack
  version: "v1",
}
```

This is one of the two always allowed actions a widget can send.
 * `source: widget`
 * Sent once the widget is ready to be displayed
 * Required to be sent form the widget. Before sending this. The client will NOT show the widget.
 * Useful for when the widget wants to do some work before being displayed. eg. asking the host what theme / language it should use or fetching events. These are defined in other MSCs)
 * If (and only if) `usesWidgetAPI` param is in the widget's state event, the Host shows a spinner in place of the widget until it receives this (`content_loaded`).
 * If the widget fails to send this before a client configured timeout (recommended 10s) the client should show an error.
 * Widgets that rely on longer load processes (media library, lots of images) should implement their own loading visalization.

#### `request_capabilities` (`Widget` -> `Host`)
```json5
{
  source: `widget`
  action: "request_capabilities",
  requestId: "1234",
  request: {capabilities: ["a", "b"]}, // list of capability strings
  // response: {}, // empty response for ack
  version: "v1",
}
```
This requests additional capabilities. The widget can only request more caps (only the host can remove capabilites).
The host will ack immediately. This does not imply any capabilities are granted/allowed yet.
The host only acknowledged that they were requested but is in full power to define the list that is approved itself.

#### `update_capabilities` (`Host` -> `Widget`)
```json5
{
  source: `host`
  action: "update_capabilities",
  requestId: "1234",
  request: {allowed: ["a", "b"]}, // list of capability strings
  // response: {}, // empty response for ack
  version: "v1",
}
```
Once the host has a set of capabilities the widget should be allowed:
 - clients can decide to allow some capabilites in specific cases by default
 - clients prompted the user to allow some capabilites
 - clients SHOULD remember already allowed capabilites and grant them on widget start.
The `Host` will send a capbilities update. This is always the full list of available capabilites.
If the client request more via `request_capabilities` the host will send an upadete with the preivous allowed
and portentially the new capabilities. This makes it easy to sync the allowed cap. state between the two.

### Capabilities
Any other widget actions can be introduced via capabilities, defined in other MSC. They're activated and deactivated by the Widget sending a
capabilities request (`request_capabilities` and `update_capabilities`). Can be at any time, before or after `content_loaded`.
Capability negotiation in the current unspecified widget implementation was initiated by the Host.

A grammar is introduced for capabilties:
 - **Every capability maps clearly to one action**
   (Actions have only one direction, a `Host`->`Widget` and `Widget`->`Host` action pair needs two capabilities)
 - **One action can have multiple capabilities.** We call those different **capability modifiers**.
 - **Every capability should read as a sentence:**
   the widget has the capability: `<source>:m.<action>.<modifier>:<modifier_data>`.\
   Reads: “the widget has the capability that the `host` will send/`widget` is allowed to
   send `action` actions with the action modifier constraints `modifier` for `modifier_data`."\

   the widget has the capability: `host:m.forward_event.timeline:m.room.message#m.text`
   Reads: "the widget has the capability that the `host` will send `forward_event` actions with the action modifier constraints `timeline` for `m.room.message#m.text`."\

 #### The Schema
```
 capability   =  host/widget ":" namespace "." action "." modifier [ ":" modifier_data ]

 source        = "widget"                           ; the widget sends this action (a request)
               / "host"                             ; the host sends this action (a subscription)
 namespace     = "m"                                ; stable
               / "org.matrix.mscXXXX"               ; unstable prefix of this proposal, one for all
 action        = the action's stable name, a verb, e.g. "send_event", "read_events", "forward_event"
 modifier      = a variant (clearly defined enum) of the action, a descriptive word: "state", "timeline", "delayed", "sticky", "room"
 modifier_data = each action modifier defines its own formatting how the modifier_data is interpreted.
                 It conatins additional constraints that can be arbitrary data outside the clear modifier enums cases.
                 as of today: eventTypes:`m.room.message#m.text` and Room Ids `#roomid:server.org` are the only existing examples
```

other MSCs with context about capabilties:
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/2762](MSC2762: Allowing widgets to send/receive events)
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/3817](MSC3817: Allow widgets to create rooms)

Other context on capabilites:
 * [https://github.com/toger5/matrix-widget-sdk/blob/main/docs/spec-appendix/capability-naming-proposal.md](capability naming proposal in the `matrix-widget-sdk`)

## Potential issues

None yet

## Alternatives

### No version field
The `version` field could be left out of the actions, as in the current unspecified implementation.
A version can confuse things if the same action has different meanings depending on the version.
We keep it because it lets the host tell the action format of this MSC (`v1`) apart from the
current implementation (no `version`), which the
[transition path](#backwards-compatibilty-transition-path) relies on. New functionality is
expected to be introduced through capabilities rather than by bumping the version.

### Other transports
The action format itself (the JSON objects, the request-response pattern and the capabilities) does
not depend on `postMessage`, so other transports could be imagined. This MSC deliberately specifies
only `postMessage`:

 * Widgets are IFrame based, so they never need to speak anything else. A client that cannot embed
   an IFrame directly can use any transport it likes to bridge to a browser context, which then acts
   as a `postMessage` adapter towards the widget. That bridge is an implementation detail of the
   host and does not need to be specified.
 * A future MSC could reuse the action format to expose an interface that is independent of web
   APIs, allowing widget-like native apps to communicate with the host client over another
   transport. Specifying such transports is left to those MSCs.

### Previous widget api comparison

#### Action format
Compared to the currently implemented widget api the action format drops:
  * `widgetId`: Widget IDs are useful at the room level as an identifier for the state event and potentially to the Host to tell its widgets apart, but a widget should not need to care about what its own ID is (keep temporarily in element web for backwards compat).
  * `api`: We do need to know the direction as it's not always implicit (because of mobile js injection fun), but it is renamed to `source`. `widget` === `fromWidget`, `host` === `toWidget`.
  * `request` in responses: repeating the request back in responses is no longer required.

#### Capabilites
The `request_capabilities` and `update_capabilities` will work as described here, a bit different than the previous MSC:
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/2974](MSC2974: Widgets: Capabilities re-exchange)
#### Backwards compatibilty (transition path)
The transition path from the unspecified current implementation can be realised as following:
 - clients (hosts) need to support the "v1" action format proposed in this PR. in parallel to the `undefined` version implementations that currently exist.
 - Based on the first action (it always starts from the widget) the client decides what implementation to use.
 - Widgets are not allowed to switch version during their lifetime.
 - Once all hosts support both versions (`undefined`) and `v1` widgets should start implementing `v1`
 - 12 month later hosts are allowed to drop the version (`undefined`) code from their implementations.


#### Remove `supported_api_versions`
In case the reader is familiar with the current unspecced implementation of widgets the following justifies why this action is not needed:
The `supported_api_versions` are redundant with the capabilities (`request_capabilities` and `update_capabilities`).
With this proposal the following is true:
 - with the **Core Actions** there will only be `source: widget` request actions. => So the host will never sent request actions but only response actions.
 - The widget can only sent: `request_capabilities` and `content_loaded`
This implies the first action will always come from the widget.

Instead of forcing the host to support `supported_api_versions` as a minimal requirment we force the host to implement
`source:widget,action:request_capabilities` and `source:widget,action:content_loaded`.
The host responding with no allowed capabilites is equivalent to an empty `supported_api_versions` response.
The host will only start sending data to the widget if the widget requests a capability.
So the host does not need to know about what the widget supports.
Capabilites themselves are versioned. So a widget will only request capabilites which it knows about.

## Security considerations

The host must follow the rules in the [Transport](#transport) section: it identifies widgets by the
`source` of the message event (not by `origin` alone) and never sends actions with a `targetOrigin`
of `*`. Otherwise one widget could impersonate another or receive data intended for another.

Widgets must likewise verify that the messages they receive come from their host, using the
`source` and `origin` of the message event.

## Unstable prefix

This MSC specifies messages that are already in use in practice, so we propose to continue using
the identifiers currently in use.

## Dependencies

[MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411), although would equally work
with the current "in the wild" implementation of widgets and/or the previous specifications given in
the context section.
