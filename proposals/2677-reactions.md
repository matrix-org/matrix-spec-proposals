# MSC2677: Annotations and Reactions

Users sometimes wish to respond to a message using emojis.  When such responses
are grouped visually below the message being reacted to, this provides a
(visually) light-weight way for users to react to messages.

This proposal was originally part of [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

## Background

As with [message
edits](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2676-message-editing.md#background),
support for reactions were landed in the Element clients and Synapse in May
2019, following the proposals of
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849) and then
presented as being "production-ready", despite them not yet having been adopted
into the Matrix specification.

Again as with edits, the current situation is therefore that client or server
implementations hoping to interact with Element users must simply follow the
examples of that implementation.

To rectify the situation, this MSC therefore seeks primarily to formalise the
status quo. Although there is plenty of scope for improvement, we consider
that better done in *future* MSCs, based on a shared understanding of the
*current* implementation.

In short, this MSC prefers fidelity to the current implementations over
elegance of design.

On the positive side: this MSC is the last part of the former MSC1849 to be
formalised, and is by far the most significant feature implemented by the
Element clients which has yet to be specified.

## Proposal

### `m.annotation` event relationship type

A new [event relationship type](https://spec.matrix.org/v1.6/client-server-api/#relationship-types)
with a `rel_type` of `m.annotation`.

This relationship type is intended primarily for handling emoji reactions, allowing clients to
send an event which annotates an existing event.

Another potential usage of annotations is for bots, which could use them to
report the success/failure or progress of a command.

The annotations are typically presented alongside the event in the timeline.

Along with the normal properties `event_id` and `rel_type`, the
[`m.relates_to`](https://spec.matrix.org/v1.6/client-server-api/#definition-mrelates_to)
property should contains a `key` that indicates the annotation being
applied. For example, when reacting with emojis, the `key` contains the emoji
being used.

An event annotating another with the thumbs-up emoji would therefore have the following `m.relates_to` propperty:

```json
"m.relates_to": {
    "rel_type": "m.annotation",
    "event_id": "$some_event_id",
    "key": "👍"
}
```

When sending emoji reactions, the `key` property should include the colourful
variation-16 when applicable.

### `m.reaction` event type

A new message type `m.reaction` is proposed to indicate that a user is reacting
to a message. No `content` properties are defined for this event type: it serves
only to hold a relationship to another event.

For example, an `m.reaction` event which annotates an existing event with a 👍
looks like:

```json
{
    "type": "m.reaction",
    "content": {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    }
}
```

### Push rules

Since reactions are considered "metadata" that annotate an existing event, they
should not by default trigger notifications.  Thus a new [default override
rule](https://spec.matrix.org/v1.6/client-server-api/#default-override-rules)
is to be added that ignores reaction events:

```json
{
    "rule_id": ".m.rule.reaction",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.reaction"
        }
    ],
    "actions": []
}
```

The rule is added between `.m.rule.tombstone` and `.m.rule.room.server_acl`.

(Synapse implementation: [base_rules.rs](https://github.com/matrix-org/synapse/blob/157c571f3e9d3d09cd763405b6a9eb967f2807e7/rust/src/push/base_rules.rs#L216-L229))

### Server support

#### Server-side aggregation of `m.annotation` relationships

Homeservers should
[aggregate](https://spec.matrix.org/v1.6/client-server-api/#aggregations)
events with an `m.annotation` relationship to a given event.

When aggregating `m.annotation` events, homeservers should group events
together based on their event `type` and `key`, and count the number of each
distinct `type`/`key`. An example aggregation is as follows:

```json
{
    "event_id": "$original_event_id",
    // irrelevant fields not shown
    "unsigned": {
        "m.relations": {
            "m.annotation": {
                "chunk": [
                  {
                      "type": "m.reaction",
                      "key": "👍",
                      "count": 3
                  },
                  {
                      "type": "example.com.test",
                      "key": "👍",
                      "count": 1
                  },
                  {
                      "type": "m.reaction",
                      "key": "👎",
                      "count": 2
                  }
                ]
            }
        }
    }
}
```

This event has received three thumbsup reactions, two thumbsdown reactions, and
a thumbsup annotation with an event type of `example.com.test` (which will be
ignored by clients which don't understand the `example.com.test` event type).

As the example shows, the aggregation format has a `chunk` property at the top
level. (This is indended to allow pagination of reactions in a future
extension, though that is not currently specified.) Each entry in the `chunk` is
an object with properties:

 * `type`: the event `type` of the aggregated events.
 * `key`: the `key` from the `m.relates_to` properties of the aggregated events.
 * `count`: the number of unredacted events with this event `type` and annotation `key`.

### Redactions

When a message using a `rel_type` of `m.annotation` is redacted, this removes
the annotation from the message.

## Edge Cases

How do you stop people reacting more than once with the same key?
 1. You error with 400 (M_INVALID_REL_TYPE) if they try to react twice with the same key, locally
 2. You flatten duplicate reactions received over federation from the same user
    when calculating your local aggregations
 3. You don't pass duplicate reactions received over federation to your local user.
 4. XXX: does synapse do 2 & 3 yet?

Can you [edit](https://github.com/matrix-org-matrix-doc/pull/2676) a reaction?
 * It feels reasonable to say "if you want to edit a reaction, redact it and resend".
   `rel_type` is immutable, much like `type`.

Can you react to a reaction?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.

What happens when you react to an edit?
 * You should be able to, but the reaction should be attributed to the edit (or
   its contents) rather than the message as a whole.
 * Edits gather their own reactions, and the clients should display
   the reactions on the most recent edit.
   * This provides a social pressure to get your edits in quickly before there
     are many reactions, otherwise the reactions will get lost.
   * And it avoids us randomly aggregating reactions to potentially very
     different contents of messages.

Which message types are reactable?
 * Any. But perhaps we should provide some UI best practice guidelines:
  * `m.room.message` must be reactable
  * `m.sticker` too
  * ...but anything else may not be rendered.

## Alternatives

### Extended annotation use case

In future it might be useful to be able to annotate events with more
information, some examples include:

  * Annotate commit/PR notification messages with their associated CI state, e.g.
    pending/passed/failed.
  * If a user issues a command to a bot, e.g. `!deploy-site` the bot could
    annotate that event with current state, like "acknowledged",
    "redeploying...", "success", "failed", etc.
  * Other use cases...?

However, this doesn't really work with the proposed grouping, as the aggregation
key wouldn't contain the right information needed to display it (unlike for
reactions).

One way to potentially support this is to include the events (or a subset of the
event) when grouping, so that clients have enough information to render them.
However this dramatically inceases the size of the parent event if we bundle the
full events inside, even if limit the number we bundle in. To reduce the
overhead the annotation event could include a `m.result` field which gets
included.

This would look something like the following, where the annotation is:

```json
{
  "type": "m.bot_command_response",
  "content": {
    "m.result": {
      "state": "success",
    },
    "m.relates_to": {
      "type": "m.annotation",
      "key": ""
    }
  }
}
```

and gets bundled into an event like:

```json
{
  "unsigned": {
    "m.relations": {
      "m.annotation": [
        {
          "type": "m.bot_command_response",
          "key": "",
          "count": 1,
          "chunk": [
            {
              "m.result": {
                "state": "success",
              },
            }
          ],
          "limited": false,
        }
      ]
    }
  }
}
```

This is something that could be added later on. A few issues with this are:

  * How does this work with E2EE? How do we encrypt the `m.result`?
  * We would end up including old annotations that had been superceded, should
    these be done via edits instead?

## Security considerations

Clients should render reactions that have a long `key` field in a sensible
manner. For example, clients can elide overly-long reactions.

If using reactions for upvoting/downvoting purposes we would almost certainly want to anonymise the
reactor, at least from other users if not server admins, to avoid retribution problems.
This gives an unfair advantage to people who run their own servers however and
can cheat and deanonymise (and publish) reactor details.  In practice, reactions may
not be best used for upvote/downvote as at the unbundled level they are intrinsically
private data.

Or in a MSC1228 world... we could let users join the room under an anonymous
persona from a big public server in order to vote?  However, such anonymous personae
would lack any reputation data.
