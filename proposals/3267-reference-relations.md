# MSC3267: reference relationships

## Proposal

This proposal defines a relation type (using
[MSC2674 relations](https://github.com/matrix-org/matrix-doc/pull/2674))
for events to make a reference to another event.

A `rel_type` of `m.reference` is defined as a generic way to associate an
event with another event. There are no aggregation semantics applied to
this relation.

In future, this relation or similar could replace [replies](https://spec.matrix.org/v1.2/client-server-api/#rich-replies)
and aggregate into a chain of replies (simple threads).

Reference relations are used by [MSC2241](https://github.com/matrix-org/matrix-doc/pull/2241)
to tie all events together for the same verification request.

For instance, an `m.room.message` which references an existing event
would look like:

```json5
{
    // Unimportant fields omitted
    "type": "m.room.message",
    "content": {
        "msgtype": "m.text",
        "body": "i <3 shelties",
        "m.relates_to": {
            "rel_type": "m.reference",
            "event_id": "$another_event_id"
        }
    }
}
```

## Server aggregation

[MSC2674](https://github.com/matrix-org/matrix-doc/pull/2674) states
that values for `rel_type` should define how the server should aggregate the
`rel_type`, and as such this MSC deliberately has no behaviour.

In future, aggregation might be achieved with a list of event IDs for
representation by [MSC2675](https://github.com/matrix-org/matrix-doc/pull/2675) or
similar.

## Limitations

Different subtypes of references could be defined through additional fields on
the `m.relates_to` object, to distinguish between replies, threads, etc.
This MSC doesn't attempt to define these subtypes.

## Edge Cases

Can you reply (via m.references) to a [reaction](https://github.com/matrix-org/matrix-doc/pull/2677)/[edit](https://github.com/matrix-org/matrix-doc/pull/2677)?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.
 * Replying to a reaction should be treated like a normal message and have the
   reply behaviour ignored.
 * Replying to an edit should be treated in the UI as if you had replied to
   the original message.

Do we need to support retrospective references?
 * For something like "m.duplicate" to retrospectively declare that one event
   dupes another, we might need to bundle two-levels deep (subject+ref and then
   ref+target).  We can cross this bridge when we get there though, as a 4th
   aggregation type

## Unstable prefix

Unfortunately not applicable - this MSC was used in production and appears in the
specified version of the [key verification framework](https://spec.matrix.org/v1.2/client-server-api/#key-verification-framework).
