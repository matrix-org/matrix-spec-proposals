# MSC4140: Delayed events (Futures)

This MSC proposes a mechanism by which a Matrix client can schedule an event (including a state event) to be sent into
a room on behalf of a user at a later time.

The client does not have to be running or in contact with the Homeserver at the time that the event is actually sent.

Once the event has been scheduled, the user's homeserver is responsible for actually sending the event at the appropriate
time and then distributing as normal via federation.

<!-- TOC -->

- [MSC4140: Delayed events Futures](#msc4140-delayed-events-futures)
  - [Background and motivation](#background-and-motivation)
  - [Proposal](#proposal)
    - [Scheduling a delayed event](#scheduling-a-delayed-event)
    - [Getting delayed events](#getting-delayed-events)
    - [Managing delayed events](#managing-delayed-events)
    - [Homeserver implementation details](#homeserver-implementation-details)
      - [Power levels are evaluated at the point of sending](#power-levels-are-evaluated-at-the-point-of-sending)
      - [Delayed events are cancelled by a more recent state event](#delayed-events-are-cancelled-by-a-more-recent-state-event)
  - [Use case specific considerations](#use-case-specific-considerations)
    - [MatrixRTC](#matrixrtc)
      - [Background](#background)
      - [How this MSC would be used for MatrixRTC](#how-this-msc-would-be-used-for-matrixrtc)
    - [Self-destructing messages](#self-destructing-messages)
  - [Potential issues](#potential-issues)
  - [Alternatives](#alternatives)
    - [Delegating futures](#delegating-futures)
    - [Batch sending](#batch-sending)
    - [Not reusing the send/state endpoint](#not-reusing-the-sendstate-endpoint)
    - [Batch sending futures with custom endpoint](#batch-sending-futures-with-custom-endpoint)
      - [Batch Response](#batch-response)
      - [Allocating event ID at the point of scheduling the send](#allocating-event-id-at-the-point-of-scheduling-the-send)
      - [EventId template variable](#eventid-template-variable)
    - [MSC4018 use client sync loop](#msc4018-use-client-sync-loop)
    - [Federated futures](#federated-futures)
    - [MQTT style Last Will](#mqtt-style-last-will)
    - [Naming](#naming)
  - [Security considerations](#security-considerations)
  - [Unstable prefix](#unstable-prefix)
  - [Dependencies](#dependencies)

<!-- /TOC -->

## Background and motivation

This proposal originates from the needs of VoIP signalling in Matrix:

The Client-Server API currently has a  [Voice over IP module](https://spec.matrix.org/v1.11/client-server-api/#voice-over-ip)
that uses room messages to communicate the call state. However, it only allows for calls with two participants.

[MSC3401: Native Group VoIP Signalling](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) proposes a scheme that
allows for more than two-participants by using room state events.

In this arrangement each device signals its participant in a call by sending a state event that represents the device's
"membership" of a call. Once the device is no longer in the call, it sends a new state event to update the call state and say
that it is no longer a member.

This works well when the client is running and can send the state events as needed. However, if the client is not running and
able to communicate with the homeserver (e.g. the user closes the app or loses connection) the call state is not updated to
say that the participant has left.

The motivation for this MSC is to allow updating call member state events after the user disconnected by allowing to
schedule/delay/timeout/expire events in a generic way.

The ["reliability requirements for the room state"](https://github.com/matrix-org/matrix-spec-proposals/blob/toger5/matrixRTC/proposals/4143-matrix-rtc.md#reliability-requirements-for-the-room-state)
section of [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) has more details on the use case.

There are numerous possible solution to solve the call member event expiration. They are covered in detail
in the [Use case specific considerations/MatrixRTC](#use-case-specific-considerations) section, because they are not part
of this proposal.

The proposal here allows a Matrix client to schedule a "hangup" state event to be sent after a specified time period. The client
can then periodically reset/restart the timer whilst it is running. If the client is no longer running or able to communicate then the timer would expire and the homeserver would send the "hangup" event on behalf of the client.

## Proposal

We propose the following operations are added to the client-server API:

- Schedule an event to be sent at a later time
- Get a list of events that have been scheduled to send
- Refresh the timeout of a scheduled event
- Send the scheduled event immediately
- Cancel a scheduled event so that it is never sent

At the point of an event being scheduled the homeserver is [unable to allocate the event ID](#allocating-event-id-at-the-point-of-scheduling-the-send). Instead, the homeserver allocates a _future ID_ to the scheduled event which is used during the above API operations.

### Scheduling a delayed event

We propose extending the existing
[`PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}`](https://spec.matrix.org/v1.11/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
and
[`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`](https://spec.matrix.org/v1.11/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey)
endpoints by adding an optional `future_timeout` query parameter.

The new query parameter is used to configure the event scheduling:

- `future_timeout` - Optional number of milliseconds the homeserver should wait before sending the event. If no `future_timeout` is provided, the event is sent immediately as normal.

The body of the request is the same as currently.

If a `future_timeout` is provided, the homeserver schedules the event to be sent with the specified delay and returns the _future ID_ in the `future_id` field (omitting the `event_id` as it is not available):

```http
200 OK
Content-Type: application/json

{
  "future_id": "1234567890"
}
```

The homeserver can optionally enforce a maximum timeout duration. If the requested timeout exceeds the maximum the homeserver
can respond with a [`400`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400) and a Matrix error code `M_FUTURE_MAX_TIMEOUT_EXCEEDED` and the maximum allowed timeout (`timeout_duration` in milliseconds).

For example the following specifies a maximum delay of 24 hours:

```http
400 Bad Request
Content-Type: application/json

{
  "errcode": "M_FUTURE_MAX_TIMEOUT_EXCEEDED",
  "error": "The requested timeout exceeds the allowed maximum.",
  "timeout_duration": 86400000
}
```

### Getting delayed events

We propose adding a new authenticated endpoint `GET /_matrix/client/v0/futures` to the client-server API to allow clients to get a list of all the events that have been scheduled to send in the future.

```http
HTTP 200 OK
Content-Type: application/json

{
  "futures": [
    {
      "future_id": "1234567890",
      "room_id": "!roomid:example.com",
      "event_type": "m.room.message",
      "timeout": 15000,
      "running_since": 1721732853284,
      "content":{
        "msgtype": "m.text",
        "body": "I am now offline"
      }
    },
    {
      "future_id": "abcdefgh",
      "room_id": "!roomid:example.com",
      "event_type": "m.call.member",
      "state_key": "@user:example.com_DEVICEID",
      "timeout": 5000,
      "running_since": 1721732853284,
      "content":{
        "memberships": []
      }
    }
  ]
}
```

`running_since` is the timestamp (as unix time in milliseconds) when the delayed event was scheduled or last refreshed.
So, unless the delayed event is updated beforehand, the event will be sent after `running_since` + `timeout`.

This can be used by clients to display events that have been scheduled to be sent in the future.

For use cases where the existence of a delayed event is also of interest for other room members,
(e.g. self-destructing messages) it is recommended to include this information in the original/affected event itself.

### Managing delayed events

We propose adding a new authenticated client-server API endpoint `POST /_matrix/client/v1/update_future` to manage
delayed events that have already been scheduled.

The body of the request is a JSON object containing the following fields:

- `future_id` - The `future_id` of the delayed event to update.
- `action` - The action to take on the delayed event. Must be one of:
  - `send` - Send the delayed event immediately.
  - `cancel` - Cancel the delayed event so that it is never sent.
  - `refresh` - Restart the timeout of the delayed event.

For example, the following would send the delayed event with `future_id` `1234567890` immediately:

```http
POST /_matrix/client/v1/update_future
Content-Type: application/json

{
  "future_id": "1234567890",
  "action": "send"
}
```

### Homeserver implementation details

#### Power levels are evaluated at the point of sending

Power levels are evaluated for each event only once the delay has occurred and it will be distributed/inserted into the
DAG. This implies a delayed event can fail if it violates power levels at the time the delay passes.

Conversely, it's also possible to successfully schedule an event that the user has no permission to at the time of sending
if the power level situation has changed at the time the delay passes.

#### Delayed events are cancelled by a more recent state event

If a new state event is sent to the same room with the same (event type, state key) pair as a delayed event, the delayed event is cancelled.

There is no race condition here since a possible race between timeout and the _new state event_ will always converge to the _new state event_:

- timeout for _delayed event_ followed by _new state event_: the room state will be updated twice: once by the content of the delayed event but later with the content of _new state event_.
- _new state event_ followed by timeout for _delayed event_: the _new state event_ will cancel the outstanding _delayed event_.

## Use case specific considerations

### MatrixRTC

In this section an overview is given how this MSC is used in [MSC4143: MatrixRTC](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)
and alternative expiration systems are evaluated.

#### Background

MatrixRTC makes it necessary to have real time information about the current MatrixRTC session.
To properly display room tiles and header in the room list (or compute a list of ongoing calls) need to know:

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
  - Use Future events with a 10s timeout to send the disconnected from call
    in less then 10s after the user is not anymore pinging the `/update_future` endpoint.
    (or delegate the disconnect action to a service attached to the SFU)
  - Use the client sync loop as a special case timeout for call member events.
    (See [Alternatives/MSC4018 (use client sync loop))](#msc4018-use-client-sync-loop))

Polling based solution have a big overhead in complexity and network requests on the clients.
Example:

> A room list with 100 rooms where there has been a call before in every room
> (or there is an ongoing call) would require the client to send a to-device message
> (or a request to the SFU) to every user that has an active state event to check if
> they are still online. Just to display the room tile properly.

For displaying the room list timeout based approaches are much more reasonable because this allows computing MatrixRTC
metadata for a room to be synchronous.

The current solution updates the room state every X minutes.
This is not elegant since we basically resend room state with the same content.
In large calls this could result in huge traffic/large DAGs (100 call members
implies 100 state events every X minutes.) X cannot be a long duration because
it is the duration after which we can consider the event as expired. Improper
disconnects would result in the user being displayed as "still in the call" for
X minutes (we want this to be as short as possible!)

Additionally this approach requires perfect server client time synchronization to compute the expiration.
This is currently not possible over federation since `unsigned.age` is not available over federation.

#### How this MSC would be used for MatrixRTC

With this proposal we can provide an elegant solution using actions and timeouts
to only send one event for joining and one for leaving (reliably)

- If the client takes care of its membership, we use a short timeout value (around 5-20 seconds)
  The client will have to ping the refresh endpoint approx every 2-19 seconds.
- When the SFU is capable of taking care of managing our connection state, and we trust the SFU to
  not disconnect, a really long value can be chosen (approx. 2-10hours). The SFU will then only send
  an action once the user disconnects or loses connection (it could even be a different action for both cases
  handling them differently on the client)
  This significantly reduces the amount of calls for the `/update_future` endpoint since the SFU only needs to ping
  once per session (per user) and every 2-5hours (instead of every `X` seconds.)

### Self-destructing messages

This MSC also allows an implementation of "self-destructing" messages using redaction:

First send (or generate the pdu when
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
`PUT /_matrix/client/v1/rooms/{roomId}/send/m.room.redaction/{txnId}?future_timeout=600000`

```jsonc
{
  "redacts": "{event_id}"
}
```

This would redact the message with content: `"m.text": "my msg"` after 10 minutes.

## Potential issues

## Alternatives

### Delegating futures

It is useful for external services to also interact with futures. If a client disconnects an external service can
be the best source to activate the Future/"last will".

This is not covered in this MSC but could be realized with scoped access tokens.
A scoped token for only the `update_future` endpoint and a subset of `future_id`s would be used.

An SFU for instance, that tracks the current client connection state, could be sent a request from the client that it
needs to call every X hours while a user is connected and a request it has to call once the user disconnects
(using a `{"action": "refresh}` and a `{"action": "send"}` `future_update` request.).
This way the SFU can be used as the source of truth for the call member room state even if the client
gets closed or looses connection and without knowing anything about the Matrix call.

### Batch sending

Timed messages, tea timers, reminders or ephemeral events could be implemented
using this where clients send room events with
intentional mentions or a redaction as a future.

In some scenarios it is important to allow to send an event with an associated
future at the same time.

- One example would be redacting an event. It only makes sense to redact the event
  if it exists.
  It might be important to have the guarantee, that the redact is received
  by the server at the time where the original message is sent.
- In the case of a state event we might want to set the state to `A` and after a
  timeout reset it to `{}`. If we have two separate request sending `A` could work
  but the event with content `{}` could fail. The state would not automatically
  reset to `{}`.

For this use case batch sending of multiple futures would be desired.

We do not include batch sending in the proposal of this MSC however since batch sending should
become a generic Matrix concept as proposed with `/send_pdus`. (see: [MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080))

There is a [batch sending version](#batch-sending-futures-with-custom-endpoint) in the Alternatives section
that proposes a future specific group sending endpoint in case this is required sooner then its realistic to implement
[MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080).

### Not reusing the `send`/`state` endpoint

Alternatively new endpoints could be introduced to not overload the `send` and `state` endpoint.
Those endpoints could be called:
`PUT /_matrix/client/v1/rooms/{roomId}/send_future/{eventType}/{txnId}?future_timeout={timeout_duration}`

`PUT /_matrix/client/v1/rooms/{roomId}/state_future/{eventType}/{stateKey}?future_timeout={timeout_duration}`

This would allow the response for the `send` and `state` endpoints intact and we get a different return type
for the new `send_future` and `state_future` endpoints.

### Batch sending futures with custom endpoint

The proposed solution does not allow to send events together with futures that reference them with one  
HTTPS request. This is desired for self-destructing events and for MatrixRTC room state events, where
we want the guarantee, that the event itself and the future removing the event both reach the homeserver
with one request. Otherwise there is a risk for the client to lose connection or crash between sending the  
event and the future which results in never expiring call membership or never destructing self-destructing messages.  
This would be solved once [MSC4080](https://github.com/matrix-org/matrix-spec-proposals/pull/4080) and the `/send_pdus`
endpoint is implemented.
(Then the `future_timeout` could be added
to the `PDUInfo` instead of the query parameters and everything could be send at once.)

This would be the preferred solution since we currently don't have any other batch sending mechanism.  
It would however require lots of changes since a new widget action for futures would be needed.
With the current main proposal it is enough to add a `future_timeout` to the send message
widget action.
The widget driver would then take care of calling `send` or `send_future` based on the presence of those fields.

An alternative to the proposed solution that allows this kind of batch sending would be to
introduce this endpoint:
`PUT /_matrix/client/v1/rooms/{roomId}/send/future/{txnId}`
It allows to send a list of event contents. The body looks as following:

```jsonc
{
  "timeout": 10,

  "send_on_timeout": {
    "type":type,
    "content":timeout_future_content
    },

  // optional
  "send_on_action":{
    "${action1}": {
      "type":type,
      "content":action_future_content
    },
    "${action2}": {
      "type":type,
      "content":action_future_content
    },
    ...
  },

  // optional
  "send_now": content,
}
```

We are sending the timeout and the group id inside the body and combine the timeout future
and the action future into one event.
Each of the `sendEventBody` objects are exactly the same as sending a normal
event.

This is a batch endpoint that sends timeout and action futures at the same time.

#### Batch Response

The response will be a collection of all the futures with the same fields as in the initial proposal:

```jsonc
{
  "send_on_timeout": {
    "future_id": "future_id",
  },
  // optional
  "send_on_action": {
    "${action1}": { "future_id": "future_id1" },
    "${action2}": { "future_id": "future_id2" }
  },

  // optional
  "send_now": { "eventId": "id_hash" }
}
```

Working with futures is the same with this alternative.
This means,

- `GET /_matrix/client/v1/futures` getting running futures
- `POST /_matrix/client/v1/update_future` to canceling, refreshing and sending futures

uses the exact same endpoints.
Also the behaviour of the homeserver on when to invalidate the futures is identical except, that
we don't need the error code `409` anymore since the events are sent as a batch and there cannot be
an action future without a timeout future.

#### Allocating event ID at the point of scheduling the send

This was considered, but when sending a future the `event_id` is not yet available:

The Matrix spec says that the `event_id` must use the [reference hash](https://spec.matrix.org/v1.10/rooms/v11/#event-ids)
which is [calculated from the fields](https://spec.matrix.org/v1.10/server-server-api/#calculating-the-reference-hash-for-an-event)
of an event including the `origin_server_timestamp` as defined in [this list](https://spec.matrix.org/v1.10/rooms/v11/#client-considerations)

Since the `origin_server_timestamp` should be the timestamp the event has when entering the DAG (required for call duration computation) we cannot compute the `event_id` when using the send endpoint when the future has not yet resolved.

#### EventId template variable

It would be useful to be able to send redactions and edits as one HTTP request.
This would handle the cases where the futures need to reference the `send_now` event.
For instance, sending a self-destructing message where the redaction timeout future needs
to reference the event to redact.

For this reason, template variables are introduced that are only valid in `Future` events.
`$m.send_now.event_id` in the content of one of the `send_on_action` and
`send_on_timeout` this template variable can be used.
The **Self-destructing messages** example be a single request:

`PUT /_matrix/client/v1/rooms/{roomId}/send/future/{txnId}`

```jsonc
{
  "m.send_now":{
    "type":"m.room.message",
    "content":{
      "m.text": "my msg"
    }
  },
  "m.timeout": 10*60,
  "m.send_on_timeout": {
    "type":"m.room.redaction",
    "content":{
      "redacts": "$m.send_now.event_id"
    }
  }
}
```

With cryptographic identities events would be presigned.
The server will first send the finalized event to the client.
At this point the client has the id but the event is not in the DAG.
So it would be trivial to sign both the event and the redaction/related event
and then send them via `/send_pdus` (see: [MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080)).

### MSC4018 (use client sync loop)

[MSC4018](https://github.com/matrix-org/matrix-spec-proposals/pull/4018) also
proposes a way to make call memberships reliable. It uses the client sync loop as
an indicator to determine if the event is expired. Instead of letting the SFU
inform about the call termination or using the call app ping loop like we propose
here.

The advantage is, that this does not require us to introduce a new refresh token type.
With cryptographic identities we however need the client to create the leave event.

The timeout for syncs are much slower than what would be desirable (30s vs 5s).

With a widget implementation for calls we cannot guarantee that the widget is running during the sync loop.
So one either has to move the hangup logic to the hosting client or let the widget run all the time.

With a dedicated ping (independent to the sync loop) it is more flexible and allows us to let the widget
execute the refresh.
If the widget dies, the call membership will disconnect.

### Federated futures

The delayed/scheduled events could be sent over federation immediately and then have the receiving servers process them at the appropriate time.

### MQTT style Last Will

[MQTT](https://mqtt.org/) has the concept of a Will Message that is published by the server when a client disconnects.

The client can set a Will Message when it connects to the server. If the client disconnects unexpectedly the server will publish the Will Message if the client is not back online within a specified time.

A similar concept could be applied to Matrix by having the client specify a set of "Last Will" event(s) and have the homeserver trigger them if the client (possibly identified by device ID) does not send an API request within a specified time.

### Naming

The following alternative names for this concept are considered

- Future
- DelayedEvents
- PostponedEvents
- LastWill

## Security considerations

Servers SHOULD impose a maximum timeout value for future timeouts of not more than a month.

## Unstable prefix

Whilst the MSC is in the proposal stage, the following should be used:

- `org.matrix.msc4140.future_timeout` should be used instead of the `future_timeout` query parameter.
- `POST /_matrix/client/unstable/org.matrix.msc4140/update_future` should be used instead of the `POST /_matrix/client/v1/update_future` endpoint.
- `GET /_matrix/client/unstable/org.matrix.msc4140/futures` should be used instead of the `GET /_matrix/client/v0/futures` endpoint.
- The `M_UNKNOWN` `errcode` should be used instead of `M_FUTURE_MAX_TIMEOUT_EXCEEDED` as follows:

```json
{
  "errcode": "M_UNKNOWN",
  "error": "The requested timeout exceeds the allowed maximum.",
  "org.matrix.msc4140.errcode": "M_FUTURE_MAX_TIMEOUT_EXCEEDED",
  "org.matrix.msc4140.timeout_duration": 86400000
}
```

instead of:

```json
{
  "errcode": "M_FUTURE_MAX_TIMEOUT_EXCEEDED",
  "error": "The requested timeout exceeds the allowed maximum.",
  "timeout_duration": 86400000
}
```

Additionally, the feature is to be advertised as unstable feature in the `GET /_matrix/client/versions` response, with the key `org.matrix.msc4140` set to `true`. So, the response could look then as following:

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
