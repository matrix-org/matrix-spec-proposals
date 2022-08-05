# MSC0000: event_match (almost) anything

The `event_match` condition kind on push rules currently only matches
string values. This is limiting because some event types have important
information in boolean or integer fields that currently cannot be
matched against.

[MSC3758] tries to address this by introducing a new condition kind
`exact_event_match`. The current proposal takes a different route by
generalising the existing `event_match` condition kind to work on any
primitive value.

## Proposal

In order to apply an `event_match` condition, home servers transform all
primitive values in the event body into a lowercase string
representation. In particular this means

- Strings are converted into lowercase (this already happens today)
- `true` / `false` become `"true"` / `"false"`
- Integers such as `123` become `"123"`
- `null` becomes `"null"`
- Arrays remain unchanged
- Nested objects are handled recursively, their values being transformed
  according to the rules above

After the transformation the condition is evaluated on the string
representations.

In order to reflect these changes, the wording in the spec is updated.
Specifically

> **event_match** This is a glob pattern match on a field of the event.

is changed to

> **event_match** This is a glob pattern match on any primitive field of
> the event. Non-string values are converted to their lowercased string
> representation before attempting the match.

and

> If the property specified by `key` is completely absent from the
> event, or does not have a string value, then the condition will not
> match, even if `pattern` is `*`.

is changed to

> If the property specified by `key` is completely absent from the
> event, then the condition will not match, even if `pattern` is `*`.

## Potential issues

It is possible for JSON values of different data types to map to the
same string representation (e.g. `0` and `"0"` or `true` and `"true"`).
These values are not possible to differentiate with the generalised
`event_match` condition kind as described in this proposal. However, in
practice it is rare for two events to differ only in the data type of a
particular field. If that happens, it’s most probably due to the
evolution of an unstable event type in which case it’s likely desirable
to treat both data types identically anyway.

## Alternatives

As mentioned earlier, [MSC3758] provides an alternative by introducing
a new condition kind `exact_event_match`. While being more powerful,
this option is also more invasive, complicating the push rule API. The
existing specifcation of `event_match` already allows for exact matches
on strings and the proposal at hand offers a lightweight generalisation
to other primitive types that is both easy to implement (see
e.g. [matrix-org/synapse#13466]) and use.

## Security considerations

None.

  [MSC3758]: https://github.com/matrix-org/matrix-spec-proposals/pull/3758
  [matrix-org/synapse#13466]: https://github.com/matrix-org/synapse/pull/13466
