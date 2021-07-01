# MSC2674: Event relationships

It's common to want to send events in Matrix which relate to existing events -
for instance, reactions, edits and even replies/threads.

This proposal is one in a series of proposals that defines a mechanism for
events to relate to each other.  Together, these proposals replace
[MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849).

* This proposal defines a standard shape for indicating events which relate to
  other events.
* [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines APIs to
  let the server calculate the aggregations on behalf of the client, and so
  bundle the related events with the original event where appropriate.
* [MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676) defines how
  users can edit messages using this mechanism.
* [MSC2677](https://github.com/matrix-org/matrix-doc/pull/2677) defines how
  users can annotate events, such as reacting to events with emoji, using this
  mechanism.

## Proposal

This proposal introduces the concept of relations, which can be used to
associate new information with an existing event.

Relations are any event which have an `m.relates_to` field in their
contents. The `m.relates_to` field must include a `rel_type` field that
gives the type of relationship being defined, and an `event_id` field that
gives the event which is the target of the relation. All the information about
the relationship lives under the `m.relates_to` key.

If it helps, you can think of relations as a "subject verb object" triple,
where the subject is the relation event itself; the verb is the `rel_type`
field of the `m.relates_to` and the object is the `event_id` field.

We consciously do not support multiple different relations within a single event,
in order to keep the API simple. Another MSC,
like [MSC 3051](https://github.com/matrix-org/matrix-doc/pull/3051),
can propose a change to add support for multiple relations if it turns out that
this would facilitate certain use cases.

Different subtypes of references could be defined through additional fields on
the `m.relates_to` object, to distinguish between replies, threads, etc.
This MSC doesn't attempt to define these subtypes.

### Sending relations

Related events are normal Matrix events, and can be sent by the normal /send
API.

The server should postprocess relations if needed before sending them into a
room, as defined by the relationship type. For example, a relationship type
might only allow a user to send one related message to a given event.

### Receiving relations

Relations are received during non-gappy incremental syncs (that is, syncs
called with a `since` token, and that have `limited: false` in the portion of
response for the given room) as normal discrete Matrix events.

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines ways in
which the server may aid clients in processing relations by aggregating the
events.

### Redactions

Relations may be redacted like any other event.

The `m.relates_to`.`rel_type` and `m.relates_to`.`event_id` fields should
be preserved over redactions, so that clients can distinguish redacted edits
from normal redacted messages, and maintain reply ordering.

  FIXME: synapse doesn't do this yet

This modification to the redaction algorithm requires a new room version.
However, event relationships can still be used in existing room versions, but
the user experince may worse if redactions are performed.

## Edge Cases

Can you reply (via m.references) to a [reaction](https://github.com/matrix-org/matrix-doc/pull/2677)/[edit](https://github.com/matrix-org/matrix-doc/pull/2677)?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.
 * Replying to a reaction should be treated like a normal message and have the
   reply behaviour ignored.
 * Replying to an edit should be treated in the UI as if you had replied to
   the original message.

What does it mean to call /context on a relation?
 * We should probably just return the root event for now, and then refine it in
   future for threading?
 * XXX: what does synapse do here?

Do we need to support retrospective references?
 * For something like "m.duplicate" to retrospectively declare that one event
   dupes another, we might need to bundle two-levels deep (subject+ref and then
   ref+target).  We can cross this bridge when we get there though, as a 4th
   aggregation type

## Potential issues

### Federation considerations

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

## Limitations

Based solely on this MSC, relations are only received as discrete events in
the timeline, so clients may only have an incomplete image of all the relations
with an event if they do not fill gaps in the timeline.

In practice, this has proven not to be too big of a problem, as reactions
(as proposed in [MSC 2677](https://github.com/matrix-org/matrix-doc/pull/2677))
tend to be posted close after the target event in the timeline.

A more complete solution to this has been deferred to
[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675). 

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
