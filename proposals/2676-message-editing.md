# MSC2676: Message editing

Users may wish to edit previously sent messages, for example to correct typos.
This can be done by sending a new message with an indication that it replaces
the previously sent message.

This proposal is one in a series of proposals that defines a mechanism for
events to relate to each other.  Together, these proposals replace
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

* [MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) defines a
  standard shape for indicating events which relate to other events.
* [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines APIs to
  let the server calculate the aggregations on behalf of the client, and so
  bundle the related events with the original event where appropriate.
* This proposal defines how users can edit messages using this mechanism.
* [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) defines how
  users can annotate events, such as reacting to events with emoji, using this
  mechanism.

## Background

Element-Web (then Riot-Web) and Synapse both implemented initial support for
message editing, following the proposals of MSC1849, in May 2019
([matrix-react-sdk](https://github.com/matrix-org/matrix-react-sdk/pull/2952),
[synapse](https://github.com/matrix-org/synapse/pull/5209)). Element-Android
and Element-iOS also added implementations around that time. Unfortunately,
those implementations presented the feature as "production-ready", despite it
not yet having been adopted into the Matrix specification.

The current situation is therefore that client or server implementations hoping
to interact with Element users must simply follow the examples of that
implementation. In other words, message edits form part of the *de-facto* spec
despite not being formalised in the written spec. This is clearly a regrettable
situation. Hopefully, processes have improved over the last three years so that
this situation will not arise again.  Nevertheless there is little we can do
now other than formalise the status quo.

This MSC, along with the others mentioned above, therefore seeks primarily to
do that. Although there is plenty of scope for improvement, we consider that
better done in *future* MSCs, based on a shared understanding of the *current*
implementation.

In short, this MSC prefers fidelity to the current implementations over
elegance of design.

## Proposal

### `m.replace` event relationship type

A new `rel_type` of `m.replace` is defined for use with the `m.relates_to`
field as defined in
[MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674). This is
intended primarily for handling edits, and lets you define an event which
replaces an existing event.

Such an event, with `rel_type: m.replace`, is referred to as a "message edit event".

### `m.new_content` property

The `content` of a message edit event must contain a `m.new_content` property
which defines the replacement content. (This allows the normal `body` fields to
be used for a fallback for clients who do not understand replacement events.)

For instance, an `m.room.message` which replaces an existing event might look like:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "* Hello! My name is bar",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text"
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id"
        }
    }
}
```

The `m.new_content` can include any properties that would normally be found in
an event's `content` property, such as `formatted_body`.

#### Encrypted events

If the original event was encrypted, the replacement should be too. In that
case, `m.new_content` is placed in the `content` of the encrypted payload. The
`m.relates_to` property remains unencrypted, as required by the
[relationships](https://spec.matrix.org/v1.3/client-server-api/#forming-relationships-between-events)
section of the Client-Server API specification.

For example, an encrypted replacement event might look like this:

```json
{
    "type": "m.room.encrypted",
    "content": {
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id"
        },
        "algorithm": "m.megolm.v1.aes-sha2",
        "sender_key": "<sender_curve25519_key>",
        "device_id": "<sender_device_id>",
        "session_id": "<outbound_group_session_id>",
        "ciphertext": "<encrypted_payload_base_64>"
    }
}
```

... and, once decrypted, the payload might look like this:


```json
{
    "type": "m.room.<event_type>",
    "room_id": "!some_room_id",
    "content": {
        "body": "* Hello! My name is bar",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text"
        }
    }
}
```

Note that:
 * There is no `m.relates_to` property in the encrypted payload. (Any such
   property would be ignored.)
 * There is no `m.new_content` property in the cleartext `content` of the
   `m.room.encrypted` event. (Again, any such property would be ignored.)

For clarity: the payload must be encrypted as normal, ratcheting the Megolm session
as normal. The original Megolm ratchet entry should **not** be re-used.

#### Applying `m.new_content`

When applying a replacement, the `content` property of the original event is
replaced entirely by the `m.new_content`, with the exception of `m.relates_to`,
which is left *unchanged*. Any `m.relates_to` property within `m.new_content`
is ignored.

For example, given a pair of events:

```json
{
    "event_id": "$original_event",
    "type": "m.room.message",
    "content": {
        "body": "I *really* like cake",
        "msgtype": "m.text",
        "formatted_body": "I <em>really</em> like cake",
    }
}
```

```json
{
    "event_id": "$edit_event",
    "type": "m.room.message",
    "content": {
        "body": "* I *really* like *chocolate* cake",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "I *really* like *chocolate* cake",
            "msgtype": "m.text",
            "com.example.extension_property": "chocolate"
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$original_event_id"
        }
    }
}
```

... then the end result is an event as shown below. Note that `formatted_body`
is now absent, because it was absent in the replacement event, but
`m.relates_to` remains unchanged (ie, absent).

```json
{
    "event_id": "$original_event",
    "type": "m.room.message",
    "content": {
        "body": "I *really* like *chocolate* cake",
        "msgtype": "m.text",
        "com.example.extension_property": "chocolate"
    }
}
```

Note that the `msgtype` property of `m.room.message` events need not be the
same as in the original event. For example, if a user intended to send a
message beginning with "/me", but their client sends an `m.emote` event
instead, they could edit the message to send be an `m.text` event as they had
originally intended.

### Validity of message edit events

Some message edit events are defined to be invalid. To be considered valid, all
of the following criteria must be satisfied:

 * The replacement and original events must have the same `type`.
 * Neither the replacement nor original events can be state events (ie, neither
   may have a `state_key`).
 * The original event must not, itself, have a `rel_type` of `m.replace`.
 * The original event and replacement event must have the same `sender`.
 * The replacement event (once decrypted, if appropriate) must have an
   `m.new_content` property.

The original event and replacement event must also have the same `room_id`, as
required by the
[relationships](https://spec.matrix.org/v1.3/client-server-api/#forming-relationships-between-events)
section of the Client-Server API specification.

If any of these criteria are not satisfied, implementations should ignore the
replacement event (the content of the original should not be replaced, and the
edit should not be included in the server-side aggregation).

### Server behaviour

#### Server-side aggregation of `m.replace` relationships

Note that there can be multiple events with an `m.replace` relationship to a
given event (for example, if an event is edited multiple times). These should
be [aggregated](https://spec.matrix.org/v1.3/client-server-api/#aggregations)
by the homeserver.

The format of the aggregation for `m.replace` simply gives gives the
`event_id`, `origin_server_ts`, and `sender` of the most recent replacement
event (as determined by `origin_server_ts`, falling back to a lexicographic
ordering of `event_id`).

This aggregation is bundled into the `unsigned/m.relations` property of any
event that is the target of an `m.replace` relationship. For example:

```json5

{
  "event_id": "$original_event_id",
  // ...
  "unsigned": {
    "m.relations": {
      "m.replace": {
        "event_id": "$latest_edit_event_id",
        "origin_server_ts": 1649772304313,
        "sender": "@editing_user:localhost"
      }
    }
  }
}
```

If the original event is redacted, any `m.replace` relationship should **not**
be bundled with it (whether or not any subsequent edits are themselves
redacted). Note that this behaviour is specific to the `m.replace`
relationship.

#### Server-side replacement of content

Whenever an `m.replace` is to be bundled with an event as above, the server should
also modify the `content` of the original event according
to the `m.new_content` of the most recent edit (determined as above).

An exception applies to [`GET
/_matrix/client/v3/rooms/{roomId}/event/{eventId}`](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomideventeventid),
which should return the *unmodified* event (though the relationship should
still be bundled, as described above).

The endpoints where this behaviour takes place is the same as those where
aggregations are bundled, with the exception of
`/room/{roomId}/event/{eventId}`. This includes:

  * `GET /rooms/{roomId}/messages`
  * `GET /rooms/{roomId}/context/{eventId}`
  * `GET /rooms/{roomId}/relations/{eventId}`
  * `GET /rooms/{roomId}/relations/{eventId}/{relType}`
  * `GET /rooms/{roomId}/relations/{eventId}/{relType}/{eventType}`
  * `GET /sync` when the relevant section has a `limited` value of `true`
  * `POST /search` for any matching events under `room_events`.

### Client behaviour

Clients can often ignore message edit events, since any events the server
returns via the C-S API will be updated by the server to account for subsequent
edits.

However, clients should apply the replacement themselves when the server is
unable to do so. This happens in the following situations:

1. The client has already received and stored the original event before the message
   edit event arrives.

2. The original event (and hence its replacement) are encrypted.

Client authors are reminded to take note of the requirements for [Validity of
message edit events](#validity-of-message-edit-events), and to ignore any
invalid edit events that may be received.

### Permalinks

Permalinks to edited events should capture the event ID that the creator of the
permalink is viewing at that point (which might be a message edit event).

The client viewing the permalink should resolve this ID to the original event
ID, and then display the most recent version of that event.

### Redactions

When a message using a `rel_type` of `m.replace` is redacted, it removes that
edit revision. This has little effect if there were subsequent edits, however
if it was the most recent edit, the event is in effect reverted to its content
before the redacted edit.

Redacting the original message in effect removes the message, including all
subsequent edits, from the visible timeline. In this situation, homeservers
will return an empty `content` for the original event as with any other
redacted event. It must be noted that, although they are not immediately
visible in Element, subsequent edits remain unredacted and can be seen via API
calls. See [Future considerations](#future-considerations).

### Edits of replies

Some particular constraints apply to events which replace a
[reply](https://spec.matrix.org/v1.3/client-server-api/#rich-replies). In
particular:

 * There should be no `m.in_reply_to` property in the the `m.relates_to`
   object, since it would be redundant (see [Applying
   `m.new_content`](#applying-mnew_content) above, which notes that the original
   event's `m.relates_to` is preserved), as well as being contrary to the
   spirit of
   [MSC2674](https://github.com/matrix-org/matrix-spec-proposals/pull/2674)
   which expects only one relationship per event.

 * `m.new_content` should **not** contain any ["reply
   fallback"](https://spec.matrix.org/v1.3/client-server-api/#fallbacks-for-rich-replies),
   since it is assumed that any client which can handle edits can also
   display replies natively.

An example of an edit to a reply is as follows:

```json
{
  "type": "m.room.message",
  "content": {
    "body": "> <@richvdh:sw1v.org> ab\n\n * ef",
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "formatted_body": "<mx-reply><blockquote><a href=\"https://matrix.to/#/!qOZKfwKPirAoSosXrf:matrix.org/$1652807718765kOVDf:sw1v.org?via=matrix.org&amp;via=sw1v.org\">In reply to</a> <a href=\"https://matrix.to/#/@richvdh:sw1v.org\">@richvdh:sw1v.org</a><br>ab</blockquote></mx-reply> * ef",
    "m.new_content": {
      "body": "ef",
      "msgtype": "m.text",
      "format": "org.matrix.custom.html",
      "formatted_body": "ef"
    },
    "m.relates_to": {
      "rel_type": "m.replace",
      "event_id": "$original_reply_event"
    }
  }
}
```


## Future considerations

### Ordering of edits

In future we may wish to consider ordering replacements (or relations in
general) via a DAG rather than using `origin_server_ts` to determine ordering -
particularly to mitigate potential abuse of edits applied by moderators.
Whatever, care must be taken by the server to ensure that if there are multiple
replacement events, the server must consistently choose the same one as all
other servers.

### Redaction of edits

It is highly unintuitive that redacting the original event leaves subsequent
edits visible to curious eyes even though they are hidden from the
timeline. This is considered a bug which this MSC makes no attempt to
resolve. See also
[element-web#11978](https://github.com/vector-im/element-web/issues/11978) and
[synapse#5594](https://github.com/matrix-org/synapse/issues/5594).

### Edits to state events

There are various issues which would need to be resolved before edits to state
events could be supported. In particular, we would need to consider how the
semantically-meaningful fields of the content of a state event relate to
`m.new_content`. Variation between implementations could easily lead to
security problems (See
[element-web#21851](https://github.com/vector-im/element-web/issues/21851) for
example.)

### Editing other users' events

There is a usecase for users with sufficient power-level to edit other peoples'
events. For now, no attempt is made to support this. If it is supported in the
future, we would need to find a way to make it clear in the timeline.
