# MSC4140: Cancellable delayed events

This MSC proposes a mechanism by which a Matrix client can schedule an event (including a state event) to be sent into
a room at a later time.

The client does not have to be running or in contact with the Homeserver at the time that the event is actually sent.

Once the event has been scheduled, the user's homeserver is responsible for actually sending the event at the appropriate
time and then distributing it as normal via federation.

<!-- TOC -->
- [Background and motivation](#background-and-motivation)
- [Proposal](#proposal)
  - [Scheduling a delayed event](#scheduling-a-delayed-event)
  - [Managing delayed events](#managing-delayed-events)
  - [Getting delayed events](#getting-delayed-events)
    - [On demand](#on-demand)
    - [On push](#on-push)
  - [Homeserver implementation details](#homeserver-implementation-details)
    - [Power levels are evaluated at the point of sending](#power-levels-are-evaluated-at-the-point-of-sending)
    - [Delayed state events are cancelled by a more recent state event](#delayed-state-events-are-cancelled-by-a-more-recent-state-event)
    - [Rate-limiting at the point of sending](#rate-limiting-at-the-point-of-sending)
  - [Guest accounts](#guest-accounts)
- [Use case specific considerations](#use-case-specific-considerations)
  - [MatrixRTC](#matrixrtc)
    - [Background](#background)
    - [How this MSC would be used for MatrixRTC](#how-this-msc-would-be-used-for-matrixrtc)
  - [Self-destructing messages](#self-destructing-messages)
- [Potential issues](#potential-issues)
  - [Compatibility with Cryptographic Identities](#compatibility-with-cryptographic-identities)
- [Alternatives](#alternatives)
  - [Delegating delayed events](#delegating-delayed-events)
  - [Batch sending](#batch-sending)
  - [Not reusing the `send`/`state` endpoint](#not-reusing-the-sendstate-endpoint)
  - [Batch delayed events with custom endpoint](#batch-delayed-events-with-custom-endpoint)
    - [Batch Response](#batch-response)
    - [EventId template variable](#eventid-template-variable)
  - [Allocating the event ID at the point of scheduling the send](#allocating-the-event-id-at-the-point-of-scheduling-the-send)
  - [MSC4018 (use client sync loop)](#msc4018-use-client-sync-loop)
  - [Federated delayed events](#federated-delayed-events)
  - [MQTT style Last Will](#mqtt-style-last-will)
  - [`M_INVALID_PARAM` instead of `M_MAX_DELAY_EXCEEDED`](#m_invalid_param-instead-of-m_max_delay_exceeded)
  - [Naming](#naming)
  - [Don't provide a `send` action](#dont-provide-a-send-action)
  - [Use `DELETE` HTTP method for `cancel` action](#use-delete-http-method-for-cancel-action)
  - [[Ab]use typing notifications](#abuse-typing-notifications)
- [Security considerations](#security-considerations)
- [Unstable prefix](#unstable-prefix)
- [Dependencies](#dependencies)
<!-- /TOC -->

## Background and motivation

This proposal originates from the needs of VoIP signalling in Matrix:

The Client-Server API currently has a  [Voice over IP module](https://spec.matrix.org/v1.11/client-server-api/#voice-over-ip)
that uses room messages to communicate the call state. However, it only allows for calls with two participants.

[MSC3401: Native Group VoIP Signalling](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) proposes a scheme
that allows for more than two participants by using room state events.

In this arrangement each device signals its participant in a call by sending a state event that represents the device's
"membership" of a call. Once the device is no longer in the call, it sends a new state event to update the call state and
communicate that the device is no longer a member.

This works well when the client is running and can send the state events as needed. However, if the client is not able to
communicate with the homeserver (e.g. the user closes the app or loses connection) the call state is not updated to say
that the participant has left.

The motivation for this MSC is to allow updating call member state events after the user disconnected by allowing to
schedule/delay/timeout/expire events in a generic way.

The ["reliability requirements for the room state"](https://github.com/matrix-org/matrix-spec-proposals/blob/toger5/matrixRTC/proposals/4143-matrix-rtc.md#reliability-requirements-for-the-room-state)
section of [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) has more details on the
use case.

There are numerous possible solution to solve the call member event expiration. They are covered in detail
in the [Use case specific considerations/MatrixRTC](#use-case-specific-considerations) section, because they are not part
of this proposal.

This proposal enables a Matrix client to schedule a "hangup" state event to be sent after a specified time period.
The client can then periodically restart the timer whilst it is running. If the client is no longer running
or able to communicate, then the timer would expire and the homeserver would send the "hangup" event on behalf of the client.

Such an arrangement can also be described as a "heartbeat" mechanism. The client sends a "heartbeat" to the homeserver
in the form of a "restart" of the delayed event to keep the call "alive".
The homeserver will automatically send the "hangup" if it does not receive a "heartbeat".

## Proposal

The following operations are added to the client-server API:

- Schedule an event to be sent at a later time
- Get a list of delayed events
- Restart the timer of a delayed event
- Send the delayed event immediately
- Cancel a delayed event so that it is never sent

At the point of an event being scheduled the homeserver is [unable to allocate the event ID](#allocating-the-event-id-at-the-point-of-scheduling-the-send).
Instead, the homeserver allocates a `delay_id` to the scheduled event which is used during the above API operations.

### Scheduling a delayed event

An optional `delay` query parameter is added to the existing
[`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}`](https://spec.matrix.org/v1.11/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
and
[`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`](https://spec.matrix.org/v1.11/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
endpoints.

The new query parameter is used to configure the event scheduling:

- `delay` - Optional number of milliseconds the homeserver should wait before sending the event. If no `delay` is provided,
the event is sent immediately as normal.

The body of the request is the same as it is currently.

If a `delay` is provided, the homeserver schedules the event to be sent with the specified delay and responds with an
opaque `delay_id` field (omitting the `event_id` as it is not available):

```http
200 OK
Content-Type: application/json

{
  "delay_id": "1234567890"
}
```

The homeserver can optionally enforce a maximum delay duration. If the requested delay exceeds the maximum, the homeserver
can respond with a [`400`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400) status code
and a body with a new Matrix error code `M_MAX_DELAY_EXCEEDED` and the maximum allowed delay (`max_delay` in milliseconds).

For example, the following specifies a maximum delay of 24 hours:

```http
400 Bad Request
Content-Type: application/json

{
  "errcode": "M_MAX_DELAY_EXCEEDED",
  "error": "The requested delay exceeds the allowed maximum.",
  "max_delay": 86400000
}
```

The homeserver **should** apply rate limiting to the scheduling of delayed events to provide mitigation against the
[High Volume of Messages](https://spec.matrix.org/v1.11/appendices/#threat-high-volume-of-messages) threat.

The homeserver **may** apply a limit on the maximum number of
outstanding delayed events in which case a new Matrix error code
`M_MAX_DELAYED_EVENTS_EXCEEDED` can be returned:

```http
400 Bad Request
Content-Type: application/json

{
  "errcode": "M_MAX_DELAYED_EVENTS_EXCEEDED",
  "error": "The maximum number of delayed events has been reached.",
}
```

### Managing delayed events

A new authenticated client-server API endpoint at `POST /_matrix/client/v1/delayed_events/{delay_id}` allows scheduled events
to be managed.

The body of the request is a JSON object containing the following fields:

- `action` - The action to take on the delayed event.\
Must be one of:
  - `send` - Send the delayed event immediately instead of waiting for the delay time to be reached.
  - `cancel` - Cancel the delayed event so that it is never sent.
  - `restart` - Reset the send time to be `now + original_delay`.

For example, the following would send the delayed event with delay ID `1234567890` immediately:

```http
POST /_matrix/client/v1/delayed_events/1234567890
Content-Type: application/json

{
  "action": "send"
}
```

Where the `action` is `send`, the homeserver **should** apply rate limiting to provide mitigation against the
[High Volume of Messages](https://spec.matrix.org/v1.11/appendices/#threat-high-volume-of-messages) threat.

Once a delayed event has been sent or canceled, it is finalized and cannot be
accessed via this endpoint.

The server will return a `M_NOT_FOUND` error.

Managing the delayed events does not require rate limits.
The rate limits will be applied when evets are send after the delay times out (or when the event is send by calling `send`).

If the user has scheduled a large amount of delayed events they can cancel all of them without rate limiting,
because scheduling of the events itself is rate limited this is not causing issues.
Implementers should make cancelling delayed events similarly
expensive as sending a rate limit error response.

### Getting delayed events

New authenticated client-server API endpoints `GET /_matrix/client/v1/delayed_events/scheduled` and
`GET /_matrix/client/v1/delayed_events/finalised` allows clients to get a list of
all the delayed events owned by the requesting user that have been scheduled to send, have been sent, or failed to be sent.

The endpoints accepts a query parameter `from` which is a token that can be used to paginate the list of delayed events as
per the [pagination convention](https://spec.matrix.org/v1.11/appendices/#pagination). The homeserver can choose a suitable
page size.

The response is a JSON object containing the following fields:

- For the `GET /_matrix/client/v1/delayed_events/scheduled` endpoint:
  - `scheduled` - Required. An array of delayed events that have been scheduled to be sent,
  sorted by `running_since + delay` in increasing order (event that will timeout soonest first).
    - `delay_id` - Required. The ID of the delayed event.
    - `room_id` - Required. The room ID of the delayed event.
    - `type` - Required. The event type of the delayed event.
    - `state_key` - Optional. The state key of the delayed event if it is a state event.
    - `delay` - Required. The delay in milliseconds before the event is to be sent.
    - `running_since` - Required. The timestamp (as Unix time in milliseconds) when the delayed event was scheduled or
      last restarted.
    - `content` - Required. The content of the delayed event. This is the body of the original `PUT` request, not a preview
      of the full event after sending.
  - `next_batch` - Optional. A token that can be used to paginate the list of delayed events.

- For the `GET /_matrix/client/v1/delayed_events/finalised` endpoint:
  - `finalised` - Required. An array of finalised delayed events, that have either been sent or resulted in an error,
  sorted by `origin_server_ts` in decreasing order (latest finalised event first).
    - `delayed_event` - Required. Describes the original delayed event in the same format as the `delayed_events` array.
    - `outcome`: `"send"|"cancel"`
    - `reason`: `"error"|"action"|"delay"`
    - `error`: Optional Error. A matrix error (as defined by [Standard error response](https://spec.matrix.org/v1.11/client-server-api/#standard-error-response))
    to explain why this event failed to be sent. The Error can either be the `M_CANCELLED_BY_STATE_UPDATE` or any of the
    Errors from the client server send and state endpoints.
    - `event_id` - Optional EventId. The `event_id` this event got in case it was sent.
    - `origin_server_ts` - Optional Timestamp. The timestamp the event was sent.
  - `next_batch` - Optional. A token that can be used to paginate the list of finalised events.

The batch size and the amount of terminated events that stay on the homeserver can be chosen, by the homeserver.
The recommended values are:

- `finalised` retention: 7 days
- `finalised` batch size: 10
- `finalised` max cached events: 1000

There is no guarantee for a client that all events will be available in the
finalised events list if they exceed the limits of their homeserver.
Additionally, a homeserver may discard finalised delayed events that have been returned by a
`GET /_matrix/client/v1/delayed_events/finalised` response.

The homeserver **should** apply rate limiting to the `finalised` and `scheduled` delayed events `GET` endpoints.
Both most likely require (dependent on the implementation) serialization steps and can be used to slow down the server.

An example for a response to the `GET /_matrix/client/v1/delayed_events/scheduled` endpoint:

```http
200 OK
Content-Type: application/json

{
  "scheduled": [
    {
      "delay_id": "1234567890",
      "room_id": "!roomid:example.com",
      "type": "m.room.message",
      "delay": 15000,
      "running_since": 1721732853284,
      "content":{
        "msgtype": "m.text",
        "body": "I am now offline"
      }
    },
    {
      "delay_id": "abcdefgh",
      "room_id": "!roomid:example.com",
      "type": "m.rtc.member",
      "state_key": "@user:example.com_DEVICEID",
      "delay": 5000,
      "running_since": 1721732853284,
      "content":{
        "application": "m.call",
        "call_id": "",
        ...
      }
    }
  ],
  "next_batch": "b12345"
}
```

Unless the delayed event is updated beforehand, the event will be sent after `running_since` + `delay`.

This can be used by clients to display events that have been scheduled to be sent in the future.

For use cases where the existence of a delayed event is also of interest for other room members
(e.g. self-destructing messages), it is recommended to include this information in the original/affected event itself.

### Homeserver implementation details

#### Power levels are evaluated at the point of sending

Power levels are evaluated for each event only once the delay has occurred and it will be distributed/inserted into the
DAG. This implies a delayed event can fail if it violates power levels at the time the delay passes.

Conversely, it's also possible to successfully schedule an event that the user has no permission to send at the time of sending.
If the power level situation has changed at the time the delay passes, the event can even reach the DAG.

#### Delayed state events are cancelled by a more recent state event

> [!NOTE]
> Special rule for delayed state events:
> A delayed event `D` gets cancelled if:
>
> - `D` is a state event with key `k` and type `t` from sender `s`.
> - A new state event `N` with type `t` and key `k` is sent into the room.
> - The sender of `D` is different to the sender `N`.

If a new state event is sent to the same room at the same entry (`event_type`, `state_key` pair) as a delayed event by a
**different matrix user**, any delayed event for this entry (`event_type`, `state_key` pair) is cancelled.

This only happens if its a state update from a different user. If it is from the same user, the delayed event will not
get cancelled.
If the same user is updating the state which has associated delayed events, this user is in control of those delayed events.
They can just cancel and check the events manually using the `/delayed_events` and the `/delayed_events/scheduled` endpoint.

In the case where the delayed event gets cancelled due to a different user updating the same state, there
is no race condition here since a possible race between timeout and the _new state event_ will always converge to
the _new state event_:

- timeout for _delayed event_ followed by _new state event_: the room state will be updated twice: once by the content of
  the delayed event but later with the content of _new state event_.
- _new state event_ followed by timeout for _delayed event_: the _new state event_ will cancel the outstanding _delayed event_.

The finalised delayed event as represented by the finalised list of the GET endpoint (See:[Getting delayed events](#getting-delayed-events))
will be stored with the following outcome:

```json
"outcome": "cancel", 
"reason": "error", 
"error": {
  "errorcode": "M_CANCELLED_BY_STATE_UPDATE",
  "error":"The delayed event did not get send because a different user updated the same state event.
  So the scheduled event might change it in an undesired way."}
```

Note that this behaviour does not apply to regular (non-state) events as there is no concept of a (`event_type`, `state_key`)
pair that could be overwritten.

#### Rate-limiting at the point of sending

Further to the rate limiting of the API endpoints, the homeserver **should** apply rate limiting to the sending
of delayed messages at the point that they are inserted into the DAG.

This is to provide mitigation against the
[High Volume of Messages](https://spec.matrix.org/v1.11/appendices/#threat-high-volume-of-messages) threat where a malicious
actor could schedule a large volume of events ahead of time without exceeding a rate limit on the initial `PUT` request,
but has specified a `delay` that corresponds to a common point of time in the future.

A limit on the maximum number of delayed events that can be outstanding at one time could also provide some mitigation against
this attack.

### Guest accounts

All delayed event related endpoints are available to guest accounts.
This allows guest accounts to participate in MatrixRTC sessions.

## Use case specific considerations

Delayed events can be used for many different features: tea timers, reminders, or ephemeral events could be implemented
using delayed events, where clients send room events with
intentional mentions or a redaction as a delayed event.
It can even be used to send temporal power levels/mutes or bans.

### MatrixRTC

In this section, an overview is given how this MSC is used in [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)
and alternative expiration systems are evaluated.

#### Background

MatrixRTC makes it necessary to have real time information about the current MatrixRTC session.
To properly display room tiles and header in the room list (or compute a list of ongoing calls), it's required to know:

- If there is a running session.
- What type that session has.
- Who and how many people are currently participating.

A particular delicate situation is that clients are not able to inform others if they lose connection.
There are numerous approaches to solve such a situation. They split into two categories:

- Polling based
  - Ask the users if they are still connected.
  - Ask an RTC backend (SFU) who is connected.
- Timeout based
  - Update the room state every x seconds.
    This allows clients to check how long an event has not been updated and ignore it if it's expired.
  - Use delayed events with a 10s timeout to send the disconnected from call
    in less then 10s after the user is not anymore pinging the `/delayed_events` endpoint
    (or delegate the disconnect action to a service attached to the SFU).
  - Use the client sync loop as a special case timeout for call member events
    (see [Alternatives/MSC4018 (use client sync loop))](#msc4018-use-client-sync-loop)).

Polling based solutions have a large overhead in complexity and network requests on the clients.
For example:

> A room list with 100 rooms where there has been a call before in every room
> (or there is an ongoing call) would require the client to send a to-device message
> (or a request to the SFU) to every user that has an active state event to check if
> they are still online. All this is just to display the room tile properly.

For displaying the room list, timeout based approaches are much more reasonable because they allow computing MatrixRTC
metadata for a room to be synchronous.

The current solution updates the room state every X minutes.
This is not elegant since room state gets repeatedly sent with the same content.
In large calls, this could result in high traffic and increase the size of the room DAG.

A call with 100 call members implies 100 state events every X minutes. X cannot be a
long duration because
it is the duration after which the event can be considered expired. Improper
disconnects would result in the user being displayed as "still in the call" for
X minutes (which should be as short as possible).

Additionally, this approach requires perfect server client time synchronization to compute the expiration.
This is currently not possible over federation since `unsigned.age` is not available over federation.

#### How this MSC would be used for MatrixRTC

With this proposal, the client can use delayed events to implement a "heartbeat" mechanism.

On joining the call, the client sends a "join" state event as normal to indicate that it is participating:

```http
PUT /_matrix/client/v1/rooms/!wherever:example.com/state/m.rtc.member/@someone:example.com
Content-Type: application/json

{
  "application": "m.call",
  "call_id": "",
  ...
}
```

Before sending the join event, it also schedules a delayed "hangup" state event with `delay` of around 5-20 seconds that
marks the end of its participation:

```http
PUT /_matrix/client/v1/rooms/!wherever:example.com/state/m.rtc.member/@someone:example.com?delay=10000
Content-Type: application/json

{
  "application": "m.call",
  "call_id": "",
  ...
}
```

Let's say the homeserver returns a `delay_id` of `1234567890`.

The client then periodically sends a "heartbeat" in the form of a "restart" of the delayed "hangup" state event to keep
the call membership "alive".

For example it could make the request every 5 seconds (or some other period less than the `delay`):

```http
POST /_matrix/client/v1/delayed_events/1234567890
Content-Type: application/json

{
  "action": "restart"
}
```

This would have the effect that if the homeserver does not receive a "heartbeat" from the client for 10 seconds, then
it will automatically send the "hangup" state event for the client.

Since the delayed event is sent first, a client can guarantee (at the time they are sending
the join event) that it will eventually leave.

### Self-destructing messages

This MSC also allows an implementation of "self-destructing" messages using redaction:

First send (or generate the PDU when
[MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080)
is available):
`PUT /_matrix/client/v1/rooms/{roomId}/send/m.room.message/{txnId}`

```jsonc
{
  "msgtype": "m.text",
  "body": "this message will self-redact in 10 minutes"
}
```

then send:
`PUT /_matrix/client/v1/rooms/{roomId}/send/m.room.redaction/{txnId}?delay=600000`

```jsonc
{
  "redacts": "{event_id}"
}
```

This would redact the message with content: `"m.text": "my msg"` after 10 minutes.

## Potential issues

### Compatibility with Cryptographic Identities

Ideally, this proposal should be compatible with other proposals such as
[MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080) which introduce mechanisms
to allow the recipient of an event to determine whether it was sent by a client as opposed to have been spoofed/injected
by a malicious homeserver.

In the context of this proposal, the delayed events should be signed with the same cryptographic identity as the client
that scheduled them.

This means that the content of the original scheduled event must be sent "as is" without modification by the homeserver.
The consequence is an implementation detail that client developers must be aware of: if the content of the delayed
event contains a timestamp, then it would be the timestamp of when the event was originally scheduled rather than
anything later.

However, the `origin_server_ts` of the delayed event should be the time that the event is actually sent by the homeserver.

This is a general problem that arises with the introduction
of [Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080).
A user can intentionally, or caused by network conditions, delay the signing and sending of an event.
A possible solution would be the introduction of a `signing_ts` (in the signed section) and keep the `origin_server_ts`
in the unsigned section.
Both are reasonable data points that clients might want to use.
This would solve issues related to delayed events since
it would make it transparent to clients, when an event was scheduled and when it was distributed over federation.

## Alternatives

### Delegating delayed events

It is useful for external services to also interact with delayed events. If a client disconnects, an external service can
be the best source to send the delayed event/"last will".

This is not covered in this MSC but could be realized with scoped access tokens.
A scoped token that only allows to interact with the `delayed_events` endpoint and only with a subset of `delay_id`s
would be used.

With this, an SFU that tracks the current client connection state could be given the power to control the delayed event.
The client would share the scoped token and the required details, so that the SFU can call the
`refresh` endpoint while a user is connected
and can call the delayed event `send` request once the user disconnects
(using a `{"action": "restart"}` and a `{"action": "send"}` `/delayed_events` request.).
This way, the SFU can be used as the source of truth for the call member room state event without knowing anything about
the Matrix call.

Since the SFU has a much lower chance of running into a network issue,
`{"action": "restart"}` calls may be sent much more infrequently.
Instead of calling the `/delayed_events` endpoint every couple of seconds, a delayed event's
timeout can be set to be long (e.g. 6 hours), as the SFU can be expected to not forget sending the `{"action": "send"}` action
when it detects a disconnecting client.

### Batch sending

In some scenarios it is important to allow to send an event with an associated
delay at the same time.

- One example would be redacting an event. It only makes sense to redact the event if it exists.
  It might be important to have the guarantee that the delayed redact is received
  by the server at the time where the original message is sent.
- In the case of a state event, a user might want to set the state to `A` and after a
  timeout change it back to `{}`. By using two separate requests, sending `A` could work,
  but the event with content `{}` could fail. The state would not automatically
  reset to `{}`.

For this use case, batch sending of multiple delayed events would be desired.

Batch sending is not included in the proposal of this MSC however since batch sending should
become a generic Matrix concept as proposed with `/send_pdus`. (see: [MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080))

[MSC2716: Incrementally importing history into existing rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/2716)
already proposes a `batch_send` endpoint. However, it is limited to application services and focuses on historic
data. Since the additional capability to use a template `event_id` parameter is also needed,
this probably is not a good fit.

### Not reusing the `send`/`state` endpoint

Alternatively, new endpoints could be introduced to not overload the `send` and `state` endpoint.
Those endpoints could be called:

`PUT /_matrix/client/v1/rooms/{roomId}/send_delayed_event/{eventType}/{txnId}?delay={delay_ms}`

`PUT /_matrix/client/v1/rooms/{roomId}/state_delayed_event/{eventType}/{stateKey}?delay={delay_ms}`

This would allow the response for the `send` and `state` endpoints to remain as they are currently,
and to have a different return type for the new `send_delayed_event` and `state_delayed_event` endpoints.

### Allocating the event ID at the point of scheduling the send

This was considered, but when sending a delayed event the `event_id` is not yet available:

The Matrix spec says that the `event_id` must use the [reference hash](https://spec.matrix.org/v1.10/rooms/v11/#event-ids)
which is [calculated from the fields](https://spec.matrix.org/v1.10/server-server-api/#calculating-the-reference-hash-for-an-event)
of an event including the `origin_server_ts` as defined in [this list](https://spec.matrix.org/v1.10/rooms/v11/#client-considerations)

Since the `origin_server_ts` may change due to re-scheduling the event's send time, the event ID cannot be relied upon
as it would also change.  

### MSC4018 (use client sync loop)

[MSC4018: Reliable call membership](https://github.com/matrix-org/matrix-spec-proposals/pull/4018) also
proposes a way to make call memberships reliable. It uses the client sync loop as
an indicator to determine if the event is expired, instead of letting the SFU
inform about the call termination or using the call app ping/refresh loop as proposed earlier in this MSC.

The advantage is that this does not require introducing a new ping system
(as is proposed here by using the `delayed_events` restart action).
Though with cryptographic identities, the client needs to create the leave event.

The timeout for syncs are much slower than what would be desirable (30s vs 5s).

With a widget implementation for calls, it cannot be guaranteed that the widget is running during the sync loop.
So one either has to move the hangup logic to the hosting client or let the widget run all the time.

A dedicated ping (independent to the sync loop) is more flexible and allows for the widget to
execute the timer restart.
If the widget dies, the call membership will disconnect.

Additionally, the specification should not include specific
custom server rules if possible.
Sending an event on behalf of a user based on the client sync loop if there is an event with a specific type and specific
content is quite a server-specific behaviour, and also would not work well with encrypted state events and cryptographic
identities.
This proposal is a general behaviour valid for all event types.

### Federated delayed events

Delayed events could be sent over federation immediately and then have the receiving servers process (sent down to clients)
them at the appropriate time.

Downsides of this approach that have been considered are that:

- individual "heartbeats"/restarts would need to distributed via federation, meaning more traffic and processing
to be done.
- if any homeservers missed the federated "heartbeat"/restart message, then they might decide that the event is visible
to clients whereas
other homeservers might have received it and come to a different conclusion. If the event was later cancelled then
resolving the inconsistency feels more complex than if the event was never sent in the first place.

[MSC3277: Scheduled messages](https://github.com/matrix-org/matrix-spec-proposals/pull/3277) proposes a similar feature
and there is an extensive analysis of the pros and cons of this MSC vs MSC3277
[in this discussion](https://github.com/matrix-org/matrix-spec-proposals/pull/4140#discussion_r1653083566).

If it's not needed to allow modification of a delayed event after it has been scheduled, there is a benefit in
federating the scheduled event (adding it to the DAG immediately). It increases resilience: the sender's homeserver can
disconnect and the delayed message still will enter non-soft-failed state (will be sent).

However, for the MatrixRTC use case it's required to be able to modify the event after it has been scheduled. As such,
this approach has been discounted.

### MQTT style Last Will

[MQTT](https://mqtt.org/) has the concept of a Will Message that is published by the server when a client disconnects.

The client can set a Will Message when it connects to the server. If the client disconnects unexpectedly, the server will
publish the Will Message if the client is not back online within a specified time.

A similar concept could be applied to Matrix by having the client specify a set of "Last Will" events and have the
homeserver trigger them if the client (possibly identified by device ID) does not send an API request within a specified
time.

The main differentiator is that this type of approach might use the sync loop as the "heartbeat" equivalent similar to
[MSC4018](https://github.com/matrix-org/matrix-spec-proposals/pull/4018).

A benefit compared to this proposal is that theoretically there would be no additional network traffic overhead.

Some complications are:

- in order to avoid additional network traffic, the homeserver would need to proactively realise that a connection
has dropped. Depending on the network/load balancer stack this might be problematic.
- as an alternative, the client could reduce the long poll timeout (from a typical 30s down to, say, 5s) which would
result in a traffic increase.
- As syncing is a per-client concept, the MatrixRTC app has to either run in the same process as the client so that a
MatrixRTC app failure triggers the client Last Will or the client has to observe the MatrixRTC app and simulate the Last
Will if the MatrixRTC app fails.

### `M_INVALID_PARAM` instead of `M_MAX_DELAY_EXCEEDED`

The existing `M_INVALID_PARAM` error code could be used instead of introducing a new error code `M_MAX_DELAY_EXCEEDED`.

### Naming

The following alternative names for this concept are considered:

- Future
- DelayedEvents
- PostponedEvents
- LastWill

### Don't provide a `send` action

Instead of providing a `send` action for delayed events, the client could cancel the outstanding delayed event and send
a new non-delayed event instead.

This would simplify the API, but it's less efficient since the client would have to send two requests instead of one.

### Use `DELETE` HTTP method for `cancel` action

Instead of providing a `cancel` action for delayed events, the client could send a `DELETE` request to the same endpoint.

This feels more elegant, but it doesn't feel like a good suggestion for how the other actions are mapped.

### [Ab]use typing notifications

Some exploration of using typing notifications to indicate that a user is still connected to a call was done.

The idea of extending [MSC3038: Typed typing notifications](https://github.com/matrix-org/matrix-spec-proposals/pull/3038)
to allow for additional meta data (like device ID and call ID) was considered.

A perceived benefit was that if the delay events were federated, then the typing notification EDUs might provide an
efficient transport.

However, as the conclusion was to [not federate the delayed events](#federated-delayed-events), this approach was
discounted in favour of a dedicated endpoint.

### Alternative to `running_since` field

Some alternatives for the `running_since` field on the `GET` response are:

- `delaying_from`
- `delayed_since`
- `delaying_since`
- `last_restart` - but this feels less clear than `running_since` for a delayed event that hasn't been restarted

## Security considerations

All new endpoints are authenticated.

To mitigate the risk of users flooding the delayed events database, servers **must** make it possible to configure
the values for the maximum amount and the maximum timeout value for scheduled delayed events.
(When the server returns the `M_MAX_DELAYED_EVENTS_EXCEEDED` and the `M_MAX_DELAY_EXCEEDED` error)

It is the server maintainers responsibility to evaluate the best tradoff between what usecases
their users have for delayed events for and the resources they are able to provide.

Its the homeserver implementers responsibility to communicate this and educate the server hosters about the tradeoffs
and potentially give sane example values for those configurations.

As described [above](#power-levels-are-evaluated-at-the-point-of-sending), the homeserver **must** evaluate and enforce the
power levels at the time of the delayed event being sent (i.e. added to the DAG).

This has the risk that this feature could be used by a malicious actor to circumvent existing rate limiting measures which
corresponds to the [High Volume of Messages](https://spec.matrix.org/v1.11/appendices/#threat-high-volume-of-messages)
threat. The homeserver **should** apply rate-limiting to both the scheduling of delayed events and the later sending to
mitigate this risk, as well as limiting the number of scheduled events a user can have at any one time.

## Unstable prefix

Whilst the MSC is in the proposal stage, the following should be used:

- `org.matrix.msc4140.delay` should be used instead of the `delay` query parameter.
- `POST /_matrix/client/unstable/org.matrix.msc4140/delayed_events/{delay_id}` should be used instead of
  the `POST /_matrix/client/v1/delayed_events/{delay_id}` endpoint.
- `GET /_matrix/client/unstable/org.matrix.msc4140/delayed_events` should be used instead of
  the `GET /_matrix/client/v1/delayed_events` endpoint.
- The `M_UNKNOWN` `errcode` should be used instead of `M_MAX_DELAY_EXCEEDED` as follows:

```json
{
  "errcode": "M_UNKNOWN",
  "error": "The requested delay exceeds the allowed maximum.",
  "org.matrix.msc4140.errcode": "M_MAX_DELAY_EXCEEDED",
  "org.matrix.msc4140.max_delay": 86400000
}
```

instead of:

```json
{
  "errcode": "M_MAX_DELAY_EXCEEDED",
  "error": "The requested delay exceeds the allowed maximum.",
  "max_delay": 86400000
}
```

- The `M_UNKNOWN` `errcode` should be used instead of `M_MAX_DELAYED_EVENTS_EXCEEDED` as follows:

```json
{
  "errcode": "M_UNKNOWN",
  "error": "The maximum number of delayed events has been reached.",
  "org.matrix.msc4140.errcode": "M_MAX_DELAYED_EVENTS_EXCEEDED"
}
```

instead of:

```json
{
  "errcode": "M_MAX_DELAYED_EVENTS_EXCEEDED",
  "error": "The maximum number of delayed events has been reached."
}
```

- The `M_UNKNOWN` `errcode` should be used instead of `M_CANCELLED_BY_STATE_UPDATE` as follows:

```json
{
  "errcode": "M_UNKNOWN",
  "org.matrix.msc4140.errcode": "M_CANCELLED_BY_STATE_UPDATE",
  "error":"The delayed event did not get send because a different user updated the same state event.
  So the scheduled event might change it in an undesired way."
  }
```

instead of:

```json
{
  "errcode": "M_CANCELLED_BY_STATE_UPDATE",
  "error":"The delayed event did not get send because a different user updated the same state event.
  So the scheduled event might change it in an undesired way."
  }
```

Additionally, the feature is to be advertised as an unstable feature in the `GET /_matrix/client/versions` response, with
the key `org.matrix.msc4140` set to `true`. So, the response could then look as follows:

```json
{
    "versions": ["..."],
    "unstable_features": {
        "org.matrix.msc4140": true
    }
}
```

## Dependencies

None.
