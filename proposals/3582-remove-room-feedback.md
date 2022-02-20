# MSC3582: Remove m.room.message.feedback

The spec defines an
[`m.room.message.feedback`](https://spec.matrix.org/unstable/client-server-api/#mroommessagefeedback)
event that

- is obsoleted by read receipts,
- is not used by anyone anywhere, and
- is discouraged by the spec.

See also: https://github.com/matrix-org/matrix-doc/issues/3318

## Proposal

The `m.room.message.feedback` event should be removed from the spec.
