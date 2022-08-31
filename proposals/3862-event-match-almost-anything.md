# MSC3862: event_match (almost) anything

The [`event_match`] condition kind on push rules currently only
matches string values. This is limiting because some event types have
important information in boolean or integer fields that currently cannot
be matched against.

[MSC3758] tries to address this by introducing a new condition kind
`exact_event_match`. The current proposal takes a different route by
generalising the existing `event_match` condition kind to work on any
primitive value.

## Proposal

In order to apply an `event_match` condition, homeservers transform all
primitive values in the event body into a lowercase string
representation. In particular this means

- Strings are converted into case-insensitive strings (this already happens today)
- `true` / `false` become `"true"` / `"false"`
- Integers such as `123` become `"123"`
- `null` becomes `"null"`

This transformation is applied regardless of how deeply the value is
nested but not if the value is part of an array. Arrays – which are not
primitive values – and their elements are not converted. This means
that, as before, it's not possible to match anything inside an array.

For the avoidance of doubt, the exemplary event body

    {
      "a": "string",
      "b": true,
      "c": {
        "d": 1,
        "e": null
      },
      "f": [1]
    }

is transformed into

    {
      "a": "string",
      "b": "true",
      "c": {
        "d": "1",
        "e": "null"
      },
      "f": [1]
    }

After the transformation the condition is evaluated on the string
representations.

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
existing specification of `event_match` already allows for exact matches
on strings and the proposal at hand offers a lightweight generalisation
to other primitive types that is both easy to implement (see
e.g. [matrix-org/synapse#13466]) and use.

## Security considerations

None.

  [`event_match`]: https://spec.matrix.org/v1.3/client-server-api/#conditions-1
  [spec]: https://spec.matrix.org/v1.3/client-server-api/#conditions-1
  [MSC3758]: https://github.com/matrix-org/matrix-spec-proposals/pull/3758
  [matrix-org/synapse#13466]: https://github.com/matrix-org/synapse/pull/13466
