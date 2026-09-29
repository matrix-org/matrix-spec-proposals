# MSC3819: Allowing widgets to send/receive to-device messages

Widgets (embedded HTML applications in Matrix) currently have a relatively large surface area
they can use for interacting with their attached client, primarily in the context of a room. They
can [send/receive events with MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762),
[navigate to rooms with MSC2931](https://github.com/matrix-org/matrix-spec-proposals/pull/2931),
and even [open dialogs with MSC2790](https://github.com/matrix-org/matrix-spec-proposals/pull/2790),
but they can't act as a whole other Matrix client just yet.

This MSC forms part of a larger, ongoing, question about how to embed other Matrix clients into another
client or room for access. An increasingly more popular client development option is to build out an
entirely new Matrix client and want to embed that within another client (as a widget) to avoid the
user needing to switch apps. To support this, we need to consider both long term and short term impact
of the changes we propose. This MSC aims closer to the short term.

A longer term solution to the problem of clients wanting to be embedded in other clients might still
be widgets, though with a system like [MSC3008](https://github.com/matrix-org/matrix-spec-proposals/pull/3008)
to restrict access to the client-server API more effectively. For this MSC's purpose though, we're
aiming to cover a specific subset of the client-server API: to-device messages.

While we could expose the entire client-server API over `postMessage` (or similar) for embedded
clients to access, the permissions model gets hairy and difficult to secure on the client side. Instead,
we're exploring what it would look like to special case what is needed for specific applications, as
needed, starting with to-device messages.

To-device messaging is described [here](https://spec.matrix.org/v1.2/client-server-api/#send-to-device-messaging)
with practical applications for widget-ized clients being implementations of
[MSC3401 - Native group VoIP](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) for now.

## Prerequisite background

*Author's note: This is copied from [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762).*

Widgets are relatively new to Matrix and so the terminology and behaviour might not be known to all
readers. This section should clarify the components of widgets that are applicable to this MSC without
going on a deep dive into widgets in general.

Widgets are embedded HTML/JS/CSS applications in a client which use the `postMessage` API to talk
to the client. This communication allows widgets to provide enhanced functionality such as sticker
pickers (when applied to a user) or performance dashboards (in rooms).

One of the first things that happens over this communication channel is a "capabilities negotiation"
where the client asks the widget what permissions it wants, and the widget replies with its ideal
set. The client then either decides or asks the user if the permissions requested are okay.

All communication over the channel is done in a simple request/response flow, using actions to
describe the request. For the capabilities negotiation, this would be the client sending the widget
a request with an `action` of `capabilities`, and the widget would respond to that request with a
response object.

The channel in which communication occurs is called a "session", where the session is "established"
after the capabilities negotiation. Sessions can only be terminated by the client.

The Widget API is split into two parts: `toWidget` (client->widget) and `fromWidget` (widget->client).
They are differentiated by where the request originates.

## Proposal

Inspired heavily from [MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762), we
introduce new capabilities for to-device messages:

* `m.send.to_device:<event type>` (eg: `m.send.to_device:m.call.invite`) - Used for sending to-device
  messages of a given type.
* `m.receive.to_device:<event type>` (eg: `m.receive.to_device:m.call.invite`) - Used for receiving
  to-device messages of a given type.

These capabilities open up access to the following respective actions, when approved:

**`fromWidget` action of `send_to_device`**

```json5
{
  // This is a standardized widget API request.
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_to_device", // value defined by this proposal
  "data": {
    // Same structure as the `/sendToDevice` HTTP API request body
    "@target:example.org": {
      "DEVICEID": { // can also be a `*` to denote "all of the user's devices"
        "example_content": "put your real message here"
      }
    }
  }
}
```

The client upon receipt of this will validate that the widget has an appropriate capability to send
the to-device message. If the widget is approved for such a capability, the client **MUST** encrypt
the message by default unless the event is already encrypted by the widget (this MSC doesn't provide
enough API surface for a widget to do this, but in future it might be possible for the widget to
gain some context of the encryption state for the client and use that to make/manage Olm sessions).
The encrypted message is then sent as requested to the users/devices using
[`/sendToDevice`](https://spec.matrix.org/v1.2/client-server-api/#put_matrixclientv3sendtodeviceeventtypetxnid).

If the widget doesn't have appropriate permission, or an error occurs anywhere along the send path,
a standardized widget error response is returned.

Under the widget API, a response to all actions is required and takes the shape of repeating the
request with an added top-level `response` field. This `response` field is empty for this action,
as shown:

```json5
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_to_device",
  "data": {
    "@target:example.org": {
      "DEVICEID": {
        "example_content": "put your real message here"
      }
    }
  },
  "response": {}
}
```

The client *should not* send a response to the action until the server has returned 200 OK itself,
which might take longer than the default widget API timeout of 10 seconds. Widgets should raise their
maximum timeout to 60 seconds or more for this action.

**`toWidget` action of `send_to_device`**

*Note*: It is common practice to name the action in favour of the direction of travel rather than try
and determine an alternative name. This does mean that there are two `send_to_device` actions: one
for widget->client and one for client->widget. This section is talking about client->widget.

After the client has decrypted all to-device messages it receives, it determines if any widgets should
be made aware of the contents within. The decrypted event type for the message is used to determine
if the widget has appropriate capability to see the message.

The client should process all to-device messages it can before sending them off to the widget. Even if
the client does process a message though, it should still send it to the appropriate widgets for
potential re-processing. This is to avoid a scenario where the host client can no longer reliably
function, such as if Olm sessions get corrupted or similar.

The client should be aware that to-device messages might be seen which the client *could* handle, but
might not have context on, such as VoIP signaling. The client should not error out if it can't locate
a matching call, for example.

The client SHOULD only send events which were received by the client *after* the session has been
established with the widget (after the widget's capabilities are negotiated).

The request itself looks as follows:

```json5
{
  // This is a standardized widget API request.
  "api": "toWidget", // note that we're sending *to* the widget here
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_to_device", // value defined by this proposal
  "data": {
    "type": "m.call.invite",
    "sender": "@source:example.org",
    "encrypted": true,
    "content": {
      // ... as required for the event schema
    }
  }
}
```

Note that the action only supports a single to-device message at a time. This is for symmetry with
[MSC2762](https://github.com/matrix-org/matrix-spec-proposals/pull/2762).

Under the widget API, a response is required from the widget. The widget simply acknowledges the request
with an empty response object:

```json5
{
  "api": "toWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_to_device",
  "data": {
    "type": "m.call.invite",
    "sender": "@source:example.org",
    "content": {
      // ... as required for the event schema
    }
  },
  "response": {}
}
```

### Passing the current device id to widgets

For the matrixRTC usecase, the widget needs to advocate which device is joining a session.
So other devices can target it for toDevice messages.
A new template variable is added to the available options for a widget URL:

- `$matrix_device_id` - The device id of the client instance which is rendering the widget.

## Potential issues

Due to lack of documentation/spec, conventions for the widget API and its security principles could
be misunderstood or confusing. This MSC attempts to overly describe these cases where they are at
risk of being a potential misunderstanding, however readers of the proposal are still encouraged to
gather as much information as they can before reviewing this proposal.

This MSC further pushes forward an idea that the `postMessage` transport for the widget API is the
way to go, however MSCs like [MSC3009](https://github.com/matrix-org/matrix-spec-proposals/pull/3009)
explore what it could mean to have a different transport mechanism. This MSC is not tied directly
to `postMessage` and is instead describing the request/responses used over the widget API - whatever
transport that might be.

## Alternatives

As discussed in the introduction of this proposal and on other MSCs, we could expose the client-server
API more generically to the widget. This causes issues where the client is either forced to parse
requests like a webserver would to validate that the widget is allowed to make the request, or
require such a generic capability that widgets would excessively request full read/write access
from the user without consideration for the impact that might have. As such, we continue to describe
special-cased actions for the widget API on a case-by-case basis.

On other related proposals there's discussion about how a bot could achieve the same function as
the proposal. While also partially true here, the intent is not to have a game or similar publishing
events into a room but rather to have a second Matrix client (for all intents and purposes) embedded
either as a room widget or account widget. A bot precludes the second client from acting on behalf
of the user who has it open.

## Security considerations

Because the widget can implicitly decrypt events, it is absolutely imperative that clients
prompt for permission to use these capabilities even though the capabilities negotiation does not
require this to be done. Strictly speaking, clients which do not prompt for confirmation from the
user are frowned upon, however given the intended usecase of VoIP signaling it is reasonable to
auto-approve some capabilities if the client can verifiably trust the widget is running safe code.
In general, verifiable trust only comes from the client locking widgets down to specific domains
or rewriting the widget URL before rendering to something the client controls.

This MSC allows widgets to access sensitive parts of the client-server API, and the encryption
module specifically. If granted permission, a widget could feasibly harvest decryption keys *in clear
text*. It is strongly encouraged that clients do not auto-approve capabilities for key exchanges
or similar. In fact, it might even be reasonable for the client to auto-deny instead.

This MSC allows a room widget to act at the account level rather than the traditional room level.
Normally these events would be scoped to the currently active room, however to-device messages are
not tied to a room. Therefore, the events are exposed as-is to the widget and can be interacted with
as such.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

* Use `org.matrix.msc3819.` in place of `m.` in all new identifiers of this MSC.
* Only call/support the `action`s if a widget API version of `org.matrix.msc3819` is advertised.
* `$org.matrix.msc3819.matrix_device_id` in place of `$matrix_device_id`.
## Dependencies

None applicable - this MSC's dependencies have either been approved or are used simply as reference
material. In practice, widgets should probably be formally in the spec before this MSC gets included.
