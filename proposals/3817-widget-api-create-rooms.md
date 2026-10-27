# MSC3817: Allowing widgets to create rooms

[MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236) and (among others)
[MSC2763](https://github.com/matrix-org/matrix-spec-proposals/pull/2762) specify a Widget API that
is able to send events to the client and receive events from the client. One feature that is not yet
available is the creation of new rooms via this API. An example use case for this feature is a
calendar application that can create new Matrix rooms for every calendar event. Another is a widget
that allows the user to create breakout rooms to discuss certain topics directly from the widget.
Giving the widget this option would also give them the possibility to provide an initial state for
the room that is hard (or impossible) to add after the room has been created.

This proposal aims to bring the functionality of creating rooms into the widget specification. It
should provide the same features that the
[“Room Creation” endpoint](https://spec.matrix.org/v1.2/client-server-api/#creation) of the
Client-Server API provides.

## Proposal

Having the possibility to create new rooms would improve the capabilities of the widgets and would
fill a gap of widget room capabilities. As of now, a widget can read and write state or room events
to arbitrary rooms, but it can't be used to create these rooms.

In order to secure the user from malicious widgets, we will add a new capability that the user must
manually approve:

- `m.create_room`: Let the widget create new rooms.

This capability will enable the user to provide arbitrary events as the initial state of the room and
can also invite an arbitrary amount of users to the room. These events are not bound by the approved
capabilities of the widget, because we assume that the creator of the room should be able to have the
full control of the room during this initialization process. Thus, the `m.send.event:<event type>`
capabilities will not apply here.

To trigger the action, widgets will use a new `fromWidget` request with the action `create_room` which
takes the following shape:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "create_room",
  "data": {
    "creation_content": {
      "m.federate": false
    },
    "initial_state": [],
    "invite": [],
    "invite_3pid": [],
    "is_direct": false,
    "name": "The Grand Duke Pub",
    "power_level_content_override": {},
    "preset": "public_chat",
    "room_alias_name": "thepub",
    "room_version": "1",
    "topic": "All about happy hour",
    "visibility": "public"
  }
}
```

Under `data`, all keys are a mirrored representation of the original `/createRoom` API. This also
means that all keys are optional.

If the widget did not get approved for the capability required to send the event, the client MUST
send an error response (as required currently by the capabilities system for widgets).

The client SHOULD NOT modify the data of the request. The widget is responsible for producing valid
events - the client MUST pass through any errors, such as permission errors, to the widget using the
standard error response in the Widget API.

If the event is successfully sent by the client, the client sends the following response:

```json
{
  "api": "fromWidget",
  "widgetId": "20200827_WidgetExample",
  "requestid": "generated-id-1234",
  "action": "create_room",
  "data": {
    "creation_content": {
      "m.federate": false
    },
    "initial_state": [],
    "invite": [],
    "invite_3pid": [],
    "is_direct": false,
    "name": "The Grand Duke Pub",
    "power_level_content_override": {},
    "preset": "public_chat",
    "room_alias_name": "thepub",
    "room_version": "1",
    "topic": "All about happy hour",
    "visibility": "public"
  },
  "response": {
    "room_id": "!room:example.org"
  }
}
```

The `room_id` field of the `response` is required and represents the ID of the new room that has been
created.

## Alternatives

Widgets could be powered by a bot or some sort of backend which allows them to create new rooms,
however this can be a large amount of infrastructure for a widget to maintain. The widget is already
capable of interacting with the events that are stored in a room, so the sole purpose of the bot
would be to create new rooms.

The Widget API could limit the API surface by not permitting the widget to e.g. provide an initial
state or by providing user ids that should be invited by the server. However, this would limit the
usefulness of the API.

If [MSC3008](https://github.com/matrix-org/matrix-spec-proposals/pull/3008) goes forward, the widget
could interact with the respective API call of the Client-Server API. However, the status of the MSC
is unknown so it would be a good alternative to add this feature to the widget API.

Instead of mirroring the API surface of the Client-Server API, the widget api could use a more
specific interface as it is also available in the
[`matrix-react-sdk`](https://github.com/matrix-org/matrix-react-sdk/blob/c67b41fbde06e302e0ca296d99fbcea9f95b4a78/src/createRoom.ts#L52-L67)
and provide that in the `WidgetDriver` interface. This would enable the API to for example automatically
setup the encryption or add the `m.space.child` to a parent space room. However, the Widget API is
more independent if it doesn't rely on external logic, especially considering a potential emergence
of MSC3008. This also means that this complexity is moved to the widget itself that must implement
the logic if needed.

## Security considerations

It is important that clients prompt for permission to create rooms. It could mess with the room list
of a user, or it could also invite unwanted users to a room. This could either be a malicious bot,
or other users who are spammed with unwanted invitations. Instead of solely relying on the
`m.create_room` capability, the widget API could consider the `m.send.event:<event type>` capabilities
for all events that are provided as initial state in the API call. This could also include the
`m.send.event:m.room.member` capability to secure the `invite` list. But in order to correctly check
the capabilities, the widget would need to have the capabilities accepted for the `room_id` of the
room that is about to be created, or the widget must request timeline access to all (i.e. `"*"`)
rooms, which would be unpractical. An alternative could be to add more narrowly scoped capabilities
such as `m.create_room:invite,m.room.encryption,…`.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

- Use `org.matrix.msc3817.` in place of `m.` in all new identifiers of this MSC.
- Use `org.matrix.msc3817.create_room` in place of `create_room` for the action type in the
  `fromWidget` requests.
- Only call/support the `action`s if an API version of `org.matrix.msc3817` is advertised.
