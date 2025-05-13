# MSC2762: Allowing widgets to send/receive events

[MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236) originally specified a Widget API
which supports widgets being able to receive specified events from the client, and for widgets to
be able to send more than stickers.

Sticker support is already specified for widgets, though support for text and image events has been
excluded from the initial specification, as has MSC1236's event receiving support. These components
have been excluded from the specification due to lack of documentation and lack of reference
implementation to influence the spec writing process.

This proposal aims to bring the functionality originally proposed by MSC1236 into the widget
specification with the accuracy and implementation validation required by modern MSCs. Additionally,
this MSC explores options for widgets being able to see events/state for rooms in which they aren't
operating directly. An example usecase of this is a calendar system built on top of Matrix where a
calendar view might belong to a room but needs information from "calendar event rooms". The widget
would therefore need to query state from these other rooms.

## Prerequisite background

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

For a bit of background, stickers are gated by an `m.sticker` capability and have a `m.sticker`
action on the `fromWidget` API. If the widget was granted the capability and sent a valid request
to the client, the client would send an `m.sticker` event to the currently viewed room as the
user. This is all a bit confusing due to the naming of all the identifiers, but the principle
is that there's prior art for sending events from widgets.

## Proposal (sending events from widgets)

As mentioned above in the prerequisite background, sticker messages can currently be sent over the
Widget API but other events are not possible. To facilitate sending other event types to the room,
some new capabilities are introduced to allow clients to easily differentiate between custom
capabilities and custom event types (using the `m.sticker` convention could be confusing between a
capability of `com.example.event` and an event type of the same name).

The new capabilities are:

* `m.send.event:<event type>` (eg: `m.send.event:m.room.message`) - Used for sending non-state events of
  a given type.
* `m.send.state_event:<event type>` (eg: `m.send.state_event:m.room.topic`) - Used for sending state
  events of a given type.

Being able to send other kinds of events (EDUs, account data, etc) is not currently proposed.

Clients SHOULD automatically deny `m.send.event` and `m.send.state_event` capability requests for
known event types which do not match the descriptor. For example, `m.send.event:m.room.topic` should
be denied, as should `m.send.state_event:m.room.message`.

As with capabilities negotiation already, the user SHOULD be prompted to approve these capabilities
if the widget requests them.

State events can have their capabilities requested against specific state keys as well, helping the
client limit its exposure to the room's history. This is done by appending a `#` and the state key
the capability should be against. For example, `m.send.state_event:m.room.name#` will represent an
`m.room.name` state event with an empty state key whereas `m.send.state_event:m.room.name#test` will
be an `m.room.name` state event still, though with `test` as the state key. Clients should only split
on the first `#`, so `m.room.name##test` becomes an event type of `m.room.name` and state key of `#test`.

To get around an issue where widgets would not be able to request an event type with `#` in it (because
it'll be seen as a state key), widgets can use a `\` character to escape the `#`. For example,
`org.example.\#test#hello` would be parsed as an event type of `org.example.#test` with state key `hello`.
Clients should be careful to parse `\\#` as `\#` (single escape).

`m.room.message` is the only non-state event which also makes use of this `#` system, though targeting
the `msgtype` of a `m.room.message` event instead. All the same rules apply as they do to state events,
except instead to `msgtype`. This ensures that widgets cannot interfere with encryption verification.
It is expected that most widgets looking to use this functionality will request the following:

* `m.send.event:m.room.message#m.notice`
* `m.send.event:m.room.message#m.text`
* `m.send.event:m.room.message#m.emote`

Other non-state event types with `#` in them do not get parsed in any special way, and do not need escaping.

To actually send the event, widgets would use a new `fromWidget` request with action `send_event`
which takes the following shape:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_event",
  "data": {
    "state_key": "",
    "type": "m.room.topic",
    "content": {
      "topic": "Hello world!"
    }
  }
}
```

Under `data`, the `state_key` is omitted if the widget is not sending a state event. The other
properties of `data` are required.

The client is responsible for encrypting the event before sending, if required by the room. The widget
should not need to be made aware of encryption or have to encrypt events.

The widget can add an additional `room_id` property to the `data` object if it would like to target
a specific room. This requires that the widget be approved for sending to that room, which is dicussed
later in this document.

If the widget did not get approved for the capability/capabilities required to send the event, the
client MUST send an error response (as required currently by the capabilities system for widgets). If
the widget has permission to send to the room, defaulting to whichever room the user is currently
viewing, the client MUST try to send the event to that room.

The client SHOULD NOT modify the `type`, `state_key`, or `content` of the request unless required for
encryption. The widget is responsible for producing valid events - the client MUST pass through any
errors, such as permission errors, to the widget using the standard error response in the Widget API.

For added clarity, the client picks either the `/send` or `/state` endpoint to use on the homeserver
depending on the presence of a `state_key` in the request data. The client then forms a request using
the `type`, `state_key`, and `content` by matching those against the endpoint's parameters, after
encryption if required.

If the event is successfully sent by the client, the client sends the following response:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_event",
  "data": {
    "state_key": "",
    "type": "m.room.topic",
    "content": {
      "topic": "Hello world!"
    }
  },
  "response": {
    "room_id": "!room:example.org",
    "event_id": "$example"
  }
}
```

*Note: Widget API responses are a clone of the request with an added `response` field.*

Both fields of the `response` are required and represent the room ID in which the event was sent,
and the event ID of that event.

With this new approach, the `m.sticker` capability and associated action are deprecated in favour of
this MSC. If this proposal is able to land in the specification before the widgets spec has a first
release, the `m.sticker` approach described in the prerequisite background section is not to be
included in the release (existing clients may still support it for legacy purposes).

### Special case: Redactions

Due to the `redacts` key being at the top level, [at least for now](https://github.com/matrix-org/matrix-doc/pull/2174),
clients should interpret a `redacts` in the content for `m.room.redaction` events as needing to call
the [`/redact` endpoint](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-redact-eventid-txnid)
on behalf of the widget.

## Proposal (receiving events in a widget)

In addition to being able to send events into the room, some widgets have an interest in reacting
to particular events that appear in the room. Using a similar approach to the sending of events,
new capabilities matching `m.receive.event:<event type>` and `m.receive.state_event:<event type>`
are introduced, with the same formatting requirements as the `m.send.event` and `m.send.state_event`
capabilities above (ie: `m.receive.event:m.room.message#m.text`).

For each event type requested and approved, the client sends a `toWidget` request with action
`send_event` to the widget, with the `data` being the event itself. For example:

```json
{
  "api": "toWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "send_event",
  "data": {
    "type": "m.room.topic",
    "sender": "@alice:example.org",
    "event_id": "$example",
    "room_id": "!room:example.org",
    "state_key": "",
    "origin_server_ts": 1574383781154,
    "content": {
      "topic": "Hello world!"
    },
    "unsigned": {
      "age": 12345
    }
  }
}
```

The widget acknowledges receipt of this request with an empty `response` object.

The client SHOULD only send events which were received by the client *after* the session has been
established with the widget (after the widget's capabilities are negotiated). Clients are expected
to apply the same semantics as the send event capabilities: widgets don't receive `m.emote` msgtypes
unless they asked for it (and were approved), and they receive *decrypted* events.

Note that the client should also be sending the widget any events in rooms where the widget is permitted
to receive events from. The exact details of these permissions are covered later in this document.

## Proposal (receiving room state in a widget)

When a widget is approved to receive some state events, the client begins syncing all room state
entries matching the capabilities in rooms where the widget is permitted to receive events. It
communicates the current state by sending a `toWidget` request with action `update_state`.

```json
{
  "api": "toWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "update_state",
  "data": {
    "state": [
      {
        "type": "m.room.topic",
        "sender": "@alice:example.org",
        "event_id": "$example",
        "room_id": "!room:example.org",
        "state_key": "",
        "origin_server_ts": 1574383781154,
        "content": {
          "topic": "Hello world!"
        },
        "unsigned": {
          "age": 12345
        }
      }
    ]
  }
}
```

`data.state` is an array of state events representing the current values of the room state for each
(`room_id`, `type`, `state_key`) tuple. The widget acknowledges receipt of this request with an
empty `response` object.

Whenever a widget is granted the ability to receive some room state (through a capability
negotiation or renegotiation), the widget may wait upon the next `update_state` action to know when
the requested room state has finished loading. Therefore, if all new room state entries that the
widget may receive are empty, the client must send an `update_state` action with an empty
`data.state` array.

The client continues sending `update_state` actions whenever it observes a change in the relevant
room state. Each action only has to mention the events that changed.

## Proposal (reading events in a widget)

Widgets can also read the events they were approved to receive on demand with the following `fromWidget`
API action:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "read_events",
  "data": {
    "state_key": "",
    "type": "m.room.topic",
    "limit": 25
  }
}
```

When no `state_key` is present, the client will respond with message-like events (i.e. non-state
events) matching the event type.

When a `state_key` is present, the client will respond with state events matching that state key. If
`state_key` is instead a boolean `true`, the client will respond with state events of the given type
with any state key.

For clarity, the state events returned should *not* be understood to represent the current state of
the room. Rather, they are simply events from the room's timeline that match the requested filter,
and may or may not belong to the resolved room state. Multiple events may be returned, even when
requesting a specific state key.

To support the ability to read particular msgtypes, the widget can specify a `msgtype` in place of the
`state_key` for `m.room.message` requests.

The `type` is simply the event type to go searching for.

The `limit` is the number of events the widget is looking for. The client can arbitrarily decide to
return less than this limit, though should never return more than the limit. For example, a client
may decide that for privacy reasons a widget can only ever see the last 5 room messages - even though
the widget requested 25, it will only ever get 5 maximum back. When `limit` is not present it is
assumed that the widget wants as many events as the client will give it. When negative, the client
can reject the request with an error.

There is no recommended maximum `limit`, though clients will want to consider local limitations in
being able to send events. Web clients, for example, may be more able to send *every* event it knows
about. The default assumption is that the client will send over as much as possible as an upper limit.

The client is not required to backfill (use the `/messages` endpoint) to get more events for the
widget, and is able to return less than the requested amount of events.

An optional `room_ids` property may also be added to the `data` object by the widget, indicating which
room(s) to listen for events in. This is either an array of room IDs, undefined, or the special string
`"*"` to denote "any room in which the widget has permission for reading that event" (covered later).
When undefined, the client should send events sent in the user's currently viewed room only.

The client's response would look like so (note that because of how Widget API actions work, the request
itself is repeated in the response - the actual response from the client is held within the `response`
object):

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "read_events",
  "data": {
    "state_key": "",
    "type": "m.room.topic",
    "limit": 25
  },
  "response": {
    "events": [
      {
        "type": "m.room.topic",
        "sender": "@alice:example.org",
        "event_id": "$example",
        "room_id": "!room:example.org",
        "state_key": "",
        "origin_server_ts": 1574383781154,
        "content": {
          "topic": "Hello world!"
        },
        "unsigned": {
          "age": 12345
        }
      }
    ]
  }
}
```

The `events` array is simply the array of events requested. When no matching events are found, this
array must be defined but can be empty.

## Proposal (accessing other rooms)

As mentioned earlier in this MSC, widgets are typically limited to the room in which the user is currently
viewing - they cannot typically reach out into other rooms or see what other rooms are out there. This
has limitations on certain kinds of widgets which rely on room structures to store data outside of a
single canonical room, however.

To complement the send/receive event capabilities, a single capability is introduced to access the timelines
of other rooms: `m.timeline:<Room ID>`. The `<Room ID>` can either be an actual room ID, or a `*` to denote
all joined or invited rooms the client is able to see, current and future. The widget can limit its exposure
by simply requesting highly scoped send/receive capabilities to accompany the timeline capability.

Do note that a widget does not need to request capabilities for all rooms if it only ever interacts with the
user's currently viewed room. Widgets such as stickerpickers will not need to request timeline capabilities
because they'll always send events to the user's currently viewed room, and the client will let them do that
without special room timeline permissions.

There is no Widget API action exposed for listing the user's invited/joined rooms: the widget can request
permission to receive the `m.room.create` state entries of rooms and learn about them that way. Clients
should be aware of this trick and describe the situation appropriately to users.

## Alternatives

Widgets could be powered by a bot or some sort of backend which allows them to filter the room state
and timeline themselves, however this can be a large amount of infrastructure for a widget to maintain
and the user experience is not as great. The client already has most of the information a widget would
need, and trying to interact through a bot would generally mean slower response times or technical
challenges on the part of the widget developer.

## Security considerations

Because the widget can implicitly decrypt room history, it is absolutely imperative that clients
prompt for permission to use these capabilities even though the capabilities negotation does not
require this to be done. Clients which approve the capabilities proposed by this MSC without
asking the user first are strongly frowned upon. There are very few use cases where not asking for
the user's permission is valid.

This MSC allows widgets to arbitrarily read history from a room without the user necessarily knowing.
Clients should apply strict limits to the number of events they are willing to provide to widgets
and ensure that users are prompted to explicitly approve the permissions requested, like in MSC2762.

Clients may also wish to consider putting iconography next to room messages when a widget reads them.

This MSC allows widgets to arbitrarily access/modify history in, at worst, all of the user's rooms.
Clients should apply strict limits or checks to ensure the user understands what the widget is trying
to do and isn't unreasonably accessing the user's account. For example, a large warning saying that
a room-based widget is trying to access messages in *all rooms* might be suitable. Another approach
might be to simply limit the number of rooms a widget can access, requiring the widget to know what
room IDs it specifically wants (ie: denying the `*` request on behalf of the user).

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

* Use `org.matrix.msc2762.` in place of `m.` in all new identifiers of this MSC.
* Only call/support the `action`s if an API version of `org.matrix.msc2762` is advertised.
