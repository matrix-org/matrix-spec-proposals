# Label based filtering

## Problem

Rooms often contain overlapping conversations, which Matrix should help users
navigate.

## Context

We already have the concept of 'Replies' to define which messages are responses
to which, which [MSC1849](https://github.com/matrix-org/matrix-doc/pull/1849)
proposes extending into a generic mechanism for defining threads which could (in
future) be paginated both depth-wise and breadth-wise.  Meanwhile,
[MSC1198](https://github.com/matrix-org/matrix-doc/issues/1198) is an alternate
proposal for threading, which separates conversations into high-level "swim
lanes" with a new `POST /rooms/{roomId}/thread` API.

However, fully generic threading (which could be used to implement forum or
email style semantics) runs a risk of being overly complicated to specify and
implement and could result in feature creep. This is doubly true if you try to
implement retrospective threading (e.g. to allow moderators to split off
messages into their own thread, as you might do in a forum or to help manage
conversation in a busy chatroom).

Therefore, this is a simpler proposal to allow messages in a room to be filtered
based on a given label in order to give basic one-layer-deep threading
functionality.

## Proposal

We let users specify an optional `m.labels` field onto the events. This field
maps key strings to freeform text labels:

```json
{
  // ...
  "m.labels": {
    "somekey": "somelabel"
  }
}
```

Labels which are prefixed with # are expected to be user-visible and exposed to
the user by clients as a hashtag, letting the user filter their current room by
the various hashtags present within it. Labels which are not prefixed with # are
expected to be hidden from the user by clients (so that they can be used as
e.g. thread IDs bridged from another platform).

Clients can use these to filter the overlapping conversations in a room into
different topics. The labels could also be used when bridging as a hashtag to
help manage the disconnect which can happen when bridging a threaded room to an
unthreaded one.

Clients are expected to explicitly set the label on a message if the user's
intention is to respond as part of a given labelled topic.  For instance, if the
user is currently filtered to only view messages with a given label, then new
messages sent should use the same label. Similarly if the user sends a reply to
a given message, that reply should typically use the same labels as the message
being replied to.

When a user wants to filter a room to given label(s), it defines a filter for
use with /sync or /messages to limit appropriately. This is done by new `labels`
and `not_labels` fields to the `EventFilter` object, which specifies a list of
labels to include or exclude in the given filter.

### Encrypted rooms

In encrypted events, the string used as the key in the map is a SHA256 hash of a
contatenation of the text label and the ID of the room the event is being sent
to. Once encrypted by the client, the resulting `m.room.encrypted` event's
content contains a `m.labels_hashes` property which is an array of these hashes.

When filtering events based on their label(s), clients are expected to use the
hash of the label(s) to filter in or out instead of the actual label text.

#### Example

Consider a label `#fun` on a message sent to a room which ID is
`!someroom:example.com`. Before encryption, the message would be:

```json
{
  "type": "m.room.message",
  "content": {
    "body": "who wants to go down the pub?",
    "msgtype": "m.text",
    "m.labels": {
      "3204de89c747346393ea5645608d79b8127f96c70943ae55730c3f13aa72f20a": "#fun"
    }
  }
}
```

`3204de89c747346393ea5645608d79b8127f96c70943ae55730c3f13aa72f20a` is the SHA256
hash of the string `#fun!someroom:example.com`.

Once encrypted, the event would become:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "AwgAEpABm6.......",
    "device_id": "SOLZHNGTZT",
    "sender_key": "FRlkQA1enABuOH4xipzJJ/oD8fxiQHj6jrAyyrvzSTY",
    "session_id": "JPWczbhnAivenK3qRwqLLBQu4W13fz1lqQpXDlpZzCg",
    "m.labels_hashes": [
      "3204de89c747346393ea5645608d79b8127f96c70943ae55730c3f13aa72f20a"
    ]
  }
}
```

### Unencrypted rooms

In unencrypted rooms, the string to use as a key does not matter (as this format
is only kept for consistency with events sent in encrypted rooms) and clients
are free to use any non-empty string they wish (as long as it's unique per label
in the event).

When filtering events based on their label(s), clients are expected to use the
actual label text instead of the string key.

#### Example

```json
{
  "type": "m.room.message",
  "content": {
    "body": "who wants to go down the pub?",
    "msgtype": "m.text",
    "m.labels": {
      "somekey": "#fun"
    }
  }
}
```

## Problems

Do we care about internationalising hashtags?

Too many threading APIs?

Using hashes means that servers could be inclined to compute rainbow tables to
read labels on encrypted messages. However, since we're using the room ID as
some kind of hash, it makes it much more expensive to do because it would mean
maintaining one rainbow table for each encrypted room it's in, which would
probably make it not worth the trouble.

## Unstable prefix

Unstable implementations should hook up `org.matrix.labels` rather than
`m.labels`. When defining filters, they should also use `org.matrix.labels` and
`org.matrix.not_labels` in the `EventFilter` object.

Additionally, servers implementing this feature should advertise that they do so
by exposing a `label_based_filtering` flag in the `unstable_features` part of
the `/versions` response.
