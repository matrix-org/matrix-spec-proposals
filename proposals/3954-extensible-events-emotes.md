# MSC3954: Extensible Events - Text Emotes

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers a replacement
for the `m.emote` `msgtype` specifically.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way emotes
are represented should not block the overall schema from going through.

## Proposal

MSC1767 allows for regular, non-emotive, text to be sent with an `m.message` event type and `m.text`
content block. This MSC simply introduces a new `m.emote` event type taking a **required** `m.text`
content block, enabling emotes in rooms supporting extensible events.

An example:

```json5
{
    // irrelevant fields not shown
    "type": "m.emote",
    "content": {
        "m.text": [{"body": "says hi"}]
    }
}
```

## Potential issues

No significant issues known.

## Alternatives

It may be more desirable to create an emote mixin, however that raises questions like "what does it mean
to emote a poll". For simplicity, or at least until a use case arises, this MSC aims to directly replace
the `m.emote` `msgtype` instead - a future MSC can expand support for the feature.

## Security considerations

No specific considerations are required for this proposal.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
