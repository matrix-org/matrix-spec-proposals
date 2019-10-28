# Label based filtering

## Problem

Rooms often contain overlapping conversations, which Matrix should help users
navigate.

## Context

We already have the concept of 'Replies' to define which messages are
responses to which, which [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849)
proposes extending into a generic mechanism for defining threads which could
(in future) be paginated both depth-wise and breadth-wise.  Meanwhile,
[MSC1198](https://github.com/matrix-org/matrix-doc/issues/1198) is an alternate
proposal for threading, which separates conversations into high-level "swim
lanes" with a new `POST /rooms/{roomId}/thread` API.

However, fully generic threading (which could be used to implement forum or
email style semantics) runs a risk of being overly complicated to specify and
implement and could result in feature creep.  This is doubly true if you try
to implement retrospective threading (e.g. to allow moderators to split off
messages into their own thread, as you might do in a forum or to help manage
conversation in a busy chatroom).

Therefore, this is a simpler proposal to allow messages in a room to be
filtered based on a given label in order to give basic one-layer-deep
threading functionality.

## Proposal

We let users specify an optional `m.label` field onto events (outside of E2E
contents) which provides a list of freeform text labels for the events they
send.  Clients can use these to filter the overlapping conversations in a room
into different topics.  The labels could also be used when bridging as a
hashtag to help manage the disconnect which can happen when bridging a
threaded room to an unthreaded one.

Example:

```json
{
  "type": "m.room.message",
  "content": {
    "body": "who wants to go down the pub?",
    "msgtype": "m.text",
    "m.label": [ "#fun" ]
  }
}
```

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "AwgAEpABm6.......",
    "device_id": "SOLZHNGTZT",
    "sender_key": "FRlkQA1enABuOH4xipzJJ/oD8fxiQHj6jrAyyrvzSTY",
    "session_id": "JPWczbhnAivenK3qRwqLLBQu4W13fz1lqQpXDlpZzCg",
    "m.label": [ "#work" ]
  },
}
```

Labels which are prefixed with # are expected to be user-visible and exposed
to the user as a hashtag, letting the user filter their current room by the
various hashtags present within it.

Clients are expected to explicitly set the label on a message if the user's
intention is to respond as part of a given labelled topic.  For instance, if
the user is currently filtered to only view messages with a given label, then
new messages sent should use the same label.  Similarly if the user sends a
reply to a given message, that reply should typically use the same labels as
the message being replied to.

The convention is to use hashtag style human-visible labels prefixed with a #,
but one could also use a unique ID (e.g. thread ID bridged from another
platform) without a # prefix).

When a user wants to filter a room to given label(s), it defines a filter for
use with /sync or /messages to limit appropriately. This is done by new
`labels` and `not_labels` fields to the `EventFilter` object, which specifies
a list of labels to include or exclude in the given filter.

## Problems

Do we care about internationalising hashtags?

Too many threading APIs?

## Unstable prefix

Unstable implementations should hook up `org.matrix.label` rather than `m.label`.
