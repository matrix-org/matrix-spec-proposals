# MSC4140: Delayed events (Futures)

<!-- TOC -->

- [MSC4140: Delayed events Futures](#msc4140-delayed-events-futures)
  - [Proposal](#proposal)
    - [Response](#response)
    - [Delegating futures](#delegating-futures)
    - [Getting running futures](#getting-running-futures)
  - [Usecase specific considerations](#usecase-specific-considerations)
    - [MatrixRTC](#matrixrtc)
      - [Background](#background)
      - [How this MSC would be used for MatrixRTC](#how-this-msc-would-be-used-for-matrixrtc)
    - [Self-destructing messages](#self-destructing-messages)
  - [Potential issues](#potential-issues)
  - [Alternatives](#alternatives)
    - [Reusing the send/state endpoint](#reusing-the-sendstate-endpoint)
    - [Batch sending futures with custom endpoint](#batch-sending-futures-with-custom-endpoint)
    - [MSC4018 use client sync loop](#msc4018-use-client-sync-loop)
    - [Naming](#naming)
  - [Security considerations](#security-considerations)
  - [Unstable prefix](#unstable-prefix)
  - [Dependencies](#dependencies)

<!-- /TOC -->

The motivation for this MSC is: Updating call member events after the user disconnected by allowing to schedule/delay/timeout/expire events in a generic way.
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
in the [Usecase specific considerations/MatrixRTC](#usecase-specific-considerations) section, because they are not part of the actual proposal.
In the introduction only an overview of considered options is given:

- expiration using timestamp logic.
- expiration using bots/appservices.
- expiration with to-device messages/sfu polling.
- expiration with custom synapse logic based on the client sync loop.

The preferred solution requires us to send an event to the homeserver in advance,
but let the homeserver decide the time/condition when its actually added to the DAG.
The condition for actually sending the delayed event could be a timeout or an external trigger
via an unauthenticated Synapse endpoint.
The Proposal section of this MSC will focus on how to achieve this.

## Proposal

To make this as generic as possible, the proposed solution is to allow sending events and delegate
the control of when to actually send these events to an external service or a timeout condition.
This allows a very flexible way to mark events as expired.
The sender can define what event will be sent once the timeout condition is met. For state
events the timed out version of the event would be an event where the content communicates, that
the users has left the call.

This proposal also includes a way to refresh the timeout. Allowing to delay the event multiple times.
A periodic ping of the refreshing can be used as a heartbeat mechanism. Once the refresh ping is not send
anymore the timeout condition is met and the homeserver sends the event with the expired content information.

This translate to: _"only send the event when the client is not running its program anymore (not sending the heartbeat anymore)"_
We call those delayed events `Futures`.

New endpoints are introduced:

`PUT /_matrix/client/v3/rooms/{roomId}/send_future/{eventType}/{txnId}?future_timeout={timeout_duration}&future_group_id={group_id}`

`PUT /_matrix/client/v3/rooms/{roomId}/state_future/{eventType}/{stateKey}?future_timeout={timeout_duration}&future_group_id={group_id}`

Those behave like the normal `send`/`state` endpoints except that that they allow
to define `future_timeout` and `future_group_id` in their query parameters.

- `future_timeout: number` defines how long (in milliseconds) the homeserver will wait before sending
  the event into the room. **Note**, since the timeout can be refreshed and sending the future can be triggered via an endpoint (see: [Proposal/Delegating futures](#delegating-futures)) this value is not enough to predict the time this event will arrive in the room.
  - If this query parameter is not added the future will never expire and can only be send by the [external delegation endpoint](#delegating-futures).
    We call such a future **action future**.
  - If set to a `number` (ms) we call the future **timeout future**
- `future_group_id: string` is optional if a `future_timeout` is a `number`. The purpose of this identifier is to group
  **multiple futures in one mutually exclusive group**.
  - Only one of the events in such a group can ever reach the DAG/will be distributed by the homeserver.
    All other futures will be discarded.
  - Every future group needs at least one timeout future to guarantee that all future expire eventually.
  - If a timeout future is sent without a `future_group_id` a unique identifier will be generated by the
    homeserver and is part of the `send_future` response.
  - Group id's can only be used by one user. Reasons for this are, that this would basically allow full control over a future group once another matrix user knows the group id. It would also require to federate futures if the users are not on the same homeserver.

Both of the query parameters are optional but one of them has to be present.
This gives us the following options:

```
?future_timeout=10 - a timeout future in a new future group
?future_timeout=10&future_group_id="groupA" - a timeout future added to groupA
?future_group_id="groupA" - an action future added to groupA
```

Possible error responses are all error responses that can occur when using the `send` and `state` endpoint accordingly and:

- The server will respond with a [`409`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/409)
  (`Conflict` This response is sent when a request conflicts with the current state of the server.) if
  the client tries to send an action future without there being a timeout future with the same `future_group_id`
- The server can optionally configure a maximum `timeout_duration`
  (In the order of one week dependent on how long they want to track futures)
  The server will respond with a [`400`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400) (`Bad Request`, with a message
  containing the maximum allowed `timeout_duration`) if the
  client tries to send a timeout future with a larger `timeout_duration`.
- The future is using a group_id that belongs to a future group from another user. In this case the homeserver sends a [`405`] (`Not Allowed`).

The body is the same as sending a normal event.

Power levels are evaluated for each event only once the trigger has occurred and it will be distributed/inserted into the DAG.
This implies a future can fail if it violates power levels at the time it resolves.
(It's also possible to successfully send a future the user has no permission to at the time of sending
if the power level situation has changed at the time the future resolves.)

### Response

The response will include a `send_token`, `cancel_token`, the associated `future_group_id` and an optional `refresh_token` but no `event_id` since the `event_id` depends on the `origin_server_ts` which is not yet determined. A timeout future will contain `refresh_token` but an action future will not.

```json
{
  // always present
  "send_token": "send_token",
  "cancel_token": "cancel_token",
  "future_group_id": "group_id",
  // optional, only present if its a a timeout future response
  "refresh_token": "refresh_token"
}
```

### Delegating futures

This MSC also proposes a `futures` endpoint.
The `token` can be used to call this public `futures` endpoint:
`POST /_matrix/client/v3/future/{token}`

The information required to call this endpoint is minimal so that
no metadata is leaked when sharing the refresh/send url with a third party.
Since the refresh and send tokens are of the same format it is not even possible to evaluate
what that token is for when reading the https request log.
This unauthenticated endpoint allows to delegate resolving the future.
An SFU for instance, that tracks the current client connection state, could get a url that it
needs to call every X hours while a user is connected and a url it has to call once the user disconnects.
This way the SFU can be used as the source of truth for the call member room state even if the client
gets closed or looses connection and without knowing anything about the Matrix call.

The homeserver does the following when receiving a Future:

- It checks for the validity of the request (based on the `future_timeout` and the `future_group_id` query parameters)
  and returns a `409`, `400` or `405` if necessary.
- It **generates** a `send_token`, a `cancel_token` and if not provided in the request a `future_group_id` and a optionally `refresh_token` and stores them alongside the time
  of retrieval and the `timeout_duration`.
- If `future_timeout` was present, it **Starts a timer** for the `refresh_token`.

  - If a `POST /_matrix/client/v3/future/{refresh_token}` is received, it
    **restarts the timer** with the stored `timeout_duration` for the associated timeout future.
  - If a `POST /_matrix/client/v3/future/{send_token}` is received, it **sends the associated action or timeout future**
    and deletes any stored futures with the `group_id` associated with that token.
  - If a `POST /_matrix/client/v3/future/{cancel_token}` is received, it **does NOT send any future**
    and deletes/invalidates the associated stored future. This can mean that a whole future group gets deleted (see below).
  - If a `POST /_matrix/client/v3/future/{unknown_token}` is received the server responds with a `410` (Gone).
    An `unknown_token` either means that the service is making something up or that the service is using a
    token that is invalidated by now.
  - If a timer times out, **it sends the timeout future**.
  - If the homeserver receives a _new state event_ with the same state key as existing futures the
    **futures get invalidated and the associated timers are stopped**.

    - There is no race condition here since a possible race between timeout and
      the _new state event_ will always converge to the _new state event_:
      - Timeout -> _new state event_: the room state will be updated twice. once by
        the content of the future but later with the content of _new state event_.
      - _new state event_ -> timeout: the _new state event_ will invalidate the future.

- After the homeservers sends a timeout future or action future, the associated
  timer and tokens is canceled/deleted.

So for each `future_group_id`, the homeserver will at most send one timeline event.

- No timeline event will be send in case all of the timeout futures in a future group are cancelled via `/_matrix/client/v3/future/{cancel_token}`.
- Otherwise one of the timeout or action futures will be send.

**Rate limiting** the `POST /_matrix/client/v3/future/{token}`endpoint:

- A malicious party can try to find a correct token by randomly sending requests to this endpoint.
- Homeservers should rate limit this endpoint so that one can at
  most send `N` invalid tokens in a row and then will get a `429` (Too Many Requests)
  response for `T` seconds. We allow `N` invalid tokens because it is not
  easy to compute if a token is still valid or not so it is useful to ask for this.
- The recommended values for `T` are 10 seconds and for `N` 5. (It is spec conform to use other values.)

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
that proposes a future specific group sending endpoint in case this is required sooner then its realistic to implement [MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080).

### Getting running futures

Using `GET /_matrix/client/v3/future` it is possible to get the list of all running futures issues by the authenticated user.
This is an authenticated endpoint. It sends back the json
of the final event content with the associated tokens.

```json
[
  {
    "url":"/_matrix/client/v3/rooms/{roomId}/send_future/{eventType}/{txnId}?future_timeout={timeout_duration}&future_group_id={group_id}",
    "body":{
      ...event_body
    },
    "response":{
      // always present
      "send_token": "send_token",
      "cancel_token": "cancel_token",
      "future_group_id": "group_id",
      // optional if there is a timeout
      "refresh_token": "token",
    }
  },
]
```

This can be used so clients can optionally display events
that will be send in the future.
And to acquire cancel_tokens for then.

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
    in less then 10s after the user is not anymore pinging the `/refresh` endpoint.
    (or delegate the disconnect action to a service attached to the SFU)
  - Use the client sync loop as a special case timeout for call member events.
    (See [Alternatives/MSC4018 (use client sync loop))](#msc4018-use-client-sync-loop))

Polling based solution have a big overhead in complexity and network requests on the clients.
Example:

> A room list with 100 rooms where there has been a call before in every room
> (or there is an ongoing call) would require the client to send a to-device message
> (or a request to the SFU) to every user that has an active state event to check if
> they are still online. Just to display the room tile properly.

For displaying the room list timeout based approaches are much more reasonable because this allows computing MatrixRTC metadata for a room to be synchronous.

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
  This significantly reduces the amount of calls for the `/future` endpoint since the sfu only needs to ping
  once per session (per user) and every 2-5hours (instead of every `X` seconds.)

### Self-destructing messages

This MSC also allows to implement self-destructing messages:

First send (or generate the pdu when
[MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080)
is available):
`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{eventType}/{txnId}`

```json
{
  "m.text": "my msg"
}
```

then send:
`PUT /_matrix/client/v3/rooms/{roomId}/send_future/{eventType}/{txnId}?timeout={10*60}&future_group_id={XYZ}`

```json
{
  "redacts": "{event_id}"
}
```

This would redact the message with content: `"m.text": "my msg"` after 10minutes.

## Potential issues

## Alternatives

### Reusing the `send`/`state` endpoint

Since the `send_future` and `state_future` endpoints are almost identical to the
normal `send` and `state` endpoints it comes to mind, that one could reuse them and allow adding the
query parameters `?future_timeout={timeout_duration}&future_group_id={group_id}` directly to the
`send` and `state` endpoint.

This would be elegant but since those two endpoint are core to Matrix, changes to them might  
be controversial if their return value is altered.

Currently they always return

```json
{
  "event_id":string
}
```

as a non optional field.

When sending a future the `event_id` would not be available:

- The `event_id` is using the [reference hash](https://spec.matrix.org/v1.10/rooms/v11/#event-ids) which is
  [calculated via the essential fields](https://spec.matrix.org/v1.10/server-server-api/#calculating-the-reference-hash-for-an-event)
  of an event including the `origin_server_timestamp` as defined in [this list](https://spec.matrix.org/v1.10/rooms/v11/#client-considerations)
- Since the `origin_server_timestamp` should be the timestamp the event has when entering the DAG (required for call duration computation)
  we cannot compute the `event_id` when using the send endpoint when the future has not yet resolved.

As a result the return type would change to:

```json
{
  "event_id": string | undefined,
  "future_group_id": string | undefined,
  "send_token": string | undefined,
  "refresh_token": string | undefined,
  "cancel_token": "string | undefined
}
```

dependent on the query parameters.

### Batch sending futures with custom endpoint

The proposed solution does not allow to send events together with futures that reference them with one  
HTTPS request. This is desired for self-destructing events and for MatrixRTC room state events, where
we want the guarantee, that the event itself and the future removing the event both reach the homeserver
with one request. Otherwise there is a risk for the client to lose connection or crash between sending the  
event and the future which results in never expiring call membership or never destructing self-destructing messages.  
This would be solved once [MSC4080](https://github.com/matrix-org/matrix-spec-proposals/pull/4080) and the `/send_pdus` endpoint is implemented.
(Then the `future_timeout` and `future_group_id` could be added
to the `PDUInfo` instead of the query parameters and everything could be send at once.)

This would be the preferred solution since we currently don't have any other batch sending mechanism.  
It would however require lots of changes since a new widget action for futures would be needed.
With the current main proposal it is enough to add a `future_timeout` and `future_group_id` parameter to the send message widget action.
The widget driver would then take care of calling `send` or `send_future` based on the presence of those fields.

An alternative to the proposed solution that allows this kind of batch sending would be to
introduce this endpoint:
`PUT /_matrix/client/v3/rooms/{roomId}/send/future/{txnId}`
It allows to send a list of event contents. The body looks as following:

```json
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

**Response**

The response will be a collection of all the futures with the same fields as in the initial proposal:

```json
{
  "send_on_timeout": {
    "send_token": "token",
    "refresh_token": "token",
    "cancel_token": "token"
  },
  // optional
  "send_on_action": {
    "${action1}": { "send_token": "token" },
    "${action2}": { "send_token": "token" }
  },

  // optional
  "send_now": { "eventId": "id_hash" }
}
```

We do not need a `future_group_id` since we will send one group in one request.

Working with futures is the same with this alternative.
This means,

- `GET /_matrix/client/v3/future` getting running futures
- `POST /_matrix/client/v3/future/{token}` cancel, refreshing and sending futures

uses the exact same endpoints.
Also the behaviour of the homeserver on when to invalidate the furures is identical except, that
we don't need the error code `409` anymore since the events are sent as a batch and there cannot be
an action future without a timeout future.

**EventId template variable**

It would be useful to be able to send redactions and edits as one HTTP request.
This would handle the cases where the futures need to reference the `send_now` event.
For instance, sending a self-destructing message where the redaction timeout future needs
to reference the event to redact.

For this reason, template variables are introduced that are only valid in `Future` events.
`$m.send_now.event_id` in the content of one of the `send_on_action` and
`send_on_timeout` this template variable can be used.
The **Self-destructing messages** example be a single request:

`PUT /_matrix/client/v3/rooms/{roomId}/send/future/{txnId}`

```json
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

### Naming

The following alternative names for this concept are considered

- Future
- DelayedEvents
- RetardedEvents
- PostponedEvents

## Security considerations

We are using an unauthenticated endpoint to refresh the expirations. Since we use
generated tokens it is hard to guess a correct request and force sending one
of the Futures. (The homeserver has them but they can always send events in your name
as long as we do not have [MSC4080: Cryptographic Identities](https://github.com/matrix-org/matrix-spec-proposals/pull/4080))

It is an intentional decision to not provide an endpoint like
`PUT /_matrix/client/v3/future/room/{roomId}/event/{eventId}`
where any client with access to the room could also `end` or `refresh`
the expiration. With the token the client creating the future has ownership
over the expiration and only intentional delegation of that ownership
(sharing the token) is possible.

On the other hand the token makes sure that the instance gets as little
information about the Matrix metadata of the associated `future` event. It cannot
even tell with which room or user it is interacting or what the token does (refresh vs send).

## Unstable prefix

Use `io.element.msc3140.` instead of `m.` as long as the MSC is not stable.
For the endpoints introduced in this MSC use the prefix `/io.element.msc3140/` and set the paths version string to unstable, instead of v#.

## Dependencies
