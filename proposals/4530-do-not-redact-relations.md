# MSC4530: Do not redact relationships

## Proposal

When someone redacts an event that is inside of a thread or is an edit revision
(i.e. `m.thread` and `m.replace` (this problem also applies to `m.annotation`) relationships),
the client will render these events as normal redacted messages on the main timeline of the room.
This leads to a lot of flood on the main timeline of the client without any context.

To fix this, in the `m.relates_to` object of the `content` object of an event,
these keys MUST NOT be stripped upon receipt of a redaction event:
* `rel_type`
* `event_id`

For [fallback](https://spec.matrix.org/v1.19/client-server-api/#fallback-for-unthreaded-clients) and context reasons,
`m.in_reply_to` and `is_falling_back` keys MUST NOT be stripped in the `m.relates_to` object of the `content` object
if the `rel_type` key's value is `m.thread` in the `m.relates_to` object of the `content` object.

With these keys present, the client will have enough information to correctly categorize and render the redacted event,
e.g. render the redacted event as related to a thread or an "edit revisions" list.

## Alternatives

### Do not strip `m.in_reply_to` unconditionally as well

I believe this key should be stripped for unthreaded messages, as it doesn't affect the problem described and looks
like the expected behavior in simple replies for privacy reasons.
Compared to these simple replies, for threads it's important to keep all of the context.

## Security considerations

None.
