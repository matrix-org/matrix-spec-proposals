# MSC3758: Add `event_property_is` push rule condition kind

Currently the only condition used to match event content for push rules is the `event_match` kind.
This compares a glob-style string against a string value within the event dictionary. The event
dictionary is flattened before conditions are checked to enable matching nested values.

This approach is currently limited to only checking for string values within the event dictionary
(at any level). This MSC proposes a new exact match type for event content that works with all
JSON types.


## Proposal

### Exact matching event data

We propose a new type of condition, `event_property_is`. Similar to  the current `event_match`
([link to spec](https://spec.matrix.org/v1.3/client-server-api/#conditions-1)), this condition
takes two parameters: `value` and `key`. The exact match compares the `value` to the event data
associated with `key` exactly. Both type and content (when a string) should be identical
(include case). This allows for matching all non-compound JSON types allowed by
[canonical JSON](https://spec.matrix.org/v1.5/appendices/#canonical-json):
i.e. strings, `null`, `true`, `false` and integers. This also provides a simpler
exact string matching mechanism (and any associated performance gains on implementation side without
globbing).

An example condition may look like (encoded as a JSON object):

```json
{
  "kind": "event_property_is",
  "key": "content.is_something",
  "value": true
}
```


## Alternatives

[MSC3862](https://github.com/matrix-org/matrix-spec-proposals/pull/3862) proposes an alternative
solution by converting non-string JSON objects to strings in the `event_match` condition type.

## Security considerations

None.

## Future extensions

A future MSC may wish to define the behavior of `event_property_is` when
used with a JSON object or array.

[MSC3887](https://github.com/matrix-org/matrix-spec-proposals/pull/3887) is a
related MSC which attempts to define behavior for searching for a value inside of
an array.

## Unstable prefix

While still not part of the Matrix spec, the new push rule condition should be
`com.beeper.msc3758.exact_event_match` instead of `event_property_is`, e.g.:

```json
{
  "kind": "com.beeper.msc3758.exact_event_match",
  "key": "..."
}
```

## Dependencies

None.
