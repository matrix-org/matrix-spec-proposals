# MSCXXXX: List matching push rules

This MSC proposes a way to match against a list within event content.
[MSC1796](https://github.com/matrix-org/matrix-spec-proposals/pull/1796) is an example change that
would require this list matching.


## Proposals

### Handling of lists within event data

We propose that conditons simply match any value within a list. Conditions should be evaluated against
every item in the list and return a match if any of the items meet the condition. This is compatible
with [all condition types](https://spec.matrix.org/v1.3/client-server-api/#conditions-1). For example an event:

```json
{
  "content": {
    "mentions": ["@user-a:beeper.com", "@user-b:beeper.com"]
  }
}
```

The following condition would match:

```json
{
  "kind": "event_match",
  "key": "event.content.mentions",
  "value": "@user-a:beeper.com"
}
```


## Alternatives

A new condition kind designed specifically for matching against lists could provide more options, such
as specifying if one, all or some items must match.

TODO: consider use-cases different to the example that would require more in-depth forms of matching.


## Security considerations

None.


## Unstable prefix

Not required.
