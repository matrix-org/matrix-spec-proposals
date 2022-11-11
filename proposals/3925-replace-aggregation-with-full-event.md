# MSC3925: m.replace aggregation with full event

When a client sends a `m.replace`
relation, [the server should replace the content of the original event](https://spec.matrix.org/v1.4/client-server-api/#server-side-replacement-of-content).

There are some issues with this requirement:

* Changing the fundamental concept of mostly immutable events is confusing. The server
  can respond with different event contents for the same `event_id`.
* If an event with `m.replace` relation is redacted, the client would need to
  detect, if the original content was replaced and possibly needs to fetch the
  original content.
* Servers cannot replace the original event content for encrypted events (because the
  replacement content is inside the encrypted body).
  See [matrix-spec#1299](https://github.com/matrix-org/matrix-spec/issues/1299).


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

```json
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

```json
{
  "event_id": "$edit_event",
  "type": "m.room.message",
  "content": {
    "body": "* I really like *chocolate* cake",
    "msgtype": "m.text",
    "m.new_content": {
      "body": "I really like *chocolate* cake",
      "msgtype": "m.text",
      "com.example.extension_property": "chocolate"
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

```json
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
            "msgtype": "m.text",
            "com.example.extension_property": "chocolate"
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

* There could be clients which rely on the current behavior.
* It will be harder for clients to get the current content of an event: currently
  they can just looking at `content.body`. While this is true, it
  is also a relatively inconsistent behavior. Future replacements of the event
  would be rendered as "* new content". So the event with the replaced event
  does look different (without "*") despite the fact, that it is also replaced.

## Alternatives

We could flip the event stack on it's head and have the outer event
be the edit and then in unsigned have the base event being edited. Currently, it
is the inverse where we have the original event and then in unsigned the newer
event sits. That way, if someone doesn't care about edits (because not
implemented) then they see the right thing, and when someone does care about
them, they
can just inspect unsigned to present the "edits" dialog.

## Security considerations

None currently foreseen.

## Unstable prefix

No unstable prefix is currently proposed.
