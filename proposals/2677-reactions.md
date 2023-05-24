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

When sending emoji reactions, the `key` property should include the unicode
[emoji presentation
selector](https://www.unicode.org/reports/tr51/#def_emoji_presentation_selector)
(`\uFE0F`) for codepoints which allow it (see the [emoji variation sequences
list](https://www.unicode.org/Public/UCD/latest/ucd/emoji/emoji-variation-sequences.txt)).

Any `type` of event is eligible for an annotation, including state events.

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

Since they contain no `content` other than `m.relates_to`, `m.reaction` events
are normally not encrypted, as there would be no benefit in doing so. (However,
see [Encrypted reactions](#encrypted-reactions) below.)

### Interaction with edited events

It is not considered valid to send an annotation for a [replacement
event](https://spec.matrix.org/v1.6/client-server-api/#event-replacements)
(i.e., a message edit event): any reactions should refer to the original
event. Annotations of replacement events will be ignored according to the rules
for [counting annotations](#counting-annotations).

As an aside, note that it is not possible to edit a reaction, since replacement
events do not change `m.relates_to` (see [Applying
`m.new_content`](https://spec.matrix.org/v1.6/client-server-api/#applying-mnew_content)),
and there is no other meaningful content within `m.reaction`.  If a user wishes
to change their reaction, the original reaction should be redacted and a new
one sent in its place.

### Counting annotations

The intention of annotations is that they are counted up, rather than being displayed individually.

Clients must keep count of the number of annotations with a given event `type`
and annotation `key` they observe for each event; these counts are typically
presented alongside the event in the timeline.

When performing this count:

 * Each event `type` and annotation `key` should normally be counted separately,
   though whether to actually do so is an implementation decision.

 * Annotation events sent by [ignored users](https://spec.matrix.org/v1.6/client-server-api/#ignoring-users)
   should be excluded from the count.

 * Multiple identical annotations (i.e., with the same event `type` and
   annotation `key`) from the same user (i.e., events with the same `sender`) should
   be treated as a single annotation.

 * It is not considered valid to annotate an event which itself has an
   `m.relates_to` with `rel_type: m.annotation` or `rel_type:
   m.replace`. Implementations should ignore any such annotation events.

 * When an annotation is redacted, it is removed from the count.

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

#### Avoiding duplicate annotations

Homeservers should prevent users from sending a second annotation for a given
event with identical event `type` and annotation `key` (unless the first event
has been redacted).

Attempts to send such an annotation should be rejected with a 400 error and an
error code of `M_DUPLICATE_ANNOTATION`.

Note that this does not guarantee that duplicate annotations will not arrive
over federation. Clients and servers are responsible for deduplicating received
annotations when [counting annotations](#counting-annotations).

#### Server-side aggregation of `m.annotation` relationships

`m.annotation` relationships are *not* [aggregated](https://spec.matrix.org/v1.6/client-server-api/#aggregations)
by the server. In other words, `m.annotation` is not included in the `m.relations` property.

## Alternatives

### Encrypted reactions

[matrix-spec#660](https://github.com/matrix-org/matrix-spec/issues/660)
discusses the possibility of encrypting message relationships in general.

Given that reactions do not rely on server-side aggregation support, an easier
solution to encrypting reactions might be not to use the relationships
framework at all and instead just use a keys within `m.reaction` events, which
could then be encrypted. For example, a reaction could instead be formatted as:

```json5
{
    "type": "m.reaction",
    "content": {
       "event_id": "$some_event_id",
       "key": "👍"
    }
}
```

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
  * We would end up including old annotations that had been superseded, should
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
