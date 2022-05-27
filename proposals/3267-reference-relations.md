# MSC3267: reference relationships

## Proposal

This proposal defines a relation type (using
[MSC2674 relations](https://github.com/matrix-org/matrix-doc/pull/2674))
for events to make a reference to another event.

A `rel_type` of `m.reference` is defined as a generic way to associate an
event with another event. As a bundle, `m.reference` relations appear as
an object with a single `chunk` field. The `chunk` is an array of objects
with a single `event_id` field for all the child events which `m.reference`
the parent.

There are no implied semantics by a reference relation: the feature or event
type which makes use of the `rel_type` should specify what sort of semantic
behaviour there is, if any. For example, describing that a poll response event
*references* the poll start event, or that a location update *references* a
previous location update.

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
`rel_type`. For `m.reference`, child events are bundled to appear as follows
under `m.relations`:

```json5
{
  "m.reference": {
    "chunk": [
      {"event_id": "$one"},
      {"event_id": "$two"},
      {"event_id": "$three"}
    ]
  }
}
```

Note that currently only the `event_id` is noted in the chunk, however a future
MSC might add more fields.

## Limitations

Different subtypes of references could be defined through additional fields on
the `m.relates_to` object, to distinguish between other forms of semantic behaviour
indepdent of type (hypothetical threads, replies, etc if we didn't have a system
for them already). This MSC doesn't attempt to define these subtypes.

This relation cannot be used in conjunction with another relation due to `rel_type`
being a single value. This is known and unfortunately not resolved by this MSC.
A future MSC might address the concern.

## Edge Cases

Can you reference an event which doesn't have logical meaning? Eg to a [reaction](https://github.com/matrix-org/matrix-doc/pull/2677)?
 * Yes, at the protocol level.  But you shouldn't expect clients to do anything
   useful with it.
 * The relationship is effectively pointless, so the event would appear as though
   there was no reference relationship.

Do we need to support retrospective references?
 * For something like "m.duplicate" to retrospectively declare that one event
   dupes another, we might need to bundle two-levels deep (subject+ref and then
   ref+target).  We can cross this bridge when we get there though, as another
   aggregation type

## Unstable prefix

Unfortunately not applicable - this MSC was used in production and appears in the
specified version of the [key verification framework](https://spec.matrix.org/v1.2/client-server-api/#key-verification-framework).
