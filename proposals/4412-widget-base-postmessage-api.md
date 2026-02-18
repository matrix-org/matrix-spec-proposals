# MSC4412: Widget Base PostMessage API

This is an early draft of an MSC to replace the existing attempts to specify the Widget API
(https://github.com/matrix-org/matrix-spec-proposals/issues/3803).

Context:
 * [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411): Made in tandem with this MSC
 * https://github.com/matrix-org/matrix-spec-proposals/pull/2871
 * https://github.com/matrix-org/matrix-spec-proposals/pull/2974
 * https://github.com/matrix-org/matrix-spec-proposals/pull/2762 - widget sending matrix events to a room
 * https://github.com/matrix-org/matrix-spec-proposals/issues/3803 / https://docs.google.com/document/d/1uPF7XWY_dXTKVKV7jZQ2KmsI19wn9-kFRgQ1tFQP7wQ/edit?tab=t.0#heading=h.9rn9lt6ctkgi - The "v2" widget API

This MSC just defines the negotiation between Matrix Client ("Host") and Widget: how the widget loads and
sets itself up to communicate with the Host (the "postMessage API").

It also proposes removing some unnecessary fields from the Widget postMessage API.

## Proposal

 * Spec the request-response pattern over PostMessage
   For requests:
     * The Host receives a postmessage from the widget's 'Window' object (ie. [source](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage#source) is the Window object that the Host contained for the widget - it must check the `source` and not the origin as multiple widgets may be hosted on the same origin. However, both Host and Widget 
 * Formatting for requests and response
   ```json5
   {
     source: `widget` or `host` // we think this is necessary because of how mobile clients inject JS into the widget itself to send postMessages to itself, but this makes me wonder if one of them could lie about this to confuse the other?
     requestId: "1234",
     action: "xxx", // defines the type of 'data'
     // [either]:
     data: { [arbitrary object] }
     // [or]:
     response: { [arbitrary object] }
   }
   ```
   That is, we remove:
     * widgetId: Widget IDs are useful at the room level as an identifier for the state event and potentially to the Host to tell its widgets apart, but a widget should not need to care about what its own ID is (keep temporarily in element web for backwards compat).
     * api: We do need to know the direction as it's not always implicit (because of mobile js injection fun) but renamed to 'source'). `widget` === `fromWidget`, `host` === `toWidget`.
     * request: From responses, ie. don't repeat the request back in responses, it's not necessary.

![](https://github.com/matrix-org/matrix-spec-proposals/raw/9d689ab2d960b416eed3ef1abe6feac6c7ae56b7/proposals/images/4412-widget-base-postmessage-api_host-widget-flow.png)

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

### Backwards compat
TODO: Work out what the transition path is, what we can remove and when.

### Fundamental Actions
This MSC specifies only `content_loaded` and `supported_api_versions`: the "fundamental actions" (the ones all widgets
will need to use). Any other requests / responses are defined in separate MSCs.

#### `supported_api_versions`
 * Can be sent both from Host and Widget
 * The first postMessage sent by the widget
 * Establishes what widget API versions the host supports
 * Everything else is the widget requesting specific features (via capabilities)
 * Request is an empty object
 * Response is the versions that the host supports

#### `content_loaded`
 * From widget
 * Sent once the widget is ready to be displayed
 * Useful for when the widget wants to do some work `eg. asking the client what theme / language it should use)
   before displaying (but these are defined in other MSCs).
 * If (and only if) `usesWidgetAPI` param is in the widget's state event, the Host shows a spinner in place of the widget until it receives this.
   This replaces `waitForIFrameLoaded`, hopefully being less confusing.

#### Capability Negotiation
Any other widget actions can be introduced via capabilities, defined in another MSC. They're activated and deactivated by the Widget sending a
capabilities request. Can be at any time, before or after `content_loaded`. Capability negotiation was previously initiated by the Host so we will
need to think about backwards compat here.

 * [https://github.com/matrix-org/matrix-spec-proposals/pull/2762](MSC2762: Allowing widgets to send/receive events)
 * [https://github.com/matrix-org/matrix-spec-proposals/pull/3817](MSC3817: Allow widgets to create rooms)

#### Other transports
This just defines the PostMessage API and nothing else, but other transports could absolutely exist. Widgets will only ever need to speak PostMessage API though: any others would be bridged to PostMessage API as an adapter to the Widget, but these would likely be implementation specific to the Host.

All other messages are within other capabilities and are defined in other MSCs.

### Naming
 * actions are always `snake_case` (we're not changing them, not worth it)

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
