# MSC3966: `event_property_contains` push rule condition

[MSC3952](https://github.com/matrix-org/matrix-spec-proposals/pull/3952):
Intentional mentions requires a way for a push rule condition to search
for a value in a JSON array of values. This proposes implementing it in a
generic fashion for re-use with other push rules.

## Proposal

A new push rule condition `event_property_contains` is added which acts like
[`event_match`](https://spec.matrix.org/v1.5/client-server-api/#conditions-1),
but searches an array for an exact value. The values must match exactly and be a
non-compound JSON type allowed by [canonical JSON](https://spec.matrix.org/v1.5/appendices/#canonical-json):
i.e. strings, `null`, `true`, `false` and integers.

An example condition would look like:

```json
{
  "kind": "event_property_contains",
  "key": "content.my_array",
  "value": "foo"
}
```

This would match an event with content:

```json
{
  "content": {
    "my_array": ["foo", true]
  }
}
```

And it would not match if `my_array` was empty or did not exist.

## Potential issues

None foreseen.

## Alternatives

[MSC3887](https://github.com/matrix-org/matrix-spec-proposals/pull/3887) is an
unfinished alternative which suggests allowing [`event_match`](https://spec.matrix.org/v1.5/client-server-api/#conditions-1)
to search in arrays without other changes.

## Security considerations

It is possible for the event content to contain very large arrays (the
[maximum event size](https://spec.matrix.org/v1.5/client-server-api/#size-limits)
is 65,536 bytes, if most of that contains an array of empty strings you get
somewhere around 20,000 entries). Iterating through arrays of this size should
not be a problem for modern computers, especially since the push rule searches
for *exact* matches.

## Unstable prefix

During development `org.matrix.msc3966.exact_event_property_contains` shall be
used in place of `event_property_contains`.

## Dependencies

This MSC has similar semantics to [MSC3758](https://github.com/matrix-org/matrix-spec-proposals/pull/3758)
(and the implementation builds on that), but it does not strictly depend on it.
