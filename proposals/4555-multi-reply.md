# MSC4555: Multiple Replies

Matrix already supports replies using `m.relates_to>m.in_reply_to`, but does not specify how to handle multiple `event_id` children fields. This could lead to breakage in clients, but it also presents opportunity for turning this into a feature. 

## Proposal

Sometimes, replying to just one message doesn't get across to all the people you mean to talk about a topic with. Replying to multiple messages solves this.

`m.in_reply_to>event_id` is turned into an array of event IDs, as well as being renamed to `event_ids`, implying there can be multiple.

This changes the JSON payload to look like such:
```json
{
  "content": {
    "m.relates_to": {
      "m.in_reply_to": {
        "event_ids": [
        	"$some_event",
        	"$another_event",
        	"$third_times_the_charm"
        ]
      }
    },
    "body": "That sounds like a great idea!"
  },
  // other fields as required by events
}
```

Clients SHOULD display replies in order of the JSON payload.

## Potential issues

A client may send a large amount of Event IDs in the array, bloating up the event's size as well as spamming the room with reply lines.

Clients should thus consider limiting the amount of replies they display. Additionally, a Policy Server can be used to limit the amount of replies a message may have.

## Alternatives

Instead of turning `event_id` into an array called `event_ids`, one could also just add more `event_id` fields to the existing JSON structure:
```json
{
  "content": {
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$another_event",
        "event_id": "$yet_another_event"
      }
    },
    "body": "That sounds like a great idea!"
  },
  // other fields as required by events
}
```

This, however, is problematic, as while technically possible, isn't supported behavior of most JSON parsers, which may lead to difficulties implementing this MSC.

## Unstable prefix

Before this MSC is merged and part of a spec release, clients should use `eu.cyrneko.msc4555.event_ids` instead of `event_ids`. Additionally, the last-selected reply Event ID should remain in the existing `event_id` field for some amount of backwards-compatibility.

the full JSON payload should then look like this:

```json
{
  "content": {
    "m.relates_to": {
      "m.in_reply_to": {
        "event_id": "$another_event",
        "eu.cyrneko.msc4555.event_ids": [
        	"$event",
        	"$another_event"
        ]
      }
    },
    "body": "That sounds like a great idea!"
  },
  // other fields as required by events
}
``` 
