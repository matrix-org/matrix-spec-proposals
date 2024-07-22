# MSC4140: Delayed events (Futures)

<!-- TOC -->

- [MSC4140: Delayed events Futures](#msc4140-delayed-events-futures)
    - [Proposal](#proposal)
        - [Response](#response)
        - [Interacting with futures](#interacting-with-futures)
        - [Delegating futures](#delegating-futures)
        - [Batch sending](#batch-sending)
        - [Getting running futures](#getting-running-futures)
    - [Usecase specific considerations](#usecase-specific-considerations)
        - [MatrixRTC](#matrixrtc)
            - [Background](#background)
            - [How this MSC would be used for MatrixRTC](#how-this-msc-would-be-used-for-matrixrtc)
        - [Self-destructing messages](#self-destructing-messages)
    - [Potential issues](#potential-issues)
    - [Alternatives](#alternatives)
        - [Not reusing the send/state endpoint](#not-reusing-the-sendstate-endpoint)
        - [Batch sending futures with custom endpoint](#batch-sending-futures-with-custom-endpoint)
            - [Batch Response](#batch-response)
            - [EventId template variable](#eventid-template-variable)
        - [MSC4018 use client sync loop](#msc4018-use-client-sync-loop)
        - [Naming](#naming)
    - [Security considerations](#security-considerations)
    - [Unstable prefix](#unstable-prefix)
    - [Dependencies](#dependencies)

<!-- /TOC -->

The motivation for this MSC is: Updating call member events after the user disconnected by allowing to
schedule/delay/timeout/expire events in a generic way.
It is best to first read [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) and in particular
the section: ["Reliability requirements for the room state"](https://github.com/matrix-org/matrix-spec-proposals/blob/toger5/matrixRTC/proposals/4143-matrix-rtc.md#reliability-requirements-for-the-room-state)
to understand the MatrixRTC usecase of this MSC.

It turns out that there is a big overlap to other usecases in Matrix which can also be implemented using the proposed concept:

- Updating call member events after the user disconnected.
- Sending scheduled messages (send at a specific time).
- Creating self-destructing events (by sending a delayed redact).

Currently there is no mechanism for a client to reliably share that they are not part of a call anymore.
A network issue can disconnect the client. The call is not working anymore and for that user the call ended.
Since the only way to update an event is to post a new one the room state will not represent the correct call state
until the user rejoins and disconnects intentionally so the client is still online sending/updating the room state
without this devices call membership.

The same happens if the user force quits the client without pressing the hangup button. (For example closing a browser tab.)

There are numerous possible solution to solve the call member event expiration. They are covered in detail
in the [Usecase specific considerations/MatrixRTC](#usecase-specific-considerations) section, because they are not part
of this proposal.
Here, in the introduction, only an overview of considered options is given:

- expiration using timestamp logic.
- expiration using bots/appservices.
- expiration with to-device messages/sfu polling.
- expiration with custom synapse logic based on the client sync loop.

This covers how events can be queued for sending after a "passive termination" event.
The client is not in a state anymore to actually send requests, the server detects this
(by missing heartbeat pings) and sendes the pre-sent event.
This is sometimes called "last will" in other technologies.

## Proposal

When an event is scheduled for sending the client gets a temporal so called `future_id`
to control when to actually send these events.
This allows a very flexible way to mark events as expired.
The sender predefines the event that will be sent once the condition "the client does not sent heartbeat pings"
anymore is met.
For call state events the future/"last will" version of the event would
be an event where the content communicates, that
the users has left the call.

Using the `future_id` the client can refresh the timeout. Allowing to delay the event multiple times.
A periodic refresh ping using this `future_id` can be used as a heartbeat mechanism. Once the refresh ping is not send
anymore the timeout condition is met and the homeserver sends the event with the expired content information.

This translate to: _"only send the event when the client is not running its program anymore (not sending the heartbeat anymore)"_
We call those delayed events `Futures`.

Futures reuse the `send` and `state` endpoint and extend them with an optional `future_timeout` query parameter.

`PUT /_matrix/client/v1/rooms/{roomId}/send/{eventType}/{txnId}?future_timeout={timeout_duration}`

`PUT /_matrix/client/v1/rooms/{roomId}/state/{eventType}/{stateKey}?future_timeout={timeout_duration}`

The `future_timeout` query parameter is used to configure the event scheduling:

- `future_timeout: number` defines how long (in milliseconds) the homeserver will wait before sending
  the event into the room. **Note**, since the timeout can be refreshed and sending the future can be triggered via an
  endpoint (see: [Proposal/Delegating futures](#delegating-futures)) this value is not enough to predict the time this
  event will arrive in the room.

Possible error responses are all error responses that can occur when using the `send` and `state` endpoint accordingly.
Additionally the following can occur:

- The server can optionally configure a maximum `timeout_duration`
  (In the order of one week dependent on how long they want to track futures)
  The server will respond with a [`400`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400) (`Bad Request`,
  with a matrix error code `M_FUTURE_MAX_TIMEOUT_EXCEEDED`
  containing the maximum allowed `timeout_duration`) if the
  client tries to send a timeout future with a larger `timeout_duration`.

The body is the same as [sending a normal event](https://spec.matrix.org/v1.11/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid)
or [sending a state event](https://spec.matrix.org/v1.11/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey).

Power levels are evaluated for each event only once the trigger has occurred and it will be distributed/inserted into the
DAG.
This implies a future can fail if it violates power levels at the time it resolves.
(It's also possible to successfully send a future the user has no permission to at the time of sending
if the power level situation has changed at the time the future resolves.)

### Response

When sending a future the `event_id` is not yet available:

- The `event_id` is using the [reference hash](https://spec.matrix.org/v1.10/rooms/v11/#event-ids) which is
  [calculated via the essential fields](https://spec.matrix.org/v1.10/server-server-api/#calculating-the-reference-hash-for-an-event)
  of an event including the `origin_server_timestamp` as defined in [this list](https://spec.matrix.org/v1.10/rooms/v11/#client-considerations)
- Since the `origin_server_timestamp` should be the timestamp the event has when entering the DAG
  (required for call duration computation)
  we cannot compute the `event_id` when using the send endpoint when the future has not yet resolved.

So the response will include a custom `future_id` but no `event_id`,
if the request was sent with the `future_timeout` parameter.
A request without query parameters would
get a response with an `event_id` (as before).

As a result the return type changes to:

```jsonc
{
  "event_id": "1234", // string | undefined
  "future_id": "2345" //string | undefined,
}
```

For a future event the response looks as following:

```jsonc
{
  "future_id": "1234" // string,
}
```

Each `future_id` is a UUID similar to an `event_id`s. It is computed on the homeserver.
It can optionally be used to interact with futures.

### Interacting with futures

This MSC also proposes a authenticaed EDU endpoint: `update_future`.
The `future_id` can be used to send an EDUs to the `update_future` endpoint:
`POST /_matrix/client/v1/update_future`
using the following EDU body:

```jsonc
{
  "future_id": "1234567890", // UUID
  "action": "send" // "send"|"cancel"|"refresh,
}
```

The homeserver does the following when receiving a Future:

- It checks for the validity of the request (based on the `future_timeout` query parameter)
  and returns a `400` or `410` if necessary.
- It **generates** a `future_id`.
- It **Starts a timer** for the Future using the `future_timeout` value.

  - If a `POST /_matrix/client/v1/update_future`, `{"action": "refresh"}` is received, it
    **restarts the timer** with the stored `timeout_duration` for the associated timeout future.
  - If a `POST /_matrix/client/v1/update_future`, `{"action": "send"}` is received, it
    **sends the associated action or timeout future**
  - If a `POST /_matrix/client/v1/update_future`, `{"action": "cancel"}` is received, it **does NOT send any future**
    and deletes/invalidates the associated stored future.
  - If a `POST /_matrix/client/v1/update_future` `{"future_id": "unknown"}` is received the server responds
    with a `410` (Gone).
  - If a timer times out, **it sends the timeout future**.
  - If the homeserver receives a _new state event_ with the same state key as existing futures the
    **futures get invalidated and the associated timers are stopped**.

    - There is no race condition here since a possible race between timeout and
      the _new state event_ will always converge to the _new state event_:
      - Timeout -> _new state event_: the room state will be updated twice. once by
        the content of the future but later with the content of _new state event_.
      - _new state event_ -> timeout: the _new state event_ will invalidate the future.

- After the homeservers sends a timeout future, the associated
  timer is deleted.

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

For this usecase batch sending of multiple futures would be desired.

We do not include batch sending in the proposal of this MSC however since batch sending should
become a generic Matrix concept as proposed with `/send_pdus`. (see: [MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080))

There is a [batch sending version](#batch-sending-futures-with-custom-endpoint) in the Alternatives section
that proposes a future specific group sending endpoint in case this is required sooner then its realistic to implement
[MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080).

### Getting running futures

Using `GET /_matrix/client/v0/futures` it is possible to get the list of all running futures issues by the authenticated
user. This is an authenticated endpoint. It sends back the json of the final event content with the associated tokens.

```jsonc
[
  {
    "url":"/_matrix/client/v1/rooms/{roomId}/send_future/{eventType}/{txnId}?future_timeout={timeout_duration}",
    "body":{
      ...event_body
    },
    "response":{
      "future_id": UUID,
      "last_refresh": Time,
      "timeout": Number | undefined,
    }
  },
]
```

This can be used so clients can optionally display events
that will be send in the future.

For all usecases where the existence of a running future is also of interest for other room members,
(like self-destructing messages) it is recommended to include
this information in the effected event itself.

## Usecase specific considerations

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
- When the SFU is capable of taking care of managing our connection state and we trust the SFU to
  not disconnect a really long value can be chosen (approx. 2-10hours). The SFU will then only send
  an action once the user disconnects or looses connection (it could even be a different action for both cases
  handling them differently on the client)
  This significantly reduces the amount of calls for the `/update_future` endpoint since the SFU only needs to ping
  once per session (per user) and every 2-5hours (instead of every `X` seconds.)

### Self-destructing messages

This MSC also allows to implement self-destructing messages:

First send (or generate the pdu when
[MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080)
is available):
`PUT /_matrix/client/v1/rooms/{roomId}/send/{eventType}/{eventType}/{txnId}`

```jsonc
{
  "m.text": "my msg"
}
```

then send:
`PUT /_matrix/client/v1/rooms/{roomId}/send_future/{eventType}/{txnId}?timeout={10*60}`

```jsonc
{
  "redacts": "{event_id}"
}
```

This would redact the message with content: `"m.text": "my msg"` after 10minutes.

## Potential issues

## Alternatives

### Not reusing the `send`/`state` endpoint

Alternatively new endpoints could be introduced to not oveload the `send` and `state` endpoint.
Those endpoints would be called:
`PUT /_matrix/client/v1/rooms/{roomId}/send_future/{eventType}/{txnId}?future_timeout={timeout_duration}`

`PUT /_matrix/client/v1/rooms/{roomId}/state_future/{eventType}/{stateKey}?future_timeout={timeout_duration}`

This keeps the response type of the `send` and `state` endpoint in tact and we get a different return type
the new `send_future` and `state_future` endpoint.

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
Also the behaviour of the homeserver on when to invalidate the furures is identical except, that
we don't need the error code `409` anymore since the events are sent as a batch and there cannot be
an action future without a timeout future.

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
    "type":"m.room.readact",
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

With a dedicated ping (independent to the sync loop) it is more felxibale and allows us to let the widget
execute the refresh.
If the widget dies, the call membership will disconnect.

### Naming

The following alternative names for this concept are considered

- Future
- DelayedEvents
- PostponedEvents
- LastWill

## Security considerations

Servers SHOULD impose a maximum timeout value for future timeouts of not more than a month.

## Unstable prefix

Use `org.matrix.msc4140.` instead of `m.` as long as the MSC is not stable.
For the endpoints introduced in this MSC use the prefix `/org.matrix.msc4140/` and set the paths version string to unstable,
instead of v#.

## Dependencies
