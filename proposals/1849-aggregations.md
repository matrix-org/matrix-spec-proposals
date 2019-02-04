# Proposal for aggregations via m.relates_to

> WIP WIP WIP WIP WIP WIP WIP WIP WIP WIP 
>
> Checking this in so i can link to it, even though it's very much an informal draft

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

Problem:
 * Should the payload be inside or outside the E2E payload?
 * For reaction data to be useful for server-side calculated reputation work they have to be available outside E2E.   But perhaps we should be doing reputation analysis clientside instead?
   * Folks who publish reputation data could deliberately do so aggregated, and outside E2E.  They could also lie through their teeth, but they can do that anyway.
 * We will never be able to do smart aggregations over federation if these are E2E encrypted, as the server won't know that 5 x 👍 == 5👍.

And then the server just blitzes through `m.relates_to.event_id` and builds up all the relationships based on that field.
This is kinda similar to pik's proposal below, but without the JSON schema.

## CS API considerations

Then, whenever the event is served down the CS API, we inline all the relationships for a given event (modulo filters)?

For edits, we'd want the most recent relation (by default)
For reactions, we want all the reaction objects (or ideally their sum?)
For replies, we don't want the original at all; the client can load it if needed via /context.

Do we send the events down via normal pagination?  Or do we inline them?
    We should probably do both: updates come in via pagination, but when doing a limited sync,
    we should probably include them as inline as a basis.

This in turn is related to LL members: ideally we wouldn't re-load LL members from scratch after
a limited sync, but just load the difference somehow.  Similarly, we don't want to do a full snapshot
of all reactions after a limited sync, but just the base delta that changed.  Perhaps this is okay, though:
limited syncs can just include the number of reactions.

This is similar to how redactions are calculated today.  We just build up a table of which events reference
which other events, and expand out the 'join' when syncing.

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

## Federation considerations

In general, no special considerations are needed for federation; relational events are just sent as needed over federation
same as any other event type.

We need some mechanism to know whether we have synced all the relational events that exist for a given event, however.
Perhaps we should inline them into the original events, as we do on the CS API.

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