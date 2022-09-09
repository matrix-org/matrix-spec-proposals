# MSC3758: Expand push rule conditions

Currently the only condition used to match event content for push rules is the `event_match` kind.
This compares a glob-style string against a string value within the event dictionary. The event
dictionary is flattened before conditions are checked to enable mathing nested values.

This approach is currently limited to only checking for string values within the event dictionary
(at any level). This MSC proposes a new exact match type for event content that works with all
JSON types.


## Proposals

### Exact matching event data

We propose a new type of condition, `exact_event_match`. Similar to `event_match`, this condition
takes two parameters: `pattern` and `key`. The exact match compares the `pattern` to the event data
associated with `key` exactly. Both type and content (when a string) should be identical. This allows
for matching all valid JSON types `null`, `true`, `false` and numbers. This also provides a simpler
exact string matching mechanism (and any associated performance gains on implementation side without
globbing).

An example condition may look like (encoded as a JSON object):

```json
{
  "kind": "exact_event_match",
  "key": "event.content.is_something",
  "pattern": true
}
```


## Alternatives
