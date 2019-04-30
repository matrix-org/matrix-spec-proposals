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

`m.relates_to` is the signal to the server that the fields within describe
aggregation operations.

We would like to add support for other types of relations, including message
editing and reactions.


## Types of relations

There are three broad types of relations: annotations, replacements and
references.

Annotations are things like reactions, which should be displayed alongside the
original event. These should support be aggregated so that e.g. if twenty people
"likes" an event we can bundle the twenty events together when sending the
original event to clients. Another usage of an annotation is e.g. for bots, who
could use annotations to report the success/failure or progress of a command.

Replacements are essentially edits, and indicate that instead of giving clients
the original event they should be handed the replacement event instead. Clients
should be able to request all replacements of an event, i.e. the "edit history".

References things like replies, where a later event refers to an earlier event
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
reactions would be implemented as a `m.reaction` with aggration key of e.g.
`👍`.

    TODO: Should we include anything other than event type, aggregation key and
    count?


Replacements replace the original event, and so no aggregation is required.
Though care must be taken by the server to ensure that if there are multiple
replacement events it consistently chooses the same one as all other servers.
The replacement event should also include a reference to the original event ID
so that clients can tell that the message has been edited.

For references the original event should include the list of `type` and
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
        "m.relates_to": {
            "type": "m.references",
            "event_id": "$some_event_id"
        }
    }
}
```

And a reaction might look like the following, where we define for `m.reaction`
that the aggregation key is the unicode reaction itself.

```json
{
    "type": "m.reaction",
    "contents": {
        "m.relates_to": {
            "type": "m.annotation",
            "event_id": "$some_event_id",
            "aggregation_key": "👍"
        }
    }
}
```

    TODO: This limits an event to only having one relation, on the assumption
    that there are no use cases and that it will make life simpler.


An event that has relations might look something like:

```json
{
    ...,
    "unsigned": {
        "m.relations": {
            "m.annotation": [
                {
                    "type": "m.reaction",
                    "aggregation_key": "👍",
                    "count": 3
                }
            ],
            "m.reference": {
                "chunk": [
                    {
                        "type": "m.room.message",
                        "event_id": "$some_event"
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

Since the server bundles related events the relation information must not be
encrypted.

For aggregations of annotations there are two options:

1. Don't group together annotations and have the aggregation_key encrypted, so
   as to not leak how someone reacted (though server would still see that they
   did).
2. In some way encrypt the `aggregation_key`, with the properties that different
   users and clients reacting in the same way to the same event produce the same
   `aggregation_key`, but isn't something the server can calculate and is
   different between different events (to stop statistical analysis). Clients
   also need to be able to go from encrypted `aggregation_key` to the actual
   reaction.

   One suggestion here was to use the decryption key of the event as a base for
   a shared secret.


## CS API

Sending a related event uses an equivalent of the normal send API (with an
equivalent `PUT` API):

```
POST /_matrix/client/r0/rooms/{roomId}/send_relation/{parent_id}/{relation_type}/{event_type}
{
    // event contents
}
```

Whenever an event that has relations is sent to the client, e.g. pagination,
event search etc, the server bundles the relations into the event as per above.

The `parent_id` is:

  * For annotations the event being displayed (which may be an edit)
  * For replaces/edits the original event (not previous edits)
  * For references should be the original event (?)

The same happens in the sync API, however the client will need to handle new
relations themselves when they come down incremental sync.


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
   Socially this probably doesn't work as reactions will likely drop-off over
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
      "annotation_key": ""
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
          "aggregation_key": "",
          "count": 1,
          "chunk": [
            {
              "state": "success",
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

  * How does this work with end to end? How do we encrypt the `m.summary`?
  * We would end up including old annotations that had been superceded, should
    these be done via edits instead?


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
