Proposal
========

I propose for message edits to follow a similar format to replies, using `m.relates_to`. The content of the edited message should be inside
`m.supersedes.new_content` which can be accessed if the client is edit-aware. If the client is not aware, it can use `content.body` and
`content.formatted_body` to render an approximation of the edit. The fallback should be in the format given below.

Clients should always favor fetching the source from `m.supersedes.event_id` where possible, rather than using the fallback as the fallback can
be faked. Furthermore, clients should refuse to display with a appropriate message when the sender of the source event and the edit event differ.

It should be noted that this allows any event to be replaced by an entirely different set of content. The client should make a best effort attempt
to describe the relationship between the two events for both the fallback and representation.

If the edit event's content is invalid, it is acceptable to display/keep the old event in place with a warning.

Example
-------

Original message:
```javascript
{
  "content": {
    "body": "This is an example message I want to edit.",
    "msgtype": "m.text"
  },
  "event_id": "$1539340060524DGxMc:half-shot.uk",
  "sender": "@Half-Shot:half-shot.uk",
  "type": "m.room.message",
  "room_id": "!IPcexxPYNJKmTvRfoV:half-shot.uk"
}
```

New edited message:
```javascript
{
  "content": {
    "body": "Edited: ~~This is an example message I want to edit~~ This is the edited message",
    "format": "org.matrix.custom.html",
    "formatted_body": "Edited: <del>This is an example message I want to edit</del> This is the edited message",
    "m.relates_to": {
      "m.supersedes": {
        "event_id": "$1539340060524DGxMc:half-shot.uk",
        "new_content": {
            "body": "This is the edited message.",
            "msgtype": "m.text"
        }
      }
    },
    "msgtype": "m.text"
  },
  "event_id": "$1539340066525PiiWI:half-shot.uk",
  "sender": "@Half-Shot:half-shot.uk",
  "type": "m.room.message",
  "room_id": "!IPcexxPYNJKmTvRfoV:half-shot.uk"
}
```

Problems
--------

One of the glaring problems with this approach is it doesn't modify the original event. In this proposal I'd recommend that users redact events rather
than try to edit sensitive information out of them.

Clients will also render the original event without the edit if the client isn't aware of the edit, since event aggregations aren't a thing yet. This is
an acceptable risk for this proposal, and aggregations are considered an extension to message edits for Matrix.

It should be noted that many bridges and bots already show edits in the form of a fallback already, so this event only strives to add some specced metadata
to allow clients to render them clearly. In the future, this proposal could be extended to use aggregations to apply to older events.
