# MSC4530: Do not redact relationships

## Proposal

When someone redacts an event that is inside of a thread or is an edit revision
(i.e. `m.thread` and `m.replace` (this problem also applies to `m.annotation`) relationships),
the client will render these events as normal redacted messages on the main timeline of the room.
This leads to a lot of flood on the main timeline of the client without any context.

To fix this, in the `m.relates_to` object of the `content` object of an event,
these keys (if they're a non-empty string) and the `m.relates_to` itself (if it's a non-empty object) MUST NOT be
stripped upon receipt of a redaction event:
* `rel_type`
* `event_id`

With these keys present, the client will have enough information to correctly categorize and render the redacted event,
e.g. render the redacted event as related to a thread or an "edit revisions" list.

## Security considerations

None.

## Unstable prefix

The room version is `org.matrix.msc4530.12` based on room version 12.
