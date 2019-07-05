# Proposal for aggregations via relations

## Problem

It's common to want to send events in Matrix which relate to existing events -
for instance, reactions, edits and even replies/threads.

Clients typically need to track the related events alongside the original
event they relate to, in order to correctly display them.  For instance,
reaction events need to aggregated together by summing and be shown next to
the event they react to; edits need to be aggregated together by replacing the
original event and subsequent edits; replies need to be indented after the
message they respond to, etc.

It is possible to treat relations as normal events and aggregate them
clientside, but to do so comprehensively could be very resource intensive, as
the client would need to spider all possible events in a room to find
relationships and maintain an correct view.

Instead, this proposal seeks to solve this problem by:
 * Defining a standard shape for defining events which relate to other events
 * Defining APIs to let the server calculate the aggregations on behalf of the
   client, and so bundle the related events with the original event where
   appropriate.

## Proposal

This proposal introduces the concept of relations, which can be used to
associate new information with an existing event.

Relations are any event which have an `m.relationship` mixin in their
contents. The `m.relationship` field must include a `rel_type` field that
gives the type of relationship being defined, and the `event_id` field that
gives the event which is the target of the relation.  All the information about
the relationship lives under the `m.relationship` key.

If it helps, you can think of relations as a "subject verb object" triple,
where the subject is the relation event itself; the verb is the `rel_type`
field of the `m.relationship` and the object is the `event_id` field.

We consciously do not support multiple different relations within a single event,
in order to keep the API simple, and in the absence of identifiable use cases.
Instead, one would send multiple events, each with its own `m.relationship`
defined.

### Relation types

This proposal defines three `rel_type`s, each which provide different behaviour
when aggregated:

 * `m.annotation` - Intended primarily for handling emoji reactions, these let
   you define an event which annotates an existing event. The annotations are
   typically presented alongside the event in the timeline. When aggregated,
   it groups events together based on their `key` and returns a `count`.
   Another usage of an annotation is e.g. for bots, who could use annotations
   to report the success/failure or progress of a command.

For example, an `m.reaction` event which `annotates` an existing event with a 👍
looks like:

```json
{
    "type": "m.reaction",
    "content": {
        "m.relationship": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    }
}
```

 * `m.replace` - Intended primarily for handling edits, these let you define
   an event which replaces an existing event.  When aggregated, returns the
   most recent replacement event (as determined by `origin_server_ts`). The
   replacement event must contain an `m.new_content` which defines the
   replacement content (allowing the normal `body` fields to be used for a
   fallback for clients who do not understand replacement events).

For instance, an `m.room.message` which `replaces` an existing event looks like:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "s/foo/bar/",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello! My name is bar",
            "msgtype": "m.text",
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id",
        }
    }
}
```

  Permalinks to edited events should capture the event ID that the sender is viewing
  at that point (which might be an edit ID).  The client viewing the permalink
  should resolve this ID to the source event ID, and then display the most recent
  version of that event.

  XXX: in future we may wish to consider ordering replacements (or relations
  in general) via a DAG rather than using `origin_server_ts` to determine
  ordering - particularly to mitigate potential abuse of edits applied by
  moderators.  Whatever, Care must be taken by the server to ensure that if
  there are multiple replacement events, the server must consistently choose
  the same one as all other servers.

 * `m.reference` - Intended in future for handling replies and threading,
   these let you define an event which references an existing event. When
   aggregated, currently doesn't do anything special, but in future could
   bundle chains of references (i.e. threads). These do not yet replace
   `m.relates_to`-style replies however.

For instance, an `m.room.message` which `references` an existing event
would look like:

```json
"type": "m.room.message",
"content": {
    "body": "i <3 shelties",
    "m.relationship": {
        "rel_type": "m.reference",
        "event_id": "$another_event_id"
    }
}
```

Different subtypes of references could be defined through additional fields on
the `m.relationship` object, to distinguish between replies, threads, etc.
This MSC doesn't attempt to define these subtypes.

  XXX: do we want to support multiple parents for a m.reference event, if a
  given event references different parents in different ways?

### Sending relations

Related events are normal Matrix events, and can be sent by the normal /send
API.

The server should postprocess relations if needed before sending
them into a room, for instance, if we ever use a DAG to define the ordering of
`m.replaces` relations, the server would be responsible for specifying the
parent pointers on the DAG.

If the user tries to send the same annotation multiple times for the same
event `type` (e.g. `m.reaction`) and aggregation `key` (e.g. 👍) then the
server should respond with 403 and error FIXME.

Similar to membership events, a convenience API is also provided to highlight
that the server may post-process the event, and whose URL structures the
semantics of the relation being sent more clearly:

```
POST /_matrix/client/r0/rooms/{roomId}/send_relation/{parent_id}/{relation_type}/{event_type}
{
    // event contents
}
```

The `parent_id` is:

  * For annotations the event being displayed (which may be an edit)
  * For replaces/edits the original event (not previous edits)
  * For references should be the event being referenced

An idempotent version is available as normal by using PUT as the HTTP method
and appending a transaction ID to the URL.

### Receiving relations

#### Unbundled relation events

Relations are received during non-gappy incremental syncs as normal discrete
Matrix events.  These are called "unbundled relation events".

There is one special case: `unsigned.count` is provided on annotation events,
calculated by the server to provide the current absolute count of the given
annotation key as of that point of the event, to avoid the client having to
accurately track the absolute value itself.

  XXX: this special case isn't implemented in Synapse yet

For instance, an incremental sync might include the following:

```json
{
    "type": "m.reaction",
    "sender": "@matthew:matrix.org",
    "content": {
        "m.relationship": {
            "rel_type": "m.annotation",
            "event_id": "$some_event_id",
            "key": "👍"
        }
    },
    "unsigned": {
        "count": 1234,
    }
}
```

...to indicate that Matthew just thumbsupped a given event, bringing the current
total to 1234 thumbsups.

#### Bundled relations

Other than during non-gappy incremental syncs, an aggregate view of relation
events should be bundled into the unsigned data of the event they relate to,
rather than sending un-bundled individual relation events.  This is called a
bundled relation (or bundled aggregation), and by sending a summary of the
aggregations, avoids us having to always send lots of individual unbundled
relation events individually to the client.

Any API which receives events should bundle relations (apart from non-gappy
incremental syncs), for instance: initial sync, gappy incremental sync,
/messages and /context.

The bundled relations are grouped according to their `rel_type`, and then
paginated within each group using Matrix's normal pagination idiom of `count`,
`limited` and `chunk` fields - respectively giving the total number of
elements in the list, whether that list has been truncated, and an array of
elements in the list.

The format of the aggregated value in the bundle depends on the relation type:

 * `m.annotation` aggregations provide the `type` of the relation event, the
   aggregation `key`, and the `count` of the number of annotations of that
   `type` and `key` which reference that event.
 * `m.replace` relations do not appear in bundled aggregations at all, as they
   instead replace the original event returned to the client (returning the most
   recent version of that event).
 * `m.reference` list the `event_id` and event `type` of the events which
   reference that event.

For instance, the below example shows an event
with four bundled relations; 3 thumbsup reaction annotations and one
reference.

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

#### Handling limited (gappy) syncs

For the special case of a gappy incremental sync, many reaction events may
have occurred during the gap.  It would be inefficient to send each one
individually to the client, but it would also be inefficient to send all
possible bundled aggregations to the client too.

The simplest thing a client can do is to just throw away its history for a
room on seeing a gappy incremental sync, and then re-paginate the history of
the room using /messages in order to get a consistent view of the relations
which may have changed during the gap.  However, this is quite inefficient,
and prohibits the client from persisting multiple sections of timeline for a
given room.

Alternatively, the server tells the client the event IDs of events which
predate the gap which received reactions during the gap.  This means that the
client can invalidate its copy of those events (if any) and then requery them
(including their bundled relations) from the server if/when needed.

The server does this with the new `stale_relations` field of each room object
in the sync response.  The `stale_relations` field lists all the event ids
prior to the gap which had updated relations during the gap.  The event ids
are grouped by relation type, and limited to N entries for efficiency.  N
should be 100.  If the number of events with stale relations exceeds N, the
list is marked as `limited` as per the normal Matrix pagination model.  We do
not include events referenced by `m.reference` as stale, in favour of more
sophisticated pagination techniques in future. For instance:

```json
"!roomid:matrix.org": {
  "account_data": {},
  "ephemeral": {},
  "state": {},
  "summary": {},
  "timeline": {},
  "unread_notifications": {},
  "stale_events": {
    "m.annotations": {
      "chunk": [
        "$12345676321:matrix.org",
        "$12345321432:matrix.org",
      ],
      "limited": false
    }
  }
}
```

This shows that in the gappy sync response, a given room has two events prior
to the gap which received new annotations during the gap. Therefore if the
client has cached a local copy of those events, it should invalidate them, and
subsequently refresh them as needed.

To refresh events, we need an API to load arbitrary events from the room in
bulk, which the CS API doesn't currently provide.  We propose extending GET
`{roomId}/event/{eventId}` to accept a list of event IDs on the URL, e.g:

`GET /_matrix/client/r0/rooms/{roomId}/event/{eventId},{eventId},{eventId}`

...which returns an array of events with the given IDs.

  XXX: Synapse hasn't implemented any of this section yet.

#### Paginating aggregations

Bundles of relations for a given event are
paginated to prevent overloading the client with relations, and may be traversed by
via the new `/relations` API (which iterates over all relations for an event) or the
new `/aggregations` API (which iterates over the groups of relations, or the relations
within a group).

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

## End to end encryption

FIXME

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

Should we enforce that each user can only send one of each type of reaction to a msg?
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

What power level do you need to be able to edit other people's messages, and how
does it fit in with fedeation event auth rules?
 * 50, by default?

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
"content": {
    "m.relates_to": {
        "m.reference": {
            "event_id": "$another:event.com"
        }
    }
}
```
versus

```json
"content": {
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
"content": {
    "emoticon": "::smile::",
    "msgtype": "?",
    "target_id": "$another:event.com"
}
```

These would then aggregated, based on target_id, and returned as annotations on
the source event in an `aggregation_data` field:

```json
"content": {
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
