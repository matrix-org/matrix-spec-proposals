# MSC4471: Event streams

Matrix clients increasingly need to display rapidly changing, non-durable state which is associated
with a room event. A common example is an AI assistant generating a response: users benefit from seeing
the answer arrive incrementally, but intermediate text should not become room history.

This MSC defines a way for a room event to have a live, non-durable companion stream. Clients can show
the stream while the event is changing, then discard it once the final content is committed to the room.
The stream is intended for active viewers rather than durable history, and delivery is best effort.

The mechanism is intentionally not AI-specific. This MSC defines replacement and append operations for
message-like content, but future MSCs could reuse the same transport for other transient room-associated
state, such as live location streaming.


## Proposal

This MSC introduces "event streams". An event stream is identified by a room event and has a publisher
device and optional encryption information.

A stream has four protocol elements:

* a descriptor in a durable room event that declares this event will have streaming updates
* `m.stream.subscribe` to-device events sent by subscriber devices to the publisher device
* `m.stream.cancel` to-device events sent by either side to cancel subscriptions
* `m.stream.update` to-device events sent by the publisher device to subscriber devices

Stream updates are transient. They are not inserted into the room DAG, are not state, are not returned
by room history APIs, and must not create push notifications, unread counts, receipts, or relations.
Once the stream is complete, the sender should edit the room event which advertised the stream with the
final event content and omit the stream descriptor from the replacement content.

To avoid introducing a new client-server endpoint, federation EDU, or sync token field, this proposal
is implemented using To-Device events, including the existing `/sendToDevice` API, direct-to-device
federation, and `to_device.events` delivery in `/sync`. No homeserver work is required to implement
this proposal.


### Stream descriptor

A room event may advertise a stream by including an `m.stream` property in its content.

For `m.room.message`, the field is in the normal message content object:

```json
{
  "msgtype": "m.text",
  "body": "Generating response...",
  "m.stream": {
    "device_id": "DEVICEID",
    "expiry_ms": 1800000
  }
}
```

The `m.stream` object has the following fields:

* `device_id`: Required string. The publisher device ID to which subscriptions should be sent. This
  device must be owned by the sender of the room event containing the descriptor.
* `expiry_ms`: Optional integer. The lifetime of the descriptor in milliseconds, counted from the
  room event's `origin_server_ts`. If omitted, clients should assume a short implementation-defined
  lifetime.
* `encryption`: Optional object. Described below.

The descriptor is scoped to the room event which contains it. The stream identifier used by this MSC is
therefore the tuple `(room_id, event_id)`.


### Subscribing

After receiving a room event with an `m.stream` descriptor, a device may subscribe by sending a
to-device event of type `m.stream.subscribe` to the sender of the containing room event and the
descriptor's `device_id`.

As streams incur additional load on the subscriber, the publisher, and the intermediate homeservers,
Clients should only subscribe to a stream when the event containing the descriptor is currently visible
to the user, such as when the room is open and the event is in view. If the event is not currently
visible, the client should not subscribe and should instead wait to receive the final edit containing the
complete event content.

The content of `m.stream.subscribe` is:

```json
{
  "room_id": "!room:example.org",
  "event_id": "$event:example.org",
  "subscriber_device_id": "SUBSCRIBERDEVICE",
  "resync": false
}
```

The fields are:

* `room_id`: Required string. The room containing the stream descriptor.
* `event_id`: Required string. The event containing the stream descriptor.
* `subscriber_device_id`: Required string. The subscriber device which should receive updates.
* `resync`: Optional boolean. If true, the subscriber device requests a fresh `op: "replace"` baseline.
  If omitted, false is assumed.

The publisher device should accept the subscription only if:

* it is the device named by the descriptor's `device_id`
* it has a registered active stream for `(room_id, event_id)`
* the requested `subscriber_device_id` is non-empty and belongs to the subscribing user
* the subscribing user is allowed to see the room event containing the descriptor and receive the stream:
  * the subscribing user should currently be joined to the room and be allowed to see the descriptor event
    under normal room history visibility rules
  * for encrypted streams, the requested subscriber device should be eligible to receive encrypted room
    content under the publisher device's E2EE trust policy.

Either side may cancel a subscription by sending an `m.stream.cancel` to-device event for the
subscription tuple. If the publisher device rejects a subscription, it should send `m.stream.cancel` to
the subscribing user. A subscriber device may send `m.stream.cancel` to the publisher device when it no
longer wants updates for the stream. The content of `m.stream.cancel` is:

```json
{
  "room_id": "!room:example.org",
  "event_id": "$event:example.org",
  "subscriber_device_id": "SUBSCRIBERDEVICE",
  "code": "m.unknown_stream",
  "reason": "Unknown or expired stream"
}
```

The fields are:

* `room_id`: Required string. The room containing the stream descriptor.
* `event_id`: Required string. The event containing the stream descriptor.
* `subscriber_device_id`: Required string. The subscriber device whose subscription is cancelled.
* `code`: Required string. A machine-readable reason for the cancellation.
* `reason`: Optional string. A human-readable reason for debugging. Clients should not rely on this value.

This MSC defines the following cancellation codes:

* `m.unknown_stream`: The publisher device does not have an active stream for the requested descriptor,
  or the descriptor has expired.
* `m.invalid_subscription`: The subscription request is malformed or names an invalid subscriber device.
* `m.forbidden`: The publisher device declined because the subscriber is not allowed to receive updates.
* `m.limit_exceeded`: The publisher device declined because of implementation limits.
* `m.user_cancelled`: The subscriber device no longer wants updates for the stream.

An accepted subscription remains active until either side cancels it, the stream completes, or the
descriptor expires. A subscriber device should cancel its subscription when it no longer wants updates,
such as when the event leaves view. A publisher device must not send updates for an expired descriptor.
If a duplicate subscription is accepted and `resync` is false or omitted, the publisher device should not
resend already-sent stream content.

### Message stream updates

The publisher device sends updates to active subscribers using to-device events of type
`m.stream.update`. Each update either replaces or appends to the transient `body` being rendered for the
streamable event.

For such message-like streams, each `m.stream.update` has the following fields:

* `room_id`: Required string. The room containing the stream descriptor.
* `event_id`: Required string. The event containing the stream descriptor.
* `seq`: Required integer. A monotonically increasing sequence number for this subscriber device's view
  of the stream.
* `op`: Required string. One of `replace` or `append`.
* `content`: Required object. The operation payload. It has a required string field, `body`.

The `seq` values in `m.stream.update` content are scoped to the stream as delivered from the publisher
device to a particular subscriber device. They are used for local ordering and deduplication by that
subscriber device, and must not be treated as globally comparable across subscribers.

For `op: "replace"`, clients should replace the current transient `body` with `content.body`.

For `op: "append"`, clients should append `content.body` to the current transient `body`.

Clients should initialize the current transient `body` from the `body` field of the room event
containing the stream descriptor before applying any stream updates. For example, an `op: "append"`
update with `seq: 1` is valid and appends to the descriptor event's initial `body` value.

Stream updates do not replace the containing event's content and cannot add, remove, or modify
`m.stream`, `msgtype`, `format`, `formatted_body`, `m.relates_to`, mentions, or any other message
content fields. After applying a stream update, clients should render the transient `body` and ignore any
current `formatted_body`.

Clients should ignore updates with a `seq` less than or equal to the latest sequence number already
applied for that stream. An `op: "replace"` update is always a valid new baseline, even if there was a
gap before it. If a client receives `op: "append"` after a gap in `seq`, it should stop applying append
updates for that stream and resubscribe with `resync: true` if the stream is still wanted. The client may
continue rendering the last successfully applied transient `body` while waiting for the replacement
baseline.

When a publisher device accepts a subscription and has pending transient `body` content beyond the
descriptor event, it should send either an `op: "append"` update for text beyond the descriptor event's
`body`, or an `op: "replace"` update containing the current complete transient `body`. If `resync` is
true, the publisher should send an `op: "replace"` update. It should continue sending `op: "append"`
updates to that subscriber device as text becomes available, or `op: "replace"` updates when the
transient `body` needs to be replaced.

For each subscriber device, the publisher device should avoid sending another `m.stream.update` while the
previous update for that subscriber device is still being sent to the publisher's homeserver. While a send
is in progress, the publisher device should accumulate newly generated text and send it as a single later
`op: "append"` update. This attempts to preserve in-order delivery for each subscriber device. Publisher
devices should include updates for multiple subscriber devices in the same `/sendToDevice`request when
possible, using different per-device content as needed, to reduce HTTP traffic to the publisher's
homeserver.

<details>
<summary>Examples</summary>

An `op: "replace"` `m.stream.update` content object is:

```json
{
  "room_id": "!room:example.org",
  "event_id": "$event:example.org",
  "seq": 1,
  "op": "replace",
  "content": {
    "body": "The answer is still being generated."
  }
}
```

An `op: "append"` `m.stream.update` content object is:

```json
{
  "room_id": "!room:example.org",
  "event_id": "$event:example.org",
  "seq": 2,
  "op": "append",
  "content": {
    "body": " Still working."
  }
}
```

After a `resync: true` subscription, or when the publisher cannot express the pending transient content
as an append to the descriptor event's `body`, the publisher sends an `op: "replace"` update containing
the generated `body` so far:

```json
{
  "room_id": "!room:example.org",
  "event_id": "$event:example.org",
  "seq": 8,
  "op": "replace",
  "content": {
    "body": "The answer is still being generated. Still working."
  }
}
```

Append updates to that subscriber contain only text not already available to that subscriber from the
descriptor event or earlier stream updates:

```json
{
  "room_id": "!room:example.org",
  "event_id": "$event:example.org",
  "seq": 9,
  "op": "append",
  "content": {
    "body": " Almost done."
  }
}
```

</details>


### Completing message streams

When generation completes and the answer has stabilized, the sender should edit the room event which
contains the `m.stream` descriptor. The edit should replace the descriptor event's visible content with
the final message content and should omit `m.stream` from `m.new_content`, because the ephemeral stream is
no longer necessary for future users.

For example, if the stream descriptor was attached to `$event:example.org`, the final edit could be:

```json
{
  "msgtype": "m.text",
  "body": "The answer is now complete.",
  "m.relates_to": {
    "rel_type": "m.replace",
    "event_id": "$event:example.org"
  },
  "m.new_content": {
    "msgtype": "m.text",
    "body": "The answer is now complete."
  }
}
```

Clients which understand Matrix event replacement should render the final edited content as the durable
result. Clients which understand this MSC should also treat an edit of the descriptor event whose
`m.new_content` omits `m.stream` as a signal that the stream has finished and clean up any subscription
state.

### Stream encryption

If the room event containing the stream descriptor is encrypted, the descriptor is already visible only
to clients which can decrypt that room event. Stream to-device messages should also be encrypted.

Existing Matrix room encryption schemes such as Megolm are designed for durable room events and session
history, and are not a good fit for high-frequency, best-effort, per-device transient updates. This MSC
instead models stream encryption more like encrypted media: the descriptor carries key material visible
to devices which can decrypt the room event, and each transient payload is encrypted independently using
that key.

This MSC defines a to-device encryption algorithm for streams:

```
m.stream.v1.aes-gcm
```

When encryption is used, the descriptor's `encryption` object has the following fields:

```json
{
  "algorithm": "m.stream.v1.aes-gcm",
  "key": "base64url_unpadded_32_byte_key"
}
```

The `key` is 32 bytes encoded as unpadded URL-safe base64. The publisher device generates it when
creating the descriptor.

Encrypted stream subscribe, cancel, and update payloads are sent as to-device `m.room.encrypted` events.
Their content has the following fields:

```json
{
  "algorithm": "m.stream.v1.aes-gcm",
  "stream_id": "base64url_unpadded_hmac",
  "iv": "base64url_unpadded_iv",
  "ciphertext": "base64url_unpadded_ciphertext"
}
```

The `stream_id` is:

```
base64url_unpadded(HMAC-SHA-256(key, room_id || event_id))
```

where `room_id` and `event_id` are UTF-8 strings concatenated in that order. The `iv` is a fresh
random AES-GCM nonce for each encrypted payload.

After decryption, clients must verify that the plaintext `room_id` and `event_id` match the descriptor
identified by the `stream_id`. Clients must ignore encrypted stream events with an unknown `stream_id`,
unknown inner type, invalid authentication tag, or mismatched routing fields.


### Future stream uses

Future MSCs may reuse the descriptor, subscription, update, and optional encryption mechanisms here for
additional room event types. For example, this can be used as an implementation pattern for live location
sharing proposals such as
[MSC3489: Sharing streams of location data with history](https://github.com/matrix-org/matrix-spec-proposals/pull/3489):
an event stream can carry the live tail of a location share without storing every position update in room
history, while use cases that need history can still periodically emit durable beacon events or waypoints.


## Potential issues

Large rooms can still be expensive if many devices subscribe. The proposal mitigates this by requiring
bounded subscriber sets, bounded per-subscriber state, rate limiting, and room-size limits in
implementations.


## Alternatives

Use room-scoped ephemeral events, like typing notifications. This is conceptually neat, but requires
homeserver implementation work: a new send endpoint, federation handling, sync wakeups, and either a new
sync token field or reuse of an existing ephemeral stream. The earlier prototype of this idea was
replaced by the event stream design.

Use [MSC4357: Live Messages via Event Replacement](https://github.com/matrix-org/matrix-spec-proposals/pull/4357).
That approach models live updates as room events using event replacement. This keeps the updates in the
room event system and reuses existing room-event authorization and sync behavior, but it also means
intermediate updates interact with the room DAG, federation, storage, event replacement, search, and
client timeline handling. This MSC chooses an event stream instead because the motivating updates are
transient and best-effort.

Under the MSC4357 approach, AI-style responses and live telemetry may emit many updates per message or
session. Even if each update replaces an earlier one, the server still has to accept, authorize, persist,
order, federate, and later account for those events according to the normal room-event model. That bloats
the persistent event graph with intermediate states whose value is mostly limited to the few seconds
while the user is watching the stream. It can also increase work for moderation, retention, backfill,
search, and clients which need to reason about replacement chains.

Use
[MSC3489: Sharing streams of location data with history](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)
for live location sharing. MSC3489 is the better fit when a room should retain a history of location
points. This MSC is a better fit when the live location is transient and storing a route history in the
room is unnecessary or undesirable.


## Prior art

Telegram's Bot API has a `sendMessageDraft` method for streaming partial bot messages while they are
being generated:
https://core.telegram.org/bots/api#sendmessagedraft.


## Unstable prefix

While this proposal is not considered stable, implementations should use the following unstable
identifiers:

The unstable message content field is:

```
org.matrix.msc4471.stream
```

The unstable to-device event types are:

```
org.matrix.msc4471.stream.subscribe
org.matrix.msc4471.stream.cancel
org.matrix.msc4471.stream.update
```

The unstable stream encryption algorithm is:

```
org.matrix.msc4471.stream.v1.aes-gcm
```
