# MSC4412: Widget API

Matrix is moving towards less metadata on the server, more encryption, and more complexity on the
client, which caches and indexes events itself. This makes a full Matrix client (login,
encryption, event cache, key backup, ...) increasingly challenging to implement, and users have to
place more trust in the software running it.

Widgets provide a way to build shared applications on top of the federated Matrix room data.
They are a solution that avoids the security and implementation complexity problems of such apps.

A widget is a web application that is embedded in a Matrix client (the "host") and talks to Matrix
through that client instead of being a Matrix client itself. The widget API is the interface
between the two: a simpler interface than the client-server API, as the client has already done the
heavy lifting. It can be thought of as a client API on top of an event cache.

This allows niche applications (for example a fitness tracker, an expenses tool or an integration
with specific hardware such as an X-ray scanner) to integrate with Matrix without requiring users
to log into a custom (potentially less trusted) Matrix client.

This MSC specifies the base of the widget API: the format of the messages (`action`s) a widget and
its host exchange, the transport they are sent over, how errors are reported, and how a widget
negotiates capabilities with the host. All further functionality is defined by other MSCs on top of
this one, using capabilities.

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
 * [MSC3817](https://github.com/matrix-org/matrix-spec-proposals/pull/3817): widgets creating
   rooms.
 * [The capability naming proposal in the `matrix-widget-sdk`][naming].
 * [The "v2" widget API draft][v2].

[naming]: https://github.com/toger5/matrix-widget-sdk/blob/main/docs/spec-appendix/capability-naming-proposal.md
[v2]: https://docs.google.com/document/d/1uPF7XWY_dXTKVKV7jZQ2KmsI19wn9-kFRgQ1tFQP7wQ/edit?tab=t.0#heading=h.9rn9lt6ctkgi

## Proposal

### Action format

The widget and the host communicate by exchanging JSON objects called actions, using a
request-response pattern:

```json5
{
  source: "widget" | "host",
  action: "m.xxx",
  request_id: "1234",
  // in a request:
  request: { [arbitrary object] },
  // in a response:
  response: { [arbitrary object] },
}
```

 * `source`: the side that sent the request. A response carries the same `source` as its request.
 * `action`: the namespaced name of the action (see [Action naming](#action-naming)). Together with
   `source` it defines the shape of `request` and `response`.
 * `request_id`: a UUID v4 (the version used by other parts of the spec), chosen by the requester.
   The response carries the same `request_id`.
 * `request`: the request data. A response does not need to repeat it, but MAY do so (this is
   helpful for debugging).
 * `response`: the response data. An object is a response if and only if this property is present.

Every request MUST be answered with exactly one response, even if it is just an ack
(`response: {}`). Consequently, exactly two JSON objects are sent per `request_id`: one by the host
and one by the widget.

Actions are not symmetric: the set of actions with `source: "host"` does not need to match the set
with `source: "widget"`, and the same `action` can mean different things depending on `source`.
For example:
 - `action: "m.send_event"`, `source: "widget"`: the widget asks the host to send an event to the
   Matrix room.
 - `action: "m.send_event"`, `source: "host"`: the host passes the widget an event it received from
   the homeserver in the room.

### Action naming

The `action` property has the form `<namespace>.<name>`:
 * The common namespacing is used: `m` for actions that are part of the spec, and the unstable
   prefix of the defining MSC (for example `org.matrix.msc4412`) for actions that are only defined
   in an MSC. The namespace also allows iterating on actions (see
   [Evolving actions](#evolving-actions)).
 * The names use `snake_case` and do not contain `.` or `:`.

For consistency, names should start with a verb. Where one fits, it is recommended to use one of
the following verbs for actions sent by the widget (**widget** -> **host**):

| Verb      | Use it when                                                                  | Example                  |
|-----------|------------------------------------------------------------------------------|--------------------------|
| `send`    | The widget asks the host to send something Matrix related on its behalf.     | `m.send_event`           |
| `request` | The widget requests a change in the host, not necessarily related to Matrix. | `m.request_capabilities` |
| `notify`  | The widget informs the host about its own state and expects nothing back.    | `m.notify_ready`         |

Verbs for actions sent by the host (**host** -> **widget**):

| Verb      | Use it when                                                                   | Example                 |
|-----------|-------------------------------------------------------------------------------|-------------------------|
| `update`  | The host sends the current, full state of something, replacing the previous.  | `m.update_capabilities` |
| `forward` | The host passes on something that happened elsewhere, one action per event.   | `m.forward_event`       |

### Errors

If a request cannot be fulfilled, the response contains an `error` object:

```json5
{
  source: "widget",
  action: "m.send_event",
  request_id: "1234",
  response: {
    error: {
      code: "m.missing_capability",
      message: "Missing capability: widget:m.send_event.timeline:m.room.message",
    }
  },
}
```

 * A response is an error response only if `response.error` is an object.
 * `code`: a namespaced, machine readable string that identifies the kind of error. Required.
 * `message`: a human readable description intended for developers. Required. It MUST NOT be
   parsed.
 * The `error` object can contain additional properties, which are defined together with the
   `code`.

This is the format of the existing widget implementations (`response: { error: { message } }`)
extended with the `code` property.

The following error codes can be returned for every action, in both directions:

| `code`                 | Meaning                                                                       |
|------------------------|-------------------------------------------------------------------------------|
| `m.unknown_action`     | The receiver does not know or does not support the `action`.                  |
| `m.missing_capability` | The capability required for the action has not been granted.                  |
| `m.invalid_request`    | The `request` is missing required properties or contains invalid values.      |
| `m.unknown`            | The request failed for any other reason.                                      |

MSCs that define actions can define additional error codes with additional properties for their
actions. For example, an action that results in a request to the homeserver could define an error
that carries the error response of the homeserver. A receiver that does not recognise a `code` MUST
treat it like `m.unknown`.

### Action timeouts

Actions are expected to be answered quickly: between receiving a request and sending the response,
only synchronous computations should be done.

If a response takes longer than 10 seconds, the communication should be considered stalled. The
request is treated as failed. A response that arrives after that is ignored.

Longer, asynchronous operations (for example user interaction to approve capabilities) are
modelled as two separate actions that are each acked immediately, like `m.request_capabilities`
and `m.update_capabilities`.

### Transport

Actions are sent using
[`window.postMessage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage).
This is the only transport specified by this MSC.

Widgets are by definition web content embedded in an iframe
([MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411)). `postMessage` is the
mechanism the web platform provides for communication between an embedding window and a
(cross-origin) iframe. It needs no additional setup or connection and lets the receiver identify the
sending window in a way that cannot be faked. A widget therefore only ever needs to implement the
`postMessage` transport (see also [Other transports](#other-transports)).

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

Because the widget is identified by its `Window` object, no widget ID is required in the actions.

### Capabilities

Capabilities are the permission system of the widget API. Every action other than the
[core actions](#core-actions) is defined by another MSC and requires a capability:

 * A widget MUST NOT send an action, and a host MUST NOT act on it, unless the host has granted the
   corresponding capability. The host answers such an action with an `m.missing_capability`
   [error](#errors).
 * A host MUST NOT send an action to a widget unless it has granted the corresponding capability.

The widget asks for capabilities with
[`m.request_capabilities`](#mrequest_capabilities-widget---host). The host grants them, and can
take them away again, with [`m.update_capabilities`](#mupdate_capabilities-host---widget). This can
happen at any time, before or after `m.notify_ready`.

#### Capability format

Capabilities are strings that follow these principles:
 - **Every capability maps to exactly one action.** Actions have only one direction, so a pair of
   a host -> widget and a widget -> host action needs two capabilities.
 - **One action can have multiple capabilities.** They are told apart by the **modifier** and the
   **capability data**.
 - **Every capability reads as a sentence.** A capability
   `<source>:<action>.<modifier>:<capability_data>` reads: "the `host` will send / the `widget` is
   allowed to send `action` actions of the variant `modifier`, constrained to `capability_data`".

```
capability = source ":" action [ "." modifier ] [ ":" capability_data ]
```

| Part                              | Values               | Description                                                                                                         |
|-----------------------------------|----------------------|---------------------------------------------------------------------------------------------------------------------|
| `source`                          | `widget` or `host`   | Who sends the action: the `widget` (a request) or the `host` (a subscription).                                      |
| `action`                          | `<namespace>.<name>` | The value of the `action` property of the action (see [Action naming](#action-naming)).                             |
| `modifier`<br>(optional)          | A descriptive word   | Some actions have a finite set of enum cases that modify the capability. Omitted if there is only one.              |
| `capability_data`<br>(optional)   | Any string           | Additional constraints that cannot be expressed as a finite list. Its format is defined together with the modifier. |

`source`, `name` and `modifier` are clearly enumerated strings and do not contain `.` or `:`.
The `capability_data` is everything after the second `:` and can contain any character,
including `.` and `:`. Existing formats are event types (`m.room.message#m.text`) and room IDs
(`!roomid:server.org`).

Examples:
 - `host:m.forward_event.timeline:m.room.message#m.text`: "the `host` will send `m.forward_event`
   actions of the variant `timeline`, constrained to `m.room.message#m.text`".
 - `widget:m.send_to_device:m.call.encryption`: "the `widget` is allowed to send `m.send_to_device`
   actions, constrained to `m.call.encryption`". `m.send_to_device` has only one variant, so there
   is no modifier.

#### Evolving actions

The same name under two different namespaces (for example `m.send_event` and
`org.matrix.mscXXXX.send_event`) are two independent actions, each with its own behaviour,
modifiers and `capability_data` format. A new version/iteration of an action can therefore
be introduced under a new namespace next to the existing one:

 * A widget only requests the capabilities it knows about. It can request the capabilities for
   several iterations of an action and use whichever the host grants.
 * A host only grants the capabilities it knows about. It can support several iterations of an
   action for as long as widgets rely on them.

This is the only versioning mechanism of the widget API. The actions themselves do not carry a
version and no further version negotiation is required.

### Core actions

Implementations of this MSC only need to support `m.notify_ready`, `m.request_capabilities` and
`m.update_capabilities`. These are the fundamental actions that are used during the lifetime of
every widget and do not require a capability. All other actions are defined in separate MSCs and
are gated by [capabilities](#capabilities).

The host MUST NOT send an action before it has received the first action from the widget.

#### `m.notify_ready` (widget -> host)

The widget sends this action once it is ready to be displayed. The `request` is an empty object and
the response an empty ack.

 * A widget that uses the widget API (see [State event](#state-event)) MUST send it. The host ALWAYS
   shows a loading state in place of the widget until it has received this action.
 * This allows the widget to do work before being displayed, for example asking the host
   which theme or language to use, or fetching events (using actions defined in other MSCs).
 * The client should time out and show an error if the widget fails to send this action
   (recommended: 15 seconds).
 * Widgets should only do initial loading before sending `m.notify_ready`. For longer load
   processes (a media library, lots of images), widgets should implement their own reactive loading
   visualisation.

#### `m.request_capabilities` (widget -> host)

```json5
{
  source: "widget",
  action: "m.request_capabilities",
  request_id: "1234",
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

The widget requests initial or additional capabilities. A widget can only ever request more
capabilities; it cannot remove them. Only the host can remove capabilities.

The host acks immediately. The ack only acknowledges that the capabilities were requested; it does
not imply that any of them are granted. The host is in full control of which capabilities it
grants and when.

#### `m.update_capabilities` (host -> widget)

```json5
request: {
  // list of capability strings
  allowed: ["widget:m.send_event.timeline:m.room.message"]
}
// response: {}, // empty response as ack
```

The host tells the widget which capabilities it is granted. The host decides this in any of the
following ways:
 - The client allows some capabilities by default in specific cases.
 - The client prompts the user to allow capabilities.
 - The client remembers the capabilities that were allowed before. Clients SHOULD do this, so that
   users are not prompted again every time the widget starts.

From then on both sides MUST behave according to the list of allowed capabilities:
the widget and the host stop sending actions that are not allowed, and the host answers any action
that is not allowed with an `m.missing_capability` error.

`allowed` is always the full list of capabilities the widget currently has, not only the changes.
This makes it easy to keep the capability state of both sides in sync:

 * **Granting:** if the widget requests more capabilities via `m.request_capabilities`, the host
   sends an update that contains the previously allowed capabilities and the new ones.
 * **Relinquishing:** to remove capabilities from the widget (for example because the user revoked
   a permission), the host sends an update with a reduced `allowed` list.

### State event

This MSC adds a new property, `uses_widget_api`, to the content of the widget state event from
[MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411):

```json5
{
  ...
  content: {
    name: string
    url: string
    avatar_url?: string
    uses_widget_api?: boolean // defaults to false
  }
}
```

 * `true`: the host sets up listeners for widget API actions and waits for
   [`m.notify_ready`](#mnotify_ready-widget---host) before showing the widget.
 * `false` or missing: the host does not set up listeners and shows the iframe immediately.

This replaces `waitForIframeLoad`, which was more confusing.

### Backwards compatibility

The action format of this MSC is not compatible with the existing, unspecified widget
implementations ("legacy widgets"). The first action is always sent by the widget. It is used
to tell the format of this MSC and the legacy format apart: legacy actions have an `api` property,
the actions of this MSC have a `source` property instead. A widget MUST NOT switch between the two formats during its
lifetime.

A host can keep supporting legacy widgets in two ways:

 * **Natively:** the host keeps its existing implementation in parallel to the one of this MSC and
   picks one based on the first action it receives. This is not recommended.
 * **Using a compatibility wrapper:** the host only implements this MSC and loads legacy widgets
   through a wrapper widget that translates between the two formats.

The [`matrix-widget-sdk`](https://github.com/toger5/matrix-widget-sdk) is a companion
implementation of this MSC and MSC4411. It contains such a wrapper, the
[`widget-compat-wrapper`](https://github.com/toger5/matrix-widget-sdk/tree/main/packages/widget-compat-wrapper),
to prove that this approach works. The wrapper is a static web page that is itself a widget as
defined by this MSC. Instead of embedding a legacy widget directly, the host embeds the wrapper and
passes it the URL of the legacy widget. The wrapper embeds the legacy widget in an inner iframe and
relays the actions between the two, translating the action format and the capability negotiation.

The transition is expected to work as follows:
 - Hosts implement this MSC and keep supporting legacy widgets in one of the two ways above.
 - Once hosts support this MSC, widgets should start implementing it. A possible shortcut is to
   ship the legacy widget wrapped in the
   [`widget-compat-wrapper`](https://github.com/toger5/matrix-widget-sdk/tree/main/packages/widget-compat-wrapper).
 - 12 months later, hosts are allowed to drop the support for legacy widgets.

## Potential issues

 * Hosts have to support two action formats during the transition (see
   [Backwards compatibility](#backwards-compatibility)).
 * A widget cannot find out whether a host supports this MSC: there is no version negotiation, and
   a host that only has the existing implementation will not answer the actions of this MSC. This
   is why widgets should only move to this MSC once hosts support it.
 * A compatibility wrapper has to request the capabilities it needs for itself in addition to the
   ones of the legacy widget, so the user can be prompted twice.

## Alternatives

### A version property

Each action could carry a `version` property. It would be needed for two things, and both are
solved differently:

 * Telling the action format of this MSC apart from the legacy format: the presence of `source`
   instead of `api` is sufficient (see [Backwards compatibility](#backwards-compatibility)).
 * Iterating on actions: actions are namespaced and gated by capabilities (see
   [Evolving actions](#evolving-actions)). A version would also be confusing if the same action
   had different meanings depending on the version.

Should the envelope itself ever need an incompatible change, a `version` property can still be
introduced then, with its absence meaning the format of this MSC.

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

#### Changes

Compared to the currently implemented widget API:
  * `widgetId` is dropped: widget IDs are useful at the room level as an identifier for the state
    event and potentially for the host to tell its widgets apart, but a widget should not need to
    care about its own ID.
  * `api` is renamed to `source`: the direction still needs to be known as it is not always implicit
    (because of the JavaScript injection used on mobile). `widget` === `fromWidget`,
    `host` === `toWidget`.
  * `data` is renamed to `request`, and repeating it in responses is no longer required.
  * `requestId` is renamed to `request_id`, following the naming conventions of Matrix.
  * `action` is namespaced.
  * Error responses gain a machine readable `code`.
  * `content_loaded` is renamed to `m.notify_ready`: the old name does not start with a verb, and
    the action is about the widget being ready to be shown rather than about content being loaded.
  * Capability negotiation is initiated by the widget instead of the host, and
    `m.request_capabilities` and `m.update_capabilities` work a bit differently from
    [MSC2974: Widgets: Capabilities re-exchange](https://github.com/matrix-org/matrix-spec-proposals/pull/2974).

#### Removal of `supported_api_versions`

The `supported_api_versions` action is no longer needed, as it is redundant with the capabilities.
A host that does not allow any capabilities is equivalent to a host that answers
`supported_api_versions` with an empty list. The host only sends actions the widget has requested a
capability for, so it does not need to know what the widget supports, and a widget only requests
capabilities it knows about (see [Evolving actions](#evolving-actions)).

## Security considerations

Widgets are untrusted web content. Capabilities are the only thing that limits what a widget can do
with the user's Matrix account, so the host MUST enforce them for every action as described in
[Capabilities](#capabilities), and should only grant capabilities the user or the client's policy
has agreed to.

The host must follow the rules in the [Transport](#transport) section, otherwise one widget could
impersonate another or receive data intended for another. Widgets must likewise verify that the
messages they receive come from their host, using the `source` and `origin` of the message event.

Error messages are sent to untrusted widgets and should not contain information the widget is not
allowed to access.

A compatibility wrapper (see [Backwards compatibility](#backwards-compatibility)) sees all
communication between the host and the legacy widget it wraps and holds the capabilities on its
behalf. Hosts should therefore only use a wrapper they trust. They SHOULD bundle the wrapper they
use themselves.

## Unstable prefix

While this MSC is not part of the spec, implementations use `org.matrix.msc4412` instead of `m` as
the namespace of everything this MSC defines:

| Stable                    | Unstable                                   |
|---------------------------|--------------------------------------------|
| `m.notify_ready`          | `org.matrix.msc4412.notify_ready`          |
| `m.request_capabilities`  | `org.matrix.msc4412.request_capabilities`  |
| `m.update_capabilities`   | `org.matrix.msc4412.update_capabilities`   |
| `m.unknown_action`        | `org.matrix.msc4412.unknown_action`        |
| `m.missing_capability`    | `org.matrix.msc4412.missing_capability`    |
| `m.invalid_request`       | `org.matrix.msc4412.invalid_request`       |
| `m.unknown`               | `org.matrix.msc4412.unknown`               |

The properties of the action format (`source`, `action`, `request_id`, `request`, `response`) and
the `uses_widget_api` property of the state event are not prefixed.

Actions and capabilities defined by other MSCs use the unstable prefix of the MSC that defines
them.

## Dependencies

This MSC builds on [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411) (which
at the time of writing has not yet been accepted into the spec). It would equally work with the
current "in the wild" implementation of widgets and/or the previous specifications listed under
related work.
