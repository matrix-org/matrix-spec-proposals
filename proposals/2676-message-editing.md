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
better done in *future* MSCs, based on a shared understaning of the *current*
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

The replacement event must contain a `m.new_content` property which defines the
replacement content. (This allows the normal `body` fields to be used for a
fallback for clients who do not understand replacement events.)

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

Such an event, with `rel_type: m.replace`, is referred to as a "message edit".

The `m.new_content` can include any properties that would normally be found in
an event's `content` property, such as `formatted_body`.

Note that the `msgtype` property of `m.room.message` events need not be the
same as in the original event. For example, if a user intended to send a
message beginning with "/me", but their client sends an `m.emote` event
instead, they could edit the message to send be an `m.text` event as they had
originally intended.

Whenever a homeserver would return an event via the Client-Server API, it
should check for any applicable `m.replace` event, and if one is found, it
should first modify the `content` of the original event according to the
`m.new_content` of the most recent edit (as determined by
`origin_server_ts`). An exception applies to [`GET
/_matrix/client/v3/rooms/{roomId}/event/{eventId}`](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomideventeventid),
which should return the *unmodified* event (though the relationship should still be
"bundled", as described [below](#server-side-aggregation-of-mreplace-relationships).

Clients are generally expected to ignore message edit events, since the server
implementation takes care of updating the content of the original
event. However, if the client has already received the original event, it must
apply the replacement to the original itself (or, alternatively, request an
updated copy of the original via [`GET
/_matrix/client/v3/rooms/{roomId}/context/{eventId}`](https://spec.matrix.org/v1.2/client-server-api/#get_matrixclientv3roomsroomidcontexteventid)
or similar).

#### Applying `m.new_content`

When applying a replacement, the `content` property of the origial event is
replaced entirely by the `m.new_content`, with the exception of `m.relates_to`,
which is left *unchanged*. For example, given a pair of events:

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

### Permalinks

Permalinks to edited events should capture the event ID that the sender is
viewing at that point (which might be an edit ID).  The client viewing the
permalink should resolve this ID to the source event ID, and then display the
most recent version of that event.

### Redactions

When a message using a `rel_type` of `m.replace` is redacted, it removes that
edit revision.

In the UI, the act of redacting an edited message in the timeline should
remove the message entirely from the timeline.  It can do this by redacting the
original msg, while ensuring that clients locally discard any edits to a
redacted message on receiving a redaction.

When a specific revision of an event is redacted, the client should manually
refresh the parent event via `/events` to grab whatever the replacement
revision is.

### Server-side aggregation of `m.replace` relationships

Note that there can be multiple event with an `m.replace` relationship to a
given event (for example, if an event is edited multiple times).  Homeservers
should aggregate `m.replace` relationships as in
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675). The aggregation
gives the `event_id`, `origin_server_ts`, and `sender` of the most recent
replacement event (as determined by `origin_server_ts`).

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
        "sender": "@editing_user:localhost
      }
    }
  }
}
```

## Edge Cases

How do you handle racing edits?
 * The edits could form a DAG of relations for robustness.
    * Tie-break between forward DAG extremities based on origin_ts
    * this should be different from the target event_id in the relations, to
      make it easier to know what is being replaced.
    * hard to see who is responsible for linearising the DAG when receiving.
      Nasty for the client to do it, but the server would have to buffer,
      meaning relations could get stuck if an event in the DAG is unavailable.
 * ...or do we just always order by on origin_ts, and rely on a social problem
   for it not to be abused?
    * problem is that other relation types might well need a more robust way of
      ordering. XXX: can we think of any?
    * could add the DAG in later if it's really needed?
    * the abuse vector is for a malicious moderator to edit a message with origin_ts
      of MAX_INT. the mitigation is to redact such malicious messages, although this
      does mean the original message ends up being vandalised... :/
 * Conclusion: let's do it for origin_ts as a first cut, but use event shapes which
   could be switched to DAG in future is/as needed.  Good news is that it only
   affects the server implementation; the clients can trust the server to linearise
   correctly.

What can we edit?
 * Only non-state events for now.
 * We can't change event types, or anything else which is in an E2E payload
 * We can't change relation types either.

How do diffs work on edits if you are missing intermediary edits?
 * We just have to ensure that the UI for visualising diffs makes it clear
   that diffs could span multiple edits rather than strictly be per-edit-event.

What happens when we edit a reply?
 * We just send an m.replace which refers to the m.reference target; nothing
   special is needed.  i.e. you cannot change who the event is replying to.
 * The edited reply should ditch the fallback representation of the reply itself
   however from `m.new_content` (specifically the `<mx-reply>` tag in the
   HTML, and the chevron prefixed text in the plaintext which we don't know
   whether to parse as we don't know whether this is a reply or not), as we
   can assume that any client which can handle edits can also display replies
   natively.

What power level do you need to be able to edit other people's messages, and how
does it fit in with federation event auth rules?
 * 50, by default?

    XXX: Synapse doesn't impose this currently - it lets anyone send an edit,
    but then filters them out of bundled data.

"Editing other people's messages is evil; we shouldn't allow it"
 * Sorry, we have to bridge with systems which support cross-user edits.
 * When it happens, we should make it super clear in the timeline that a message
   was edited by a specific user.
 * We do not recommend that native Matrix clients expose this as a feature.


what happens if `m.new_content` is absent? or the `type` is different?

## Future considerations

In future we may wish to consider ordering replacements (or relations in
general) via a DAG rather than using `origin_server_ts` to determine ordering -
particularly to mitigate potential abuse of edits applied by moderators.
Whatever, care must be taken by the server to ensure that if there are multiple
replacement events, the server must consistently choose the same one as all
other servers.
