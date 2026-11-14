# MSC4412: Matrix apps API

This MSC specifies the base of the widget API: the format of the messages ("actions") a widget and
the Matrix client embedding it (the "host") exchange, the transport they are sent over, and how a
widget negotiates capabilities with the host. All further functionality is defined by other MSCs on
top of this one, using capabilities.

It replaces the previous attempts to specify the widget API
([#3803](https://github.com/matrix-org/matrix-spec-proposals/issues/3803)).

Related work:
 * [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411): made in tandem with
   this MSC, defines widgets themselves.
 * [MSC2871](https://github.com/matrix-org/matrix-spec-proposals/pull/2871): telling widgets which
   capabilities they were approved for.
 * [MSC2974](https://github.com/matrix-org/matrix-spec-proposals/pull/2974): capabilities
   re-exchange.
 * [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762): widgets sending and
   receiving Matrix events.
 * [The "v2" widget API draft](https://docs.google.com/document/d/1uPF7XWY_dXTKVKV7jZQ2KmsI19wn9-kFRgQ1tFQP7wQ/edit?tab=t.0#heading=h.9rn9lt6ctkgi).

## Motivation

Matrix is moving towards:
 - less metadata on the server,
 - more complexity on the client,
 - more encryption,
 - caching and indexing events on the client.

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
 * `response`: the response data. An object is a response if and only if this property is present.

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

Action names are always `snake_case` (as in the existing widget implementations; changing this is
not worth it) and should start with a verb. The recommended verbs are:
 - host -> widget: `update`, `forward`.
 - widget -> host: `send`, `request`.

### Action timeouts

Actions are expected to be answered quickly: everything the widget or the host does between
receiving a request and sending the response should be synchronous.

If a response takes longer than 10 seconds, the communication should be considered stalled and the
request treated as failed.

Longer, asynchronous operations (for example user interaction to approve capabilities) are
modelled as two separate actions. For example, a `request_something` action with `source: "widget"` is
acked immediately. The host then performs the user interaction. Once the user is done, the host
sends a new `update_something` action with `source: "host"`, which the widget acks immediately.

### Transport

Actions are sent using
[`window.postMessage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage).
This is the only transport specified by this MSC.

Widgets are by definition web content embedded in an iframe
([MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411)). `postMessage` is the
mechanism the web platform provides for communication between an embedding window and a
(cross-origin) iframe. It needs no additional setup or connection and lets the receiver identify the
sending window in a way that cannot be faked. A widget therefore only ever needs to implement the
`postMessage` transport. (A client might bridge to the widget's `postMessage` communication via a
different transport as an implementation detail, for example:
app <-`https`-> widget web wrapper <-`postMessage`-> widget.)

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

### Capabilities

Capabilities are the permission system of the widget API. Every action other than the
[core actions](#core-actions) is defined by another MSC and requires a capability:

 * A widget MUST NOT send an action, and a host MUST NOT act on it, unless the host has granted the
   corresponding capability.
 * A host MUST NOT send an action to a widget unless it has granted the corresponding capability.

The widget asks for capabilities with [`request_capabilities`](#request_capabilities-widget---host)
and the host announces the granted ones with
[`update_capabilities`](#update_capabilities-host---widget). This can happen at any time, before or
after `content_loaded`.

#### Capability format

Capabilities are strings that follow these principles:
 - **Every capability maps to exactly one action.** Actions have only one direction, so a pair of
   a host -> widget and a widget -> host action needs two capabilities.
 - **One action can have multiple capabilities.** They are told apart by the **modifier** and the
   **capability data**.
 - **Every capability reads as a sentence.** A capability
   `<source>:<namespace>.<action>.<modifier>:<capability_data>` reads: "the `host` will send / the
   `widget` is allowed to send `action` actions of the variant `modifier`, constrained to
   `capability_data`".

```
capability      = source ":" namespace "." action [ "." modifier ] [ ":" capability_data ]

source          = "widget"               ; the widget sends this action (a request)
                / "host"                 ; the host sends this action (a subscription)
namespace       = "m"                    ; stable
                / "org.matrix.mscXXXX"   ; unstable prefix of the MSC that defines the action
action          = the name of the action, for example "send_event", "read_events", "forward_event"
modifier        = a variant of the action, taken from a fixed list defined together with the action.
                  A descriptive word, for example "state", "timeline", "delayed", "sticky", "room".
                  Actions with only one variant omit the modifier.
capability_data = additional constraints that cannot be expressed as a fixed list. Each action (or
                  each of its modifiers) defines how its capability_data is formatted and
                  interpreted. Existing examples are event types ("m.room.message#m.text") and
                  room IDs ("!roomid:server.org").
```

`source`, `action` and `modifier` are clearly enumerated strings and do not contain `.` or `:`.
The `capability_data` is everything after the second `:` and can contain any character,
including `.` and `:`.

Examples:
 - `host:m.forward_event.timeline:m.room.message#m.text`: "the `host` will send `forward_event`
   actions of the variant `timeline`, constrained to `m.room.message#m.text`".
 - `widget:m.send_to_device:m.call.encryption`: "the `widget` is allowed to send `send_to_device`
   actions, constrained to `m.call.encryption`". `send_to_device` has only one variant, so there is
   no modifier.

#### Evolving actions

The capabilities make it possible to iterate on an action while staying backwards
compatible. The namespace is part of what identifies an action: the same action name under two
different prefixes (for example `m.` and `org.matrix.mscXXXX.`) are two independent actions, and
each can define its own behavior, modifiers and its own `capability_data` format. A new iteration
of an action can therefore be introduced under a new prefix next to the existing one:

 * A widget only requests the capabilities it knows about. It can request the capabilities for
   several iterations of an action and use whichever the host grants.
 * A host only grants the capabilities it knows about. It can support several iterations of an
   action for as long as widgets rely on them.

No further version negotiation is required.

Other proposals with context about capabilities:
 * [MSC2762: Allowing widgets to send/receive events](https://github.com/matrix-org/matrix-spec-proposals/pull/2762).
 * [MSC3817: Allow widgets to create rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/3817).
 * [The capability naming proposal in the `matrix-widget-sdk`](https://github.com/toger5/matrix-widget-sdk/blob/main/docs/spec-appendix/capability-naming-proposal.md).

### Core actions

Implementations of this MSC only need to support `content_loaded`, `request_capabilities` and
`update_capabilities`. These are the fundamental actions that are used during the lifetime of every
widget and do not require a capability. All other actions are defined in separate MSCs and are
gated by [capabilities](#capabilities).

The host MUST NOT send an action before it has received the first action from the widget.

#### `content_loaded` (widget -> host)

```json5
{
  source: "widget",
  action: "content_loaded",
  requestId: "1234",
  version: "v1",
  request: {},
  // response: {}, // empty response as ack
}
```

The widget sends this action once it is ready to be displayed:

 * A widget that uses the widget API (see [State event](#state-event)) MUST send it. Until the host
   receives it, the host does not show the widget and shows a loading state (for example a spinner)
   in its place.
 * This allows the widget to do some work before being displayed, for example asking the host
   which theme or language to use, or fetching events (using actions defined in other MSCs).
 * If the widget fails to send it before a client configured timeout (10 seconds are recommended),
   the client should show an error.
 * Widgets that rely on longer load processes (a media library, lots of images) should send
   `content_loaded` early and implement their own loading visualisation.

#### `request_capabilities` (widget -> host)

```json5
{
  source: "widget",
  action: "request_capabilities",
  requestId: "1234",
  version: "v1",
  request: {
    // list of capability strings
    capabilities: [
      "widget:m.send_event.timeline:m.room.message",
      "host:m.forward_event.state:m.room.member",
    ]
  },
  // response: {}, // empty response as ack
}
```

The widget requests additional capabilities. A widget can only ever request more capabilities, only
the host can remove them.

The host acks immediately. The ack only acknowledges that the capabilities were requested, it does
not imply that any of them are granted. The host is in full control of which capabilities it
grants.

#### `update_capabilities` (host -> widget)

```json5
{
  source: "host",
  action: "update_capabilities",
  requestId: "1234",
  version: "v1",
  request: {
    // list of capability strings
    allowed: ["widget:m.send_event.timeline:m.room.message"]
  },
  // response: {}, // empty response as ack
}
```

The host tells the widget which capabilities it is granted. The host decides this in any of the
following ways:
 - The client allows some capabilities by default in specific cases.
 - The client prompts the user to allow capabilities.
 - The client remembers the capabilities that were allowed before. Clients SHOULD do this, so that
   users are not prompted again every time the widget starts.

`allowed` is always the full list of capabilities the widget currently has, not only the changes.
If the widget requests more capabilities via `request_capabilities`, the host sends an update that
contains the previously allowed capabilities and potentially the new ones. This makes it easy to
keep the capability state of both sides in sync.

### State event

This MSC adds a new property, `usesWidgetAPI`, to the content of the widget state event from
[MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411):

```json5
{
  ...
  content: {
    name: string
    url: string
    avatar_url?: string
    usesWidgetAPI?: boolean // defaults to false
  }
}
```

 * If `usesWidgetAPI` is `true`, the host sets up listeners for widget API actions and ALWAYS shows
   a loading state until it receives the `content_loaded` action. In other words: `content_loaded`
   is required from every widget that uses the widget API.
 * If `usesWidgetAPI` is `false` or missing, the host does not set up listeners for the widget API
   and shows the iframe immediately.

This replaces `waitForIFrameLoaded`, which was more confusing.

### Backwards compatibility

The transition from the current, unspecified implementation works as follows:
 - Hosts support the `v1` action format proposed in this MSC in parallel to the existing
   implementation, whose actions have no `version` property.
 - The host decides which implementation to use based on the first action it receives. The first
   action is always sent by the widget.
 - Widgets MUST NOT switch version during their lifetime.
 - Once all hosts support both versions, widgets should start implementing `v1`.
 - 12 months later, hosts are allowed to drop the implementation of the version without a `version`
   property.

## Potential issues

 * The `v1` action format is not compatible with the existing implementations, so hosts have to
   maintain two implementations during the transition (see
   [Backwards compatibility](#backwards-compatibility)).
 * A widget cannot find out whether a host supports `v1`: there is no version negotiation, and a
   host that only has the existing implementation will not answer `v1` actions. This is why
   widgets should only move to `v1` once hosts support it.

## Alternatives

### No version field

The `version` property could be left out of the actions, as in the current unspecified
implementation. A version can confuse things if the same action has different meanings depending on
the version. We keep it because it lets the host tell the action format of this MSC (`v1`) apart
from the current implementation (no `version`), which the
[transition path](#backwards-compatibility) relies on. New functionality is expected to be
introduced through capabilities rather than by bumping the version (see
[Evolving actions](#evolving-actions)).

### Other transports

The action format itself (the JSON objects, the request-response pattern and the capabilities) does
not depend on `postMessage`, so other transports could be imagined. This MSC deliberately specifies
only `postMessage`:

 * Widgets are iframe based, so they never need to speak anything else. A client that cannot embed
   an iframe directly can use any transport it likes to bridge to a browser context, which then acts
   as a `postMessage` adapter towards the widget. That bridge is an implementation detail of the
   host and does not need to be specified.
 * A future MSC could reuse the action format to expose an interface that is independent of web
   APIs, allowing widget-like native apps to communicate with the host client over another
   transport. Specifying such transports is left to those MSCs.

### Comparison with the current widget API

#### Action format

Compared to the currently implemented widget API the action format drops:
  * `widgetId`: widget IDs are useful at the room level as an identifier for the state event and
    potentially for the host to tell its widgets apart, but a widget should not need to care about
    its own ID. (Element Web keeps it temporarily for backwards compatibility.)
  * `api`: the direction still needs to be known as it is not always implicit (because of the
    JavaScript injection used on mobile), but the property is renamed to `source`.
    `widget` === `fromWidget`, `host` === `toWidget`.
  * `request` in responses: repeating the request back in responses is no longer required.

#### Capabilities

 * Capability negotiation was initiated by the host. It is now initiated by the widget.
 * `request_capabilities` and `update_capabilities` work as described in this MSC, which is a bit
   different from
   [MSC2974: Widgets: Capabilities re-exchange](https://github.com/matrix-org/matrix-spec-proposals/pull/2974).

#### Removal of `supported_api_versions`

For readers familiar with the current implementation of widgets, this explains why the
`supported_api_versions` action is no longer needed: it is redundant with the capabilities.

With this proposal:
 - The only actions a widget can send without a capability are `content_loaded` and
   `request_capabilities`.
 - The only action a host can send without a capability is `update_capabilities`, and it only does
   so after the widget has requested capabilities.

This implies that the first action always comes from the widget.

Instead of requiring the host to support `supported_api_versions`, the minimal requirement for a
host is to support `content_loaded` and `request_capabilities`. A host that does not allow any
capabilities is equivalent to a host that answers `supported_api_versions` with an empty list. The
host only starts sending data to the widget once the widget has requested a capability, so the host
does not need to know what the widget supports. Capabilities themselves can be iterated on (see
[Evolving actions](#evolving-actions)), and a widget only requests capabilities it knows about.

## Security considerations

Widgets are untrusted web content. Capabilities are the only thing that limits what a widget can do
with the user's Matrix account, so the host MUST enforce them for every action as described in
[Capabilities](#capabilities), and should only grant capabilities the user or the client's policy
has agreed to.

The host must follow the rules in the [Transport](#transport) section: it identifies widgets by the
`source` of the message event (not by `origin` alone) and never sends actions with a `targetOrigin`
of `*`. Otherwise one widget could impersonate another or receive data intended for another.

Widgets must likewise verify that the messages they receive come from their host, using the
`source` and `origin` of the message event.

## Unstable prefix

This MSC specifies messages that are already in use in practice, so we propose to continue using
the identifiers currently in use.

## Dependencies

This MSC builds on [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411) (which
at the time of writing has not yet been accepted into the spec). It would equally work with the
current "in the wild" implementation of widgets and/or the previous specifications listed under
related work.
