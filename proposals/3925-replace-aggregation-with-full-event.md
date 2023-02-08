# MSC3925: m.replace aggregation with full event

As [currently specified](https://spec.matrix.org/v1.4/client-server-api/#server-side-replacement-of-content),
servers should replace the content of events that have been replaced via an `m.replace`
relation.

There are some issues with this requirement:

* Changing the fundamental concept of mostly immutable events is confusing. The server
  can respond with different event contents for the same `event_id`.
* If an event with `m.replace` relation is redacted, clients need to
  detect if the original content was replaced, and possibly need to fetch the
  original content.
* Servers cannot replace the original event content for encrypted events (because the
  replacement content is inside the encrypted body).
  See [matrix-spec#1299](https://github.com/matrix-org/matrix-spec/issues/1299).
* Replacing the content can lead to inconsistent behavior on clients which don't
  support replacing events.
  Assume that we have this timeline on the server:
    - `{"event_id": "E1", "content": {"body": "1"}}`
    - `{"event_id": "E2", "content": {"body": "* 2", "m.new_content": {"body": "2"}}` // replaces `E1`

  A `/sync` is done after `E2`. We will have this timeline on a client:
    - `{"event_id": "E1", "content": {"body": "2"}}`
    - `{"event_id": "E2", "content": {"body": "* 2"}`

  Although `2` is a replaced body it does not have a `*`. This looks to the
  user as if it is the original content of the event.


## Proposal

The following two changes are proposed:
1. The [server-side aggregation of `m.replace` relationships](https://spec.matrix.org/v1.4/client-server-api/#server-side-aggregation-of-mreplace-relationships)
   is extended to be the entire content of the most recent replacement event, formatted
   as described in [Room Event Format](https://spec.matrix.org/v1.4/client-server-api/#room-event-format).
   This ensures that the client will always have the most recent edit without having to
   fetch it from the server.
2. Servers should no longer replace the original content of an event as described 
   at https://spec.matrix.org/v1.4/client-server-api/#server-side-replacement-of-content.

For an original event:

```json5
{
  "event_id": "$original_event",
  "type": "m.room.message",
  "content": {
    "body": "I really like cake",
    "msgtype": "m.text",
    "formatted_body": "I really like cake"
  }
  // irrelevant fields not shown
}

```

With a replacing event:

```json5
{
  "event_id": "$edit_event",
  "type": "m.room.message",
  "content": {
    "body": "* I really like *chocolate* cake",
    "msgtype": "m.text",
    "m.new_content": {
      "body": "I really like *chocolate* cake",
      "msgtype": "m.text"
    },
    "m.relates_to": {
      "rel_type": "m.replace",
      "event_id": "$original_event_id"
    }
  }
  // irrelevant fields not shown
}

```

This is how the original event would look like after the replacement:

```json5
{
  "event_id": "$original_event",
  "type": "m.room.message",
  "content": {
    "body": "I really like cake",
    "msgtype": "m.text",
    "formatted_body": "I really like cake"
  },
  "unsigned": {
    "m.relations": {
      "m.replace": {
        "event_id": "$edit_event",
        "type": "m.room.message",
        "content": {
          "body": "* I really like *chocolate* cake",
          "msgtype": "m.text",
          "m.new_content": {
            "body": "I really like *chocolate* cake",
            "msgtype": "m.text"
          },
          "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$original_event_id"
          }
        }
        // irrelevant fields not shown
      }
    }
  }
  // irrelevant fields not shown
}

```

## Potential issues

* There could be clients which rely on the current behavior:
  * element-web relied on it until [matrix-org/matrix-js-sdk#3045](https://github.com/matrix-org/matrix-js-sdk/pull/3045)
  * The failure mode is: suppose we have an event E, which was subsequently replaced by an event E'. Now, if jumped back to a bit of timeline that contains E but not E', then clients unaware of this change will show the original event E rather than the edited content E'. But: That is an edge-case and it already happens for events other than `m.room.message` (including encrypted events) due to [matrix-org/synapse#12503](https://github.com/matrix-org/synapse/issues/12503).
* It will be harder for clients which do not support replacing events to get
  the current content of an event: currently they can just look at `content.body`.
  However, there is an inconsistent behavior for clients that do not support 
  replacing events (see above).

## Alternatives

One [suggestion](https://github.com/matrix-org/matrix-spec/issues/1299#issuecomment-1290332433) is
to have the server return the complete replacement event instead of the original event. However, that would
break compatibility with existing clients and is a more invasive change.

## Security considerations

None currently foreseen.

## Unstable prefix

No unstable prefix is currently proposed.
