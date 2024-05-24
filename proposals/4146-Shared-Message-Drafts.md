# MSC4146: Shared Message Drafts

In Matrix, most clients support saving drafts, yet there is no way to share this
data. This proposal outlines how such data could be shared.

## Proposal

There is often the need to draft out a message before sending it out, like
wanting someone else to proofread it first, writing a message about an ongoing
event, or a plethora of other scenarios where a message should just remain
unsent until the time comes. However the experience is frustrating because you
are limited only to one device, or even just one client on the same device.

If you're ever in a situation where you want to send the message, edit it, or
maybe even delete the draft, you cannot do so without first going back to the
device you initially wrote it on. This means you cannot carry over a draft from
your Phone to your Computer to have a more comfortable typing experience, or to
see the text on a bigger screen, and is generally just an inconvenience.

My first idea would be to repurpose rooms, similar to how it's proposed for
Profiles-As-Rooms or how Spaces are implemented. A new room type, `m.drafts` or
`m.draft` would be added, allowing the client to differentiate this room from
DMs, Spaces or Groups. A creation event could look something like this:

```json
{
  "content": {
    "creator": "@example:example.com",
    "room_version": "9",
    "type": "m.drafts"
  },
  ...
}
```

In said room, the client would then send normal `m.text` events, optionally with
a formatted body, and would edit the message every ´n´ seconds or once the user
stops typing. (This is more of a UI/UX implementation
detail though)

Another thing that would be introduced would be a field that defines what room
this is supposed to be for / In which room this draft was written

This could be done something like this, with a field to indicate what room it
relates to:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "**test!!!**",
    "format": "org.matrix.custom.html",
    "formatted_body": "<strong>test!!!</strong>",
    "m.draft_in": "!ROOMID:example.com"
  }
}
```

This format also works with media:

```json
{
  "content": {
    "body": "image.png",
    "info": {
      "h": ...,
      "mimetype": "image/png",
      "size": ...,
      "w": ...,
      "xyz.amorgan.blurhash": "..."
    },
    "msgtype": "m.image",
    "url": "mxc://example.net/...",
    "m.draft_in": "!ROOMID:example.com"
  }
}
```

In the case of Media, a client would take the `body`, `info` and `url` fields
into account when importing it into the editor. In the case of text, a client
would import the `body`, `formatted_body` and `format` fields

The format of the event should be somewhat compatible with clients that do not
implement the MSC, so that in those clients the draft gets displayed as a
message that the user could still manually copy or edit to also edit the draft.

Additionally, a client can include the `m.draft_full_event` field in the draft,
which allows the client to upload a full event including media, intentional
mentions and other metadata that are not contained in the `body` or
`formatted_body` of an event. Such an event would look something like this:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "**test!!!**",
    "format": "org.matrix.custom.html",
    "formatted_body": "<strong>test!!!</strong>",
    "m.draft_in": "!ROOMID:example.com",
    "m.draft_full_event": {
      ...
      "m.mentions": {
        "user_ids": [
          "@1:example.com",
          "@2:example.com"
        ]
      }
    }
  }
}

```

This would be useful in events where a client may want to have more information
in the draft than what fits into the existing body fields, like drafting a poll,
drafting with intentional mentions (like in the example above) or drafting a
custom event. This field is **not** required.

When a user is in multiple `m.drafts` rooms, the client should take whatever
draft is chronologically the newest for a given room from any `m.drafts` room,
unless there is two or more drafts with the same timestamp. When there is two or
more drafts with the same timestamp, the client should give the user the option
of which draft to keep, redacting the other drafts in whatever room the drafts
are in.

The Client should also only import it's own events when checking `m.drafts`
rooms, unless explicitly requested otherwise by the user.

## Potential issues

There are some issues with this approach, notably I thought of:

- If the room is encrypted to allow privacy for these drafts, then the drafts
would be unavailable to a client that has just authenticated but has not been
verified yet, and as such cannot get the keys for the messages in the room and
decrypt any of the drafts.
- Clients that do not support this MSC might display
the drafts room normally, allowing the user to send arbitrary messages into the
room, which might become messy.
- If a client removes the `m.draft_in` as part
of an edit the draft would no longer be associated with a room, causing
confusion on the users' end as to where their draft went.

## Alternatives

An alternative way to implement this would be to instead add this data to
account data, adding a field similar to what Element does with
`io.element.recent_emoji`

The field could be named something like `m.room_drafts` or `m.drafts` (just like
the room type from idea #1) and could contain something like this:

```json
{
  "type": "m.room_drafts",
  "content": {
    "!ROOMID:example.com": {
      "body": "**test!**",
      "format": "org.matrix.custom.html",
      "formatted_body": "<strong>test!!!</strong>"
    }
  }
}
```

This would cut the requirement for re-purposing a room (from what I understand).

However, it would also mean that you cannot encrypt the drafts, and as such
these drafts would be leaked metadata that the server can read. This should be
avoided as drafts can belong to an encrypted room, which you do not want leaked.

## Security considerations

By implementing this by repurposing an **encrypted** room you can avoid the
drafts - and as such messages that might go into an encrypted room - being
leaked to the homeserver. Encryption for a feature like this is a goal that
should not be neglected.

Clients should consider only uploading drafted media to the room if explicitly
requested by the user, as this could otherwise lead to media that never gets
deleted from the server; This could pose a threat to privacy if the `m.drafts`
room is unencrypted.

## Unstable prefix

Proposed unstable prefixes for `m.drafts` and `m.draft_in` would be:

| prefix                        | description                       |
|-------------------------------|-----------------------------------|
| `org.matrix.msc4146.drafts`   | For the room type                 |
| `org.matrix.msc4146.draft_in` | For the room ID information on the events |
| `org.matrix.msc4146.draft_full_event` | For storing a full event alongside the normal message body or media |

## Dependencies

Not Applicable
