Proposal
========

This proposal extends the m.room.message schema to add support for edits. It does NOT
provide a way to aggregate those edits. The edit event is comprised of some metadata
to describe the edited event and some fallback text.

Message edits should follow a similar format to replies, using  `m.relates_to`.
The content of the edited message should be inside `m.replaces.new_content` which can
be accessed if the client is edit-aware. If the client is not aware, it can use `content.body`
and `content.formatted_body` to render an approximation of the edit. The fallback should be
in the format given below.

Clients should always favour fetching the source from `m.replaces.event_id` where possible,
rather than using the fallback as the fallback can be faked. Furthermore, clients should refuse
to display with an appropriate message when the sender of the source event and the edit event differ.

Clients should provide an option to see edit history. The history does not need
to be complete (e.g. if one event in the edit chain cannot be fetched). The representation of this
history is up to the client.

It should be noted that this allows any event to be replaced by an entirely different set of content.
The client should make a best effort attempt to describe the relationship between the two events for
both the fallback and representation.

``reason`` describes why the event was replaced, which is currently a placeholder
and should always be "m.edited" to describe an event that was edited by the user.

If the edit event's content is invalid, it is acceptable to display/keep the old event in place with a warning.

User should be warned that editing a sensitive event will NOT erase it's contents, and they should use a redact instead.
NOTE: Redacts are not assurances of removal either, but they carry a clear intent to remove the message.

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
    "m.new_content": {
        "body": "This is the edited message.",
        "msgtype": "m.text"
    }
    "m.relates_to": {
      "m.replaces": {
        "event_id": "$1539340060524DGxMc:half-shot.uk",
        "reason": "m.edited"
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

It should be noted that many bridges and bots already show edits in the form of a
fallback already, so this event only strives to add some specced metadata to allow
clients to render them clearly.In the future, this proposal could be extended to
use aggregations to show a list of edits made to a message.
