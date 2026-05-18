# MSC0000: Clarify usage of content blocks in Extensible Events

[MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767) defines the basics for "Extensible Events".
In contrast to previous event definition, this introduces a way to modularly compose Matrix event types,
including benefits such as automatic fallback handling of unknown event types.

This MSC aims to adjust MSC1767 slightly to clarify some details of the concept based on practical experience gained
from implementing the unstable MSC and its siblings, and evidence of the greater concept that is distributed across the
same siblings but not stated explicitly or obviously.

## Proposal

MSC1767 defines the concept of "content blocks".

This MSC clarifies that content blocks MUST (not "can") be defined independently of events,
and event type definitions MUST draw (exclusively) on these existing definitions to compose an event type.
Content blocks can also be nested, e.g. to alias them,
such as in [MSC3551](https://github.com/matrix-org/matrix-spec-proposals/pull/3551)
which defines `m.caption` to contain exactly one `m.text` content block,
and MAY be used exclusively as a non-root property of `content`.

This behavior is clearly necessary for the fallback behavior central to extensible events:  
The "extensibility" property is based from the idea that if a receiver does not understand some event type,
it should guess the best match of a type it does understand based on the content blocks present and render it as that.
If follows that `m.text`, at least at events' content "root",
must always behave at least in a way that makes it compatible to the `m.message` type as a fallback.
As content blocks are supposed to be reusable,
it is also logical to impose the same behaviour when nested inside another content block.

MSC1767 is modified thus:

- Each content block MUST be defined exactly once.
- The context in which a content block is used MAY impose additional restrictions to it as,
  long as these restrictions leave it compatible with its general definition.

For example, an "OPTIONAL" attribute MAY be "REQUIRED" if defined by a certain context *containing* the content block,
such as an event type or other content block definition.
Regard `m.text` as defined by MSC1767.
Then we can create a new content block `dev.fitko.neo.label.v1`.
It consists of a nested `m.text` content block,
which MUST contain a plain text representation.
Clients ignore any representations using different `mimetypes`.

```jsonc
"dev.fitko.neo.label.v1": {
  "m.text": [
    { "body": "Open Website" }
  ]
}
```

[... maybe more]

## Potential issues

To the knowledge of the author, this proposal only makes explicit what is already the spirit of the accepted proposal
and thus introduces no new issues.

The criteria could technically be relaxed to allow more free behaviour in case of nesting,
but no benefits over creating a "regular" custom field are known.

## Alternatives

No known alternatives.

## Security considerations

**All proposals must now have this section, even if it is to say there are no security issues.**

No known security implications.
Regular event content validation applies.

## Unstable prefix

To the knowledge of the author, this proposal only makes explicit what is already the spirit of the accepted proposal.
It thus does not need any change in behavior in implementations nor a new prefix version.

## Dependencies

This MSC builds on MSC1767, which has been accepted but is blocked by the rest of the
[core Extensible Events](https://github.com/orgs/matrix-org/projects/108/views/7).
