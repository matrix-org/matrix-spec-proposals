# Proposal for aggregations via m.relates_to

> WIP WIP WIP WIP WIP WIP WIP WIP WIP WIP 

A very rough WIP set of notes on how relations could work in Matrix.

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

`m.relates_to` is the signal to the server that the fields within describe aggregation operations.

This is a bit clunky as for other types of relations, we end up duplicating the "m.in_reply_to"
type between the event type and the relationship type.
So instead, perhaps we should only specify a relationship type if strictly needed, e.g.:

```json
"type": "m.room.message",
"contents": {
    "m.relates_to": {
        "event_id": "$another:event.com",
        "type": "m.reply"
    }
}
```

and

```json
"type": "m.reaction",
"contents": {
    "m.text": "👍",
    "m.relates_to": {
        "event_id": "$another:event.com",
    }
}
```

or if building a relation DAG (for ordering for edits, and for pulling in missing relations after a federation outage):

```json
"type": "m.reaction",
"contents": {
    "m.text": "👍",
    "m.relates_to": {
        "event_id": ["$another:event.com", "$another2:event.com"]
    }
}
```

And then the server just blitzes through `m.relates_to.event_id` and builds up all the relationships based on that field.
This is kinda similar to pik's proposal below, but without the JSON schema.

XXX: `event_id` should take either a string or a list of strings, to support relation DAGs (needed for ordering edits)

## CS API considerations

Then, whenever the event is served down the CS API, we inline the relations for a given event (modulo filters)?

For edits, we'd want the most recent relation (by default)
For reactions, we want all the reaction objects (or ideally their sum?)
For replies, we don't want the original at all; the client can load it if needed via /context.

We should send the aggregated event down during normal pagination,
as well as the individual relations down incrementally during sync.

After a limited sync, we should send a fresh aggregated event rather
than try to calculate a delta.

This is similar to how redactions are calculated today.  We just build up a table of which events reference
which other events, and expand them out when syncing.

So:

```json
"type": "m.room.message",
"event_id": "$another:event.com",
"contents": {
    "m.text": "I have an excellent idea",
},
"relations": [
    {
        "type": "m.reaction",
        "event_id": "$reaction:alice.com",
        "sender": "@alice:alice.com",
        "contents": {
            "m.text": "👍",
        }
    },
    {
        "type": "m.reaction",
        "event_id": "$reaction2:bob.com",
        "sender": "@bob:bob.com",
        "contents": {
            "m.text": "👎",
        }
    },
]
```

## Sending relations

PUT /_matrix/client/r0/rooms/{roomId}/send_relation/{parent_id}/{eventType}/{txnId}
```json
{
    "m.text": "👍",
}
```

N.B. that the server then gets to populate out the m.relates_to field itself,
adding the `parent_id` as one parent, but also adding any other dangling relations-dag extremitie.

## Receiving relations

TODO:

 * /sync
 * /messages
 * /context

## Pagination considerations

How do we handle 20K edits in a row?
 * we need to paginate 'vertically' somehow

How do we handle a message with 20K different emojis?
 * we need to paginate 'horizontally' somehow - return the 10 most popular emojis?

Do relations automatically give us threads somehow?
 * No; we will at the least need to define how to permalink to a relation then and then paginate around it.

## Edge cases

XXX: What happens when you react to an edit?
 * You should be able to, but the reaction should be attributed to the edit (or its contents) rather than the message as a whole.
 * So how do you aggregate?

How do you handle racing edits?
 * The edits could form a DAG of relations for robustness.
    * Tie-break between forward DAG extremities based on origin_ts
    * m.relates_to should be able to take an array of event_ids.
 * ...or do we just always tiebreak on origin_ts, and rely on a social problem for it not to be abused?
    * problem is that other relation types might well need a more robust way of ordering.

Redactions
 * Redacting an edited event in the UI should redact the original; the client will need to redact the original event to make this happen.
 * Clients could also try to expand the relations and redact those too if they wanted to, but in practice the server shouldn't send down relations to redacted messages, so it's overkill.
 * You can also redact specific relations if needed (e.g. to remove a reaction from ever happening)
 * If you redact an relation, we keep the relation DAG (and solve that metadata leak alongside our others)

What does it mean to call /context on a relation?
 * We should probably just return the root event for now, and then refine it in future for threading?

## E2E considerations

In E2E rooms:
 * The payload should be encrypted.  This means that we can't sum emoji reactions serverside;
   they'll have to be passed around one by one.  Given E2E rooms tend to be smaller, this is
   hopefully not a major problem.  We could reduce bandwidth by reusing the same key to
   encrypt the relations as the original message.
   * This means that reputation data can't be calculated serverside for E2E rooms however.
   * It might be okay to calculate it clientside?  Or we could special-case reputation data to not be E2E?
 * The m.relates_to field however should not be encrypted, so that the server can use it for
   performing aggregations where possible (e.g. returning only the most recent edit).

## Federation considerations

In general, no special considerations are needed for federation; relational events are just sent as needed over federation
same as any other event type - aggregated onto the original event if needed.

XXX: We have a problem with resynchronising relations after a gap in federation.
We have no way of knowing that an edit happened in the gap to one of the events
we already have.  So, we'll show inconsistent data until we backfill the gap.
 * We could write this off as a limitation.
 * Or we could make *ALL* relations a DAG, so we can spot holes at the next relation, and
   go walk the DAG to pull in the missing relations?  Then, the next relation for an event
   could pull in any of the missing relations.
 * Could we also ask the server, after a gap, to provide all the relations which happened during the gap to events whose root preceeded the gap.
   * "Give me all relations which happened between this set of forward-extremities when I lost sync, and the point i've rejoined the DAG, for events which preceeded the gap"?

In future, we might want to aggregate relational events (e.g. send a summary of the events, rather than the
actual original events).  This requires the payload to be non-E2E encrypted, and would also require some kind of
challenge-response mechanism to prove that the summary is accurate to the recipients (a ZK mechanism of some kind).
In some ways this is a subset of the more general problem of how we can efficiently send summaries of rooms and even
room state over federation without having to send all the events up front.

## Historical context

pik's MSC441 has:

Define the JSON schema for the aggregation event, so the server can work out which fields should be aggregated.

```json
"type": "m.room._aggregation.emoticon",
"contents": {
    "emoticon": "::smile::",
    "msgtype": "?",
    "target_id": "$another:event.com"
}
```

These would then aggregated, based on target_id, and returned as annotations on the source event in an
`aggregation_data` field:

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