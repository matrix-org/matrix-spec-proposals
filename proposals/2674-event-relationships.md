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
* [MSC3267](https://github.com/matrix-org/matrix-doc/pull/3267) defines how events
  can make a reference to other events.
* [MSC3389](https://github.com/matrix-org/matrix-doc/pull/3389) defines changes to
  the redaction algorithm, to preserve the type and target id of a relation.


## Proposal

This proposal introduces the concept of relations, which can be used to
associate new information with an existing event.

A relationship is an object with a field `rel_type`, which is a string describing the type of relation,
and a field `event_id`, which is a string that represents the event_id of the target event of this relation.
The target event must exist in the same room as the relating event is sent.
Both of those fields are required. An event is said to contain a relationship if its `content` contains
a relationship with all the required fields under the `m.relates_to` key. If any of these conditions is not met,
clients and servers should treat the event as if it does not contain a relationship.
Servers should reject events not meeting these conditions with an HTTP 400 error when
they are received via the client-server API.

Here's a (partial) example of an event relating to another event:

```json
{
  "content": {
      "m.relates_to": {
          "rel_type": "m.replace",
          "event_id": "$abc:server.tld"
      }
  }
}
```

All the information about the relationship lives under the `m.relates_to` key.

If it helps, you can think of relations as a "subject verb object" triple,
where the subject is the relation event itself; the verb is the `rel_type`
field of the `m.relates_to` and the object is the `event_id` field.

We consciously do not support multiple different relations within a single event,
in order to keep the API simple.  This means that if event A relates to event B
in two different ways you would send two events to describe the two relations,
rather than bundling them into a single event.  Another MSC,
like [MSC 3051](https://github.com/matrix-org/matrix-doc/pull/3051),
can propose a change to add support for multiple relations if it turns out that
this would facilitate certain use cases.

Relations do not yet replace the 
[reply mechanism currently defined in the spec](https://matrix.org/docs/spec/client_server/r0.6.1#rich-replies).

### Relation types

Any values for `rel_type` should abide the
[general guidelines for identifiers](https://github.com/matrix-org/matrix-doc/pull/3171).

The `rel_type` property determines how an event relates to another and can be used
by clients to determine how and in what context a relation should be displayed.

[MSC 2675](https://github.com/matrix-org/matrix-doc/pull/2675) proposes to also interpret the `rel_type` server-side.

It is left up to the discretion of other MSCs building on this one whether they introduce
`rel_type`s that are specific to their use case or that can serve a broad range
of use cases. MSCs may define additional properties on the relation object for a given `rel_type`.

Currently, a few `rel_type`s are already proposed. Here's a non-exhaustive list:

 - `m.replace` in [MSC 2676](https://github.com/matrix-org/matrix-doc/pull/2676).
 - `m.annotation` in [MSC 2677](https://github.com/matrix-org/matrix-doc/pull/2677).
 - `m.reference` in [MSC 3267](https://github.com/matrix-org/matrix-doc/pull/3267).
 - `m.thread` in [MSC 3440](https://github.com/matrix-org/matrix-doc/pull/3440).


### Sending relations

Related events are normal Matrix events, and can be sent by the normal `/send`
API.

The server should postprocess relations if needed before sending them into a
room, as defined by the relationship type. For example, a relationship type
might only allow a user to send one related message to a given event.

### Receiving relations

Relations are received like other non-state events, with `/sync`,
`/messages` and `/context`, as normal discrete Matrix events. As explained
in the limitations, clients may be unaware of some relations using just these endpoints.

[MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) defines ways in
which the server may aid clients in processing relations by aggregating the
events.

### Redactions

Events with a relation may be redacted like any other event.

[MSC3389](https://github.com/matrix-org/matrix-doc/pull/3389) proposes that
the redaction algorithm should preserve the type and target id of a relation.

However, event relationships can still be used in existing room versions, but
the user experience may be worse if redactions are performed.

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
   happened during the gap to events whose root preceded the gap.
   * "Give me all relations which happened between this set of
     forward-extremities when I lost sync, and the point i've rejoined the DAG,
     for events which preceded the gap"?
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
 * In practice this seems to not be an issue, which is worth complicating
   the s-s API over. Clients very rarely jump over the federation gap to an edit.
   In most cases they scroll up, which backfills the server and we have all the
   edits, when we reach the event before the gap.
 
## Limitations

Based solely on this MSC, relations are only received as discrete events in
the timeline, so clients may only have an incomplete image of all the relations
with an event if they do not fill gaps (syncs with a since token that have 
`limited: true` set in the sync response for a room) in the timeline.

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
 * This format is now in use in the wider matrix ecosystem without a prefix,
   in spite of the original MSC 1849 not being merged. This situation is not ideal
   but we still don't want to break compatibility with several clients.
 * We don't need the extra indirection to let multiple relations apply to a given pair of
   events, as that should be expressed as separate relation events.
 * If we want 'adverbs' to apply to 'verbs' in the subject-verb-object triples which
   relations form, then we apply it as mixins to the relation data itself rather than trying
   to construct subject-verb-verb-object sentences.
 * We decided to not adopt the format used by `m.in_reply_to` as it allows for multiple relations
   and is hence overly flexible. Also, the relation type of `m.in_reply_to` is also overly specific
   judged by the guidelines for `rel_type`s laid out in this MSC. Having replies use the same
   format as relations is postponed to a later MSC, but it would likely involve replies
   adopting the relation format with a more broadly useful `rel_type` (possibly the `m.reference`
   type proposed in [MSC3267](https://github.com/matrix-org/matrix-doc/pull/3267)),
   rather than relations adopting the replies format.

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

These would then be aggregated, based on target_id, and returned as annotations on
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
