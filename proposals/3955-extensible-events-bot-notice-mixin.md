# MSC3955: Extensible Events - Automated event mixin (notices)

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers a replacement
for the `m.notice` `msgtype` specifically.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way notices
are represented should not block the overall schema from going through.

## Proposal

As mentioned in MSC1767, it is desirable to represent more than just text events as "automated" or
sent by a bot. Currently, [`m.notice`](https://spec.matrix.org/v1.5/client-server-api/#mnotice) is
defined only as a `msgtype` on `m.room.message` events, thus only allowing bots (and other automated
clients) to send plain text. To open this functionality up to any event, we define an `m.automated`
*mixin* content block that can be applied to any event:

```json5
{
    // irrelevant fields not shown
    "type": "m.emote",
    "content": {
        "m.text": [{"body": "says hi"}],
        "m.automated": true
    }
}
```

`m.automated`'s value is a boolean, defaulting to `false` when not present, to denote if an event is
automated. Note that other value types should be treated as `false` (ie: not present).

When an event is flagged as automated, the client should render that event differently compared to
normal. For example, reducing the opacity of the event.

If the client does not believe there is a material difference between automated and non-automated for
a particular event type, it is not required to render the event differently. Such an example might be
a poll: the practical difference from a user perspective of a bot sending a poll versus a user isn't
generally important, and so the client may decide to forgo opacifying the event. This is also the
default behaviour if the client does not understand the mixin: the event will be rendered normally,
with the client ultimately ignoring the `m.automated` mixin.

## Potential issues

No significant issues known.

## Alternatives

No significant alternatives known.

## Security considerations

No specific considerations are required for this proposal.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
