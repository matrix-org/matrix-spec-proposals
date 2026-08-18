# MSC4486: Listing delayed events with filtering & pagination

[MSC4140] introduces the endpoint `GET /_matrix/client/v1/delayed_events/{delay_id}`
for retrieving data on a single delayed event that had been scheduled by the requesting client's account.
This API is cumbersome for querying more than one delayed event at a time.

When a client maintains a large number of delayed events, it may be interested in querying events in
a certain room or within a specific time window. Additionally, the client may want to list events in
pages to progressively disclose them to the user during scrolling. The single-item endpoint from [MSC4140]
forces the client to load events one at a time which could be unnecessarily slow and resource-intensive,
and may become out-of-sync if delayed events end up being sent between some of the single-item queries made.

Separately, a client may want to also list finalised delayed events. A usecase for this could be to
check for delayed events that failed to be sent in order to take subsequent action such as sending
or scheduling new events. This is impossible with the endpoint from [MSC4140] without
knowledge of their `delay_id`s, which is currently known only to the client that had scheduled those delayed events.

The present proposal addresses these shortcomings by extending the existing API with a bulk-lookup endpoint
with filtering and pagination capabilities.

## Proposal

A new authenticated Client-Server API endpoint at
`GET /_matrix/client/v1/delayed_events` responds with
a list of details about delayed events owned by the requesting user.

Delayed events are returned in ascending chronological order of their intended send time
(i.e. starting from the soonest delayed event to be sent),
where the send time is calculated from `delayed_since_ts` + `delay_ms`
(where those fields are as defined in [MSC4140]).

The homeserver SHOULD apply rate limiting to this endpoint to provide mitigation against the
[Resource Exhaustion](https://spec.matrix.org/v1.18/appendices/#threat-resource-exhaustion) threat,
as the endpoint most likely requires (dependent on the implementation) serialization steps
and can be used to slow down the homeserver.

To filter results to include only delayed events with a scheduled send time within a specific time
range, the query parameters `from_ts` and `to_ts` are introduced, which are Unix timestamps that
specify this time range. If either parameter is unspecified, its respective end of the time range is
unbounded.

To return results in reverse chronological order, a query parameter of `dir=b` is added. Providing a
query parameter of `dir=f` uses the default of increasing chronological order.

Additionally, a query parameter `from` is introduced. This is a token that can be used to paginate
the list of delayed events as per the [pagination convention]. The homeserver can choose a suitable
page size. The token can be obtained from the new top-level response property `next_batch`. When
there is no next page of results, `next_batch` is absent.

To filter results on delayed events with certain properties, the following query parameters are
added:

- `room_id` - Return only delayed events that were scheduled to be sent into the room with this ID.
- `type` - Return only delayed events of the specified event type.
- `status`: `"scheduled"|"sent"|"cancelled"|"failed"` - Return only delayed events that are still
  scheduled to be sent, or only finalised delayed events that were either sent successfully,
  cancelled by user action, or cancelled by an error.

If any query parameter is set to an unsupported value, the homeserver will respond with HTTP 400 and
a [standard error response] with an `errcode` of `M_INVALID_PARAM`.

On success, the response is HTTP 200 and a JSON object containing the following fields:

- `delayed_events` - An array of objects describing delayed events owned by the requesting user.
  These objects contain the same fields as the object returned by
  [the single-item lookup](https://github.com/matrix-org/matrix-spec-proposals/blob/toger5/expiring-events-keep-alive/proposals/4140-delayed-events-futures.md#getting-delayed-events).

```http
200 OK
Content-Type: application/json

{
  "delayed_events": [
    {
      "delay_id": "...",
      "room_id": "!roomid:example.com",
      "type": "m.room.message",
      "delay_ms": 5500,
      "delayed_since_ts": 1721732853284,
      "content": {
        "msgtype": "m.text",
        "body": "I am now offline"
      }
    },
    ...
  ]
}
```

### Examples

For example, `GET /_matrix/client/v1/delayed_events?dir=b&to_ts=1721732858785` returns all of the
requesting user's delayed events that had been scheduled to be sent no later than the specified
time, starting from the one that had been scheduled to be sent last, and including ones that were
already sent or cancelled:

``` http
200 OK
Content-Type: application/json

{
  "delayed_events": [
    {
      "delay_id": "the-latest-scheduled-event",
      "room_id": "!roomid:example.com",
      "type": "m.room.message",
      "delay": 5500,
      "delayed_since_ts": 1721732853284,
      "content": {
        "msgtype": "m.text",
        "body": "I am now offline"
      }
    },
    {
      "delay_id": "an-earlier-scheduled-event",
      "room_id": "!roomid:example.com",
      "type": "m.rtc.member",
      "state_key": "@user:example.com_DEVICEID",
      "delay": 5000,
      "delayed_since_ts": 1721732853284,
      "content": {
        "application": "m.call",
        "call_id": "",
        ...
      }
    },
    {
      "delay_id": "an-event-sent-manually-before-scheduled-send-time",
      "room_id": "!another-roomid:example.com",
      "type": "m.room.message",
      "delay": 5000,
      "delayed_since_ts": 1721732853280,
      "finalised": {
        "finalised_ts": 1721732854280,
        "event_id": "$abcabca"
      },
      "content": {
        "body": "I have something important to say",
        "msgtype": "m.text"
      }
    },
    {
      "delay_id": "an-event-sent-as-scheduled",
      "room_id": "!another-roomid:example.com",
      "type": "m.room.message",
      "delay": 2000,
      "delayed_since_ts": 1721732854280,
      "finalised": {
        "finalised_ts": 1721732856280,
        "event_id": "$xyzyxyz"
      },
      "content": {
        "body": "Hello, everyone!",
        "msgtype": "m.text"
      }
    },
    {
      "delay_id": "a-cancelled-event",
      "room_id": "!another-roomid:example.com",
      "type": "m.room.message",
      "delay": 2000,
      "delayed_since_ts": 1721732853280,
      "content": {
        "body": "hello, every body!",
        "msgtype": "m.text"
      },
      "finalied": {
        "finalised_ts": 1721732853780
      }
    }
  ],
  "next_batch": "b12345"
}
```

As another example,
`GET /_matrix/client/v1/delayed_events?status=scheduled&room_id=!room:example.org&type=m.room.topic`
returns all of the requesting user's scheduled topic changes to `!room:example.org`, from earliest
to latest:

``` http
200 OK
Content-Type: application/json

{
  "delayed_events": [
    {
      "delay_id": "d0",
      "room_id": "!roomid:example.com",
      "type": "m.room.topic",
      "state_key": "",
      "delay": 5000,
      "delayed_since_ts": 1721732853280,
      "content": {
        "topic": "This is a brand new room"
      }
    },
    {
      "delay_id": "d1",
      "room_id": "!roomid:example.com",
      "type": "m.room.topic",
      "state_key": "",
      "delay": 15000,
      "delayed_since_ts": 1721732853280,
      "content": {
        "topic": "This room is not as new"
      }
    },
    {
      "delay_id": "d2",
      "room_id": "!roomid:example.com",
      "type": "m.room.topic",
      "state_key": "",
      "delay": 20000,
      "delayed_since_ts": 1721732853280,
      "content": {
        "topic": "What an old room this is"
      }
    },
  ]
}
```

As yet another example, `GET /_matrix/client/v1/delayed_events?status=error&type=m.room.member`
returns all of the requesting user's failed attempts to schedule the invitation/removal/banning of a
user:

``` http
200 OK
Content-Type: application/json

{
  "delayed_events": [
    {
      "delay_id": "d1",
      "room_id": "!room1:example.com",
      "type": "m.room.member",
      "state_key": "@new-user:example.com",
      "delay": 5000,
      "delayed_since_ts": 1721732853280,
      "content": {
        "membership": "invite",
        "reason": "You should be in this room by now"
      },
      "finalised": {
        "finalised_ts": 1721732855280,
        "error": {
          "errcode": "M_LIMIT_EXCEEDED",
          "error": "Too many requests",
          "retry_after_ms": 2000
        }
      }
    },
    {
      "delay_id": "d2",
      "room_id": "!room2:example.com",
      "type": "m.room.member",
      "state_key": "@wanted-user:example.com",
      "delay": 5000,
      "delayed_since_ts": 1721732854280,
      "content": {
        "membership": "join",
        "reason": "You just have to be in this room"
      },
      "finalised": {
        "finalised_ts": 1721732859280,
        "error": {
          "errcode": "M_FORBIDDEN",
          "error": "Cannot force another user to join."
        }
      }
    },
    {
      "delay_id": "d2",
      "room_id": "!room3:example.com",
      "type": "m.room.topic",
      "state_key": "@temporary-user:example.com",
      "delay": 5000,
      "delayed_since_ts": 1721732855280,
      "content": {
        "membership": "leave",
        "reason": "Your time is up"
      },
      "finalised": {
        "finalised_ts": 11721732860280,
        "error": {
          "errcode": "M_FORBIDDEN",
          "error": "You do not have a high enough power level to kick from this room."
        }
      }
    },
  ]
}
```

## Potential issues

None foreseen.

## Alternatives

None apparent.

## Security considerations

None.

## Unstable prefix

Whilst the MSC is unstable,
`GET /_matrix/client/unstable/org.matrix.msc4486/delayed_events` should be used
instead of the `GET /_matrix/client/v1/delayed_events` endpoint.

Servers may advertise support for the feature by listing `org.matrix.msc4486` in the
`unstable_features` section of the response to [`GET /_matrix/client/versions`].

Once this proposal completes FCP, servers may advertise support for the *stable* identifiers by
listing `org.matrix.msc4486.stable` in `unstable_features`; clients may use this while they are
waiting for the server to adopt a version of the spec that includes it.

## Dependencies

This MSC builds on [MSC4140: Cancellable delayed events][MSC4140].

  [MSC4140]: https://github.com/matrix-org/matrix-spec-proposals/pull/4140
  [pagination convention]: https://spec.matrix.org/v1.18/appendices/#pagination
  [standard error response]: https://spec.matrix.org/latest/client-server-api/#standard-error-response
  [`GET /_matrix/client/versions`]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions
