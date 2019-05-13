# Proposal for aggregations via m.relates_to

  - [Overview](#overview)
  - [Context](#context)
  - [Types of relations](#types-of-relations)
  - [Aggregating and paginating relations](#aggregating-and-paginating-relations)
  - [Event format](#event-format)
  - [End to end encryption](#end-to-end-encryption)
  - [CS API](#cs-api)
  - [Pagination](#pagination)
    - [API](#api)
  - [Edge cases](#edge-cases)
  - [Federation considerations](#federation-considerations)
  - [Extended annotation use case](#extended-annotation-use-case)
  - [Tradeoffs](#tradeoffs)
    - [Event shape](#event-shape)
  - [Historical context](#historical-context)

## Overview

This proposal introduces the concept of relations, which can be used to associate
new information with an existing event.  Relations are events which have an `m.relates_to`
mixin in their contents, and the new information they convey is expressed in their
usual event `type` and `contents`.

Clients send relations using the new `/send_relation` API.

Clients receive relations as normal events in /sync (aka 'unbundled relations'),
or may also be aggregated together by the server, and presented as
a 'bundle' attached to the original event.

Bundles of relations for a given event are
paginated to prevent overloading the client with relations, and may be traversed by
via the new `/relations` API (which iterates over all relations for an event) or the
new `/aggregations` API (which iterates over the groups of relations, or the relations
within a group).

Three types of relations are defined, each defining different behaviour when aggregated:

 * `m.annotation` - lets you define an event which annotates an existing event.
   When aggregated, groups events together based on `key` and returns a `count`.  (aka SQL's COUNT)
   These are primarily intended for handling reactions.

 * `m.replace` - lets you define an event which replaces an existing event.
   When aggregated, returns the most recent replacement event. (aka SQL's MAX)
   These are primarily intended for handling edits.

 * `m.reference` - lets you define an event which references an existing event.
   When aggregated, currently doesn't do anything special, but in future could bundle
   chains of references (i.e. threads).
   These are primarily intended for handling replies (and in future threads).

This model has been designed for scenarios where the relationship is known between
two events at the point that the 2nd event is sent.  Therefore, extensible info about
the relationship is intended to be stored in the 2nd event, rather than the relation
itself.  For instance, to distinguish different types of references (in_reply_to v. refers
v. cites v. quotes) you would look at the fields of the 2nd event.  Alternatively, one
could add fields to the `m.relates_to` object.

    XXX: do we want to support multiple parents for a m.reference event, if a given event
    references differernt parents in differernt ways?

In future, it may be desirable to send relationship events which link together two
events retrospectively - e.g. an `m.duplicate` event with an `m.link` relation type
might be a way to flag that existing 2 events are somehow duplicates of each other.
However, this would be defined as an entirely different relation type of `m.link`,
which might bundle together both referenced events when aggregated.

## Context

Today, replies looks like:

```json
"type": "m.room.message",
"contents": {
    "m.relates_to": {
        "m.in_reply_to": {
            "event_id": "$another:event.com"
        }
    }
}
```

`m.relates_to` is the signal to the server that the fields within describe
an aggregation operation.

We would like to add support for other types of relations, including message
editing and reactions.

We take the opportunity to simplify m.relates_to to avoid giving the impression
that relation types are mixins and that you can send multiple different type of
relations for a given event, and we define new relation types to describe the
different classes of aggregations.

```json
"type": "m.room.message",
"contents": {
    "m.relates_to": {
        "rel_type": "m.reference",
        "event_id": "$another:event.com"
    }
}
```

    TODO: given we're changing the shape, should we rename the new type as
    `m.relation` or something, to distinguish from the old `m.relates_to`
    type?

    FIXME: Or should we jump straight to m.reference, m.annotation, m.replace
    as top level mixin types?  Erik would prefer not to, as grouping them all
    under `m.relates_to` makes it very clear that they should not be E2E encrypted
    etc.  In fact, we could even move this outside of `contents`?

Relation events are then aggregated together based on the behaviour implied by
their `rel_type`, and bundled appropriately their target event when you /sync.
Additional APIs are available to send relations and paginate them.

## Types of relations

This proposal defines three types of relations: annotations, replacements and
references.

 * Annotations are things like reactions, which should be displayed alongside the
original event. These should support aggregations so that e.g. if twenty people
"like" an event we can bundle the twenty events together when sending the
original event to clients. Another usage of an annotation is e.g. for bots, who
could use annotations to report the success/failure or progress of a command.

 * Replacements are essentially edits, and indicate that instead of giving clients
the original event they should be handed the replacement event instead. Clients
should be able to request all replacements of an event, i.e. the "edit history".

 * References are things like replies, where a later event refers to an earlier event
in some way. The server should include references when sending an event to the
client so they can display the number of replies, and navigate easily to them.

These types effect how the server bundles the related events with the original,
and so the type must be known to servers when handling relations. However, the
exact semantics of a particular relation only needs to be known by clients. This
means that if we include the relation type in the related event we can use the
event type to easily add new types of e.g annotations without requiring server
side support.

## Aggregating and paginating relations

In large rooms an event may end up having a large number of related events, and
so we do not want to have to include all relations when sending the event to the
client. How we limit depends on the relation type.

Annotations are grouped by their event type and an "aggregation key", and the
top N groups with the highest number is included in the event. For example,
reactions would be implemented as a `m.reaction` with aggregation key of e.g.
`👍`.

    TODO: Should we include anything other than event type, aggregation key and
    count?

Replacements replace the original event, and so no aggregation is required.
Care must be taken by the server to ensure that if there are multiple
replacement events, the server must consistently choose the same one as all other servers.
The replacement event should also include a reference to the original event ID
so that clients can tell that the message has been edited.

Permalinks to edited events should capture the event ID that the sender is viewing
at that point (which might be an edit ID).  The client viewing the permalink
should resolve this ID to the source event ID, and then display the most recent
version of that event.

For references, the original event should include the list of `type` and
`event_id` of the earliest N references.

    TODO: Do we need the type? Do we want to differentiate between replies and
    other types of references? This assumes the type of the related event gives
    some hint to clients.

In each case where we limit what is included there should be a corresponding API
to paginate the full sets of events. Annotations would need APIs for both
fetching more groups and fetching events in a group.

## Event format

All the information about the relation is put under `m.relates_to` key.

A reply would look something like:

```json
{
    "type": "m.room.message",
    "contents": {
        "body": "i <3 shelties",
        "m.relates_to": {
            "rel_type": "m.reference",
            "event_id": "$some_event_id"
        }
    }
}
```

And a reaction might look like the following, where we define for `m.reaction`
that the aggregation `key` is the unicode reaction itself.

```json
{
    "type": "m.reaction",
    "contents": {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    }
}
```

    TODO: This limits an event to only having one relation, on the assumption
    that there are no use cases and that it will make life simpler.

An edit would be:

```json
{
    "type": "m.room.message",
    "contents": {
        "body": "Hello! I'm an edit",
        "msgtype": "m.text",
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id",
        }
    }
}
```

An event that has relations bundled alongside it then looks like:

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.annotation": {
                "chunk": [
                  {
                      "type": "m.reaction",
                      "key": "👍",
                      "count": 3
                  }
                ],
                "limited": false,
                "count": 1
            },
            "m.reference": {
                "chunk": [
                    {
                        "type": "m.room.message",
                        "event_id": "$some_event_id"
                    }
                ],
                "limited": false,
                "count": 1
            }
        }
    }
}
```

## End to end encryption

Since the server bundles related events, the relation information must not be
encrypted end-to-end.

For aggregations of annotations there are two options:

1. Don't group together annotations, and have the aggregation `key` encrypted, so
   as to not leak how someone reacted (though server would still see that they
   did).
2. In some way encrypt the aggregation `key`, with the properties that different
   users and clients reacting in the same way to the same event produce the same
   `key`, but isn't something the server can calculate and is
   different between different events (to stop statistical analysis). Clients
   also need to be able to go from encrypted `key` to the actual
   reaction.

   One suggestion here is to use the message key of the parent event to encrypt the
   aggregation `key`.


## CS API

Sending a related event uses an equivalent of the normal send API (with an
equivalent `PUT` API):

```
POST /_matrix/client/r0/rooms/{roomId}/send_relation/{parent_id}/{relation_type}/{event_type}
{
    // event contents
}
```

Whenever an event that has relations is sent to the client, e.g. sync, pagination,
event search etc, the server bundles the relations into the event as per above.

The `parent_id` is:

  * For annotations the event being displayed (which may be an edit)
  * For replaces/edits the original event (not previous edits)
  * For references should be the event being referenced

For the sync API, clients need to be aware of both bundled relations as well as
incremental standalone relation events in the sync response.

## Pagination

Our requirements that we need to paginate over:
 * The relations of a given event, via a new `/relations` API.
  * For replacements (i.e. edits) we get a paginated list of all edits on the source event.
  * For annotations (i.e. reactions) we get the full list of reactions for the source event.
 * Groups of annotations, via a new `/aggregations` API.
  * Need to paginate across the different groups (i.e. how many different
    reactions of different types did it get?)
  * List all the reactions individually per group for this message
 * References (i.e. threads of replies)
  * We don't bundle contents in the references (at least for now); instead we
    just follow the event IDs to stitch the right events back together.
  * We could include a count of the number of references to a given event.
  * We just provide the event IDs (to keep it nice and normalised) in a dict; we
    can denormalise it later for performance if needed by including the event
    type or whatever.  We could include event_type if it was useful to say "5
    replies to this message", except given event types are not just
    m.room.message (in future), it wouldn't be very useful to say "3 image
    replies and 2 msg replies".

### API

We provide two API endpoints, one to paginate relations based in normal
topological order, the second to paginate aggregated annotations.

Both APIs behave in a similar way to `/messages`, except using `next_batch` and
`prev_batch` names (in line with `/sync` API). Clients can start paginating
either from the earliest or latest events using the `dir` param.

Standard pagination API looks like the following, where you can optionally
specify relation and event type to filter by.  It lists all the relations
in topological order.

```
GET /_matrix/client/r0/rooms/{roomID}/relations/{eventID}[/{relationType}[/{eventType}]]
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

The aggregated pagination API operates in two modes, the first is to paginate
the groups themselves, returning aggregated results:

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}[/{relationType}][/{eventType}][?filter=id]
```

By default, the aggregation behaviour is defined by the relation type:
 * rel_type of `m.annotation` == group by count, and order by count desc
 * rel_type of `m.replace` == we just get the most recent message, no bundles.
 * rel_type of `m.reference` == we get the IDs of the events replying to us, and
   the total count of replies to this msg

In future, we could use a filter to specify/override how to aggregate the relations,
which would then also be used to inform /sync how we want to receive our bundled
relations.  (However, we really need to be better understand how to do custom
relation types first...)

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "key": "👍",
      "count": 5,
    }
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

The second mode of operation is to paginate within a group, in normal topological order:

```
GET /_matrix/client/r0/rooms/{roomID}/aggregations/{eventID}/${relationType}/{eventType}/{key}
```

e.g.

```
GET /_matrix/client/r0/rooms/!asd:matrix.org/aggregations/$1cd23476/m.annotation/m.reaction/👍
```

```json
{
  "chunk": [
    {
      "type": "m.reaction",
      "sender": "...",
      "content": { }
    },
  ],
  "next_batch": "some_token",
  "prev_batch": "some_token"
}
```

## Edge cases

What happens when you react to an edit?
 * You should be able to, but the reaction should be attributed to the edit (or
   its contents) rather than the message as a whole.
 * So how do you aggregate?
 * Suggestion: edits gather their own reactions, and the clients should display
   the reactions on the most recent edit.
   * This provides a social pressure to get your edits in quickly before there
     are many reactions, otherwise the reactions will get lost.
   * And it avoids us randomly aggregating reactions to potentially very
     different contents of messages.

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

How do you remove a reaction?
 * You redact it.

Redactions
 * Redacting an edited event in the UI should redact the original; the client
   will need to redact the original event to make this happen.
   * Is this not problematic when trying to remove illegal content from servers?
 * Clients could also try to expand the relations and redact those too if they
   wanted to, but in practice the server shouldn't send down relations to
   redacted messages, so it's overkill.
 * You can also redact specific relations if needed (e.g. to remove a reaction
   from ever happening)
 * If you redact an relation, we keep the relation DAG (and solve that metadata
   leak alongside our others)

What does it mean to call /context on a relation?
 * We should probably just return the root event for now, and then refine it in
   future for threading?

Should we enforce that each user can only send one type of reaction to a msg?
 * Yes. We can do that when sending at CS API as the first cut
  * But what do we use as a response?  We can do a 400 with an error code that tells us
    why - i.e. that it's because you can't react multiple times.
  * We mandate txn IDs to provide idempotency.
  * (Or can we rely on including our own reactions in bundles to tell whether
    are doublecounting our own reactions or not?)
 * However, we need to be able to handle bad servers who send duplicate events anyway.
   * The only way to do this will be at SS API, and refuse to accept duplicatee
     events.

Should we always include our own reactions in a bundle, to make it easier to redact them,
or to show the UI in the right state?
 * Probably, but this can be a future refinement.
 * ...but might be needed for imposing one type of reaction per msg.

Should we stop reactions being sent by the normal /send API?

What can we edit?
 * Only non-state events for now.
 * We can't change event types, or anything else which is in an E2E payload

How do diffs work on edits if you are missing intermediary edits?
 * We just have to ensure that the UI for visualising diffs makes it clear
   that diffs could span multiple edits rather than strictly be per-edit-event.

What happens when we edit a reply?
 * We just send an m.replace which refers to the m.reference target; nothing
   special is needed.  i.e. you cannot change who the event is replying to.

Do we need to support retrospective references?
 * For something like "m.duplicate" to retrospectively declare that one event
   dupes another, we might need to bundle two-levels deep (subject+ref and then
   ref+target).  We can cross this bridge when we get there though, as a 4th
   aggregation type

## Federation considerations

In general, no special considerations are needed for federation; relational
events are just sent as needed over federation same as any other event type -
aggregated onto the original event if needed.

We have a problem with resynchronising relations after a gap in federation:
We have no way of knowing that an edit happened in the gap to one of the events
we already have.  So, we'll show inconsistent data until we backfill the gap.
 * We could write this off as a limitation.
 * Or we could make *ALL* relations a DAG, so we can spot holes at the next
   relation, and go walk the DAG to pull in the missing relations?  Then, the
   next relation for an event could pull in any of the missing relations.
   Socially this probably doesn't work as reactions will likely drop off over
   time, so by the time your server comes back there won't be any more reactions
   pulling the missing ones in.
 * Could we also ask the server, after a gap, to provide all the relations which
   happened during the gap to events whose root preceeded the gap.
   * "Give me all relations which happened between this set of
     forward-extremities when I lost sync, and the point i've rejoined the DAG,
     for events which preceeded the gap"?
   * Would be hard to auth all the relations which this api coughed up.
     * We could auth them based only the auth events of the relation, except we
       lose the context of the nearby DAG which we'd have if it was a normal
       backfilled event.
     * As a result it would be easier for a server to retrospectively lie about
       events on behalf of its users.
     * This probably isn't the end of the world, plus it's more likely to be
       consistent than if we leave a gap.
       * i.e. it's better to consistent with a small chance of being maliciously
         wrong, than inconsistent with a guaranteed chance of being innocently
         wrong.
   * We'd need to worry about pagination.
   * This is probably the best solution, but can also be added as a v2.

## Security considerations

When using reactions for voting purposes we might well want to anonymise the
reactor, at least from other users if not server admins, to avoid retribution problems.
This gives an unfair advantage to people who run their own servers however and
can cheat and deanonymise (and publish) reactor details.

Or in a MSC1228 world... we could let users join the room under an anonymous
persona from a big public server in order to vote?  However, such anonymous personae
would lack any reputation data.

## Extended annotation use case

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
overhead the annotation event could include a `m.summary` field which gets
included.

This would look something like the following, where the annotation is:

```json
{
  "type": "m.bot_command_response",
  "content": {
    "m.summary": {
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
              "m.summary": {
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

  * How does this work with E2EE? How do we encrypt the `m.summary`?
  * We would end up including old annotations that had been superceded, should
    these be done via edits instead?

## Tradeoffs

### Event shape

Shape of

```json
"contents": {
    "m.relates_to": {
        "m.reference": {
            "event_id": "$another:event.com"
        }
    }
}
```
versus

```json
"contents": {
    "m.relates_to": {
        "rel_type": "m.reference",
        "event_id": "$another:event.com"
    }
}
```

The reasons to go with `rel_type` is:
 * we don't need the extra indirection to let multiple relations apply to a given pair of
   events, as that should be expressed as separate relation events.
 * if we want 'adverbs' to apply to 'verbs' in the subject-verb-object triples which
   relations form, then we apply it as mixins to the relation data itself rather than trying
   to construct subject-verb-verb-object sentences.
 * so, we should pick a simpler shape rather than inheriting the mistakes of m.in_reply_to
   and we have to keep ugly backwards compatibility around for m.in_reply_to
   but we can entirely separately worry about migrating replies to new-style-aggregations in future
   perhaps at the same time as doing threads.

## Historical context

pik's MSC441 has:

Define the JSON schema for the aggregation event, so the server can work out
which fields should be aggregated.

```json
"type": "m.room._aggregation.emoticon",
"contents": {
    "emoticon": "::smile::",
    "msgtype": "?",
    "target_id": "$another:event.com"
}
```

These would then aggregated, based on target_id, and returned as annotations on
the source event in an `aggregation_data` field:

```json
"contents": {
    ...
    "aggregation_data": {
        "m.room._aggregation.emoticon": {
            "aggregation_data": [
                {
                    "emoticon": "::smile::",
                    "event_id": "$14796538949JTYis:pik-test",
                    "sender": "@pik:pik-test"
                }
            ],
            "latest_event_id": "$14796538949JTYis:pik-test"
        }
    }
}
```
