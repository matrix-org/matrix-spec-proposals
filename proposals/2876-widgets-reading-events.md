# MSC2876: Allowing widgets to read events in a room

[MSC2762](https://github.com/matrix-org/matrix-doc/pull/2762) allows a widget to request permission
to send events as well as receive events sent while the widget's session is open, however the MSC
does not propose allowing widgets to read events from before the widget is opened. This MSC aims
to propose an approach for that flow, and is isolated from MSC2762 to avoid making MSC2762 difficult
to review.

While this MSC is isolated from MSC2762, this MSC does use a lot of concepts proposed by MSC2762. It
is suggested to give MSC2762 a read before reading this MSC.

## Proposal

It's important to avoid leaking information into the wild through a widget, which is why MSC2762
doesn't handle the case of widgets being able to look into a room's history. Instead, MSC2762 uses
access controls which prevent the widget from getting too much information up front. This MSC adds
some specific access controls that allow widgets to look backwards into the room's history, though
with the risk that it's violating MSC2762's ideal security model of event handling.

Using a capability structure like MSC2762, widgets can request `m.read.event:<event type>` and
`m.read.state_event:<event type>` to activate the functionality in this MSC. MSC2762's ability to
filter on state keys and message types applies to these capabilities as well in the same way. Like
MSC2762, clients should also not allow widgets to mix known event types into the wrong place (ie:
not allowed to request `m.read.event:m.room.topic` or `m.read.state_event:m.room.message`).

This MSC also does not apply to other kinds of events (EDUs, account data, etc), much like MSC2762.

Assuming the widget has the relevant permissions, it can request events using the following `fromWidget`
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

When a `state_key` is present, the client will respond with state events matching that state key. If
`state_key` is instead a boolean `true`, the client will respond with state events of the given type
with any state key. For clarity, `"state_key": "@alice:example.org"` would return the state event with
the specified state key (there can only be one or zero), while `"state_key": true` would return any
state events of the type, regardless of state key.

To appease MSC2762's ability to read particular msgtypes, the widget can specify a `msgtype` in place
of the `state_key` for `m.room.message` requests.

The `type` is simply the event type to go searching for.

The `limit` is the number of events the widget is looking for. The client can arbitrarily decide to
return less than this limit, though should never return more than the limit. For example, a client
may decide that for privacy reasons a widget can only ever see the last 5 room messages - even though
the widget requested 25, it will only ever get 5 maximum back. When `limit` is not present it is
assumed that the widget wants as many events as the client will give it. When negative, the client
can reject the request with an error.

The recommended maximum `limit`s are:

* For `m.room.member` state events, no limit.
* For all other events, 25.

The client is not required to backfill (use the `/messages` endpoint) to get more events for the
client, and is able to return less than the requested amount of events. When returning state events,
the client should always return the current state event (in the client's view) rather than the history
of an event. For example, `{"type":"m.room.topic", "state_key": "", "limit": 5}` should return zero
or one topic events, not 5, even if the topic has changed more than once.

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

## Potential issues

Most of the concerns are largely security concerns and are discussed in more detail later on in this
proposal.

## Alternatives

Widgets could be powered by a bot or some sort of backend which allows them to filter the room state
and timeline themselves, however this can be a large amount of infrastructure for a widget to maintain
and the user experience is not as great. The client already has most of the information a widget would
need, and trying to interact through a bot would generally mean slower response times or technical
challenges on the part of the widget developer.

## Security considerations

This MSC allows widgets to arbitrarily read history from a room without the user necessarily knowing.
Clients should apply strict limits to the number of events they are willing to provide to widgets
and ensure that users are prompted to explicitly approve the permissions requested, like in MSC2762.

Clients may also wish to consider putting iconography next to room messages when a widget reads them,
either through this MSC or MSC2762.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

* Only call/support the `action`s if an API version of `org.matrix.msc2876` is advertised.
* Use `org.matrix.msc2762.read.[state_]event:*` instead of `m.read.[state_]event:*`. Note that this
  is a different MSC number for better compatibility with MSC2762.
* Use `org.matrix.msc2876.*` in place of `m.*` for all other identifiers.
