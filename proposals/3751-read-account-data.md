# MSC3751: Allowing widgets to read account data

This proposal gives a way for widgets to read account data.

Some data is stored in the account data that is useful for widgets, such as
MSC2545, which stores a list of image packs in account data.

If this proposal is implemented, a widget can read all global packs defined in MSC2545 by
additionally using MSC2876 which is already implemented.

(this proposal uses some copypasta from MSC2876)

## Proposal

New capability:

`m.read.account_data:<event type>` to activate the functionality in this MSC. MSC2762's ability to
filter on state keys and message types applies to these capabilities as well in the same way.

Assuming the widget has the relevant permissions, it can request events using the following `fromWidget`
API action:

```json
{
  "api": "fromWidget",
  "widgetId": "WidgetExample",
  "requestid": "generated-id-1234",
  "action": "read_account_data",
  "data": {
    "type": "m.msc2545.emote_rooms",
    "state_key": "",
    "limit": 25
  }
}
```

When a `state_key` is present, the client will respond with state events matching that state key. If
`state_key` is instead a boolean `true`, the client will respond with state events of the given type
with any state key. For clarity, `"state_key": "@alice:example.org"` would return the state event with
the specified state key (there can only be one or zero), while `"state_key": true` would return any
state events of the type, regardless of state key.

The `limit` is the number of events the widget is looking for. The client can arbitrarily decide to
return less than this limit, though should never return more than the limit. For example, a client
may decide that for privacy reasons a widget can only ever see the last 5 room messages - even though
the widget requested 25, it will only ever get 5 maximum back. When `limit` is not present it is
assumed that the widget wants as many events as the client will give it. When negative, the client
can reject the request with an error.

The recommended maximum `limit` is 25.

The client should always return the current state event (in the client's view) rather than the history
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
    "type": "m.msc2545.emote_rooms",
    "limit": 25
  },
  "response": {
    "events": [
      {
        "type": "m.msc2545.emote_rooms",
        "content": {
          "rooms": {
            "!asdfasdfasdfjasdf:matrix.org": {
              "": {}
            }
          }
        },
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

This MSC allows widgets to arbitrarily read account data without the user necessarily knowing.
Clients should  ensure that users are prompted to explicitly approve the permissions requested, like in MSC2762.

Some account data may be somewhat sensitve, such as the list of direct messages. These events may be blacklisted or the client should otherwise make it clear that these events are requested. With MSC2762 there are legitimate use cases for reading these events.

## Unstable prefix

While this MSC is not present in the spec, clients and widgets should:

* Only call/support the `action`s if an API version of `org.matrix.msc3751` is advertised.
* Use `org.matrix.msc3751.read.account_data:*` instead of `m.read.account_data:*`.
* Use `org.matrix.msc3751.*` in place of `m.*` for all other identifiers.

